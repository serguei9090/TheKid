import concurrent.futures
import hashlib
import os
import sqlite3
from typing import List

from .logger import error_log, trace_log
from .teacher import translate_to_quadruplets

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "brain", "synapses.rem"))


class KidEngine:
    """The python/sqlite engine that acts as the core memory (The Kid)."""

    def __init__(self, silent_trace: bool = False):
        self.silent_trace = silent_trace
        # check_same_thread=False for parallel processing safety.
        # SQLite handles file locks, but manual transactions need care if multi-writing.
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=15.0)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA journal_mode=WAL;")
        self._initialize_db()

    def _trace(self, module: str, message: str, color: str = "GRAY"):
        trace_log(module, message, color=color, show_in_console=not self.silent_trace)

    def _initialize_db(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS quadruplets (
                subject TEXT,
                relation TEXT,
                object TEXT,
                context TEXT DEFAULT 'General',
                strength REAL DEFAULT 1.0,
                truth_value REAL DEFAULT 1.0,
                occurrences INTEGER DEFAULT 1,
                last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(subject, relation, object, context)
            )
        """)
        # Migrate old triplets to quadruplets safely
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='triplets'")
        if self.cursor.fetchone():
            self.cursor.execute("""
                INSERT OR IGNORE INTO quadruplets (
                    subject, relation, object, context, strength, truth_value, occurrences, 
                    last_seen_at
                )
                SELECT subject, relation, object, 'General', strength, truth_value, occurrences, 
                       last_seen_at FROM triplets
            """)
            self.cursor.execute("DROP TABLE triplets")

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                file_hash TEXT PRIMARY KEY,
                file_name TEXT,
                status TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                user_name TEXT PRIMARY KEY,
                last_fact_id INTEGER,
                last_interaction_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def hash_file(self, file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(65536), b""):
                sha256.update(block)
        return sha256.hexdigest()

    def is_file_ingested(self, file_hash: str) -> bool:
        self.cursor.execute("SELECT status FROM sources WHERE file_hash = ?", (file_hash,))
        result = self.cursor.fetchone()
        return result is not None and result[0] == "processed"

    def chunk_text(self, text: str, chunk_size: int = 2000) -> List[str]:
        """Simple character chunking for text."""
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    def store_quadruplet(self, quad_str: str, default_context: str = "General"):
        """Stores a $Subject | Relation | Object | Context$ formatted quadruplet."""
        clean_str = quad_str.strip()
        if not (clean_str.startswith("$") and clean_str.endswith("$")):
            return

        parts = [p.strip() for p in clean_str[1:-1].split("|")]

        # Handle fallback for older triplet formats
        if len(parts) == 3:
            s, r, o = parts
            c = default_context
        elif len(parts) >= 4:
            s, r, o, c = parts[:4]
        else:
            return

        self._trace("LEARNING", f"Saving Fact -> {s} | {r} | {o} | {c}")
        # Insert or update occurrence
        self.cursor.execute(
            """
            INSERT INTO quadruplets (subject, relation, object, context, occurrences) 
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(subject, relation, object, context) 
            DO UPDATE SET occurrences = occurrences + 1, last_seen_at = CURRENT_TIMESTAMP
        """,
            (s, r, o, c),
        )

    def ingest_file(self, file_path: str):
        """Parallel ingestion of a file's contents into the database."""
        if not os.path.exists(file_path):
            error_log(f"Ingestion file not found: {file_path}")
            return

        self._trace("HASHING", f"Checking file {file_path}")
        file_hash = self.hash_file(file_path)

        if self.is_file_ingested(file_hash):
            self._trace("SKIP", f"File already ingested: {file_path}")
            return

        file_name = os.path.basename(file_path)

        # Mark as processing
        self.cursor.execute(
            """
            INSERT INTO sources (file_hash, file_name, status) 
            VALUES (?, ?, 'processing')
            ON CONFLICT(file_hash) DO UPDATE SET status = 'processing'
        """,
            (file_hash, file_name),
        )
        self.conn.commit()

        self._trace("READING", file_name)
        content = ""
        if file_path.lower().endswith(".pdf"):
            try:
                import pypdf

                with open(file_path, "rb") as f:
                    reader = pypdf.PdfReader(f)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            content += page_text + "\n"
            except Exception as e:
                error_log(f"Failed to read PDF {file_name}: {e}")
                return
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

        chunks = self.chunk_text(content)
        self._trace("PARALLEL INGESTION", f"Starting {len(chunks)} chunks...")

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                future_to_chunk = {
                    executor.submit(translate_to_quadruplets, chunk): chunk for chunk in chunks
                }

                total_chunks = len(chunks)
                completed = 0

                for future in concurrent.futures.as_completed(future_to_chunk):
                    try:
                        result_quads = future.result()
                        # LIVE INGESTION: Stream results straight to the database
                        for quad in result_quads:
                            self.store_quadruplet(quad)
                        self.conn.commit()

                        completed += 1
                        if completed % 10 == 0 or completed == total_chunks:
                            # Bypass silent_trace to show milestone progress without locking the input
                            trace_log(
                                "PROGRESS",
                                f"Ingested {completed}/{total_chunks} chunks of {file_name}",
                                color="CYAN",
                                show_in_console=True,
                            )

                        self._trace(
                            "TEACHER RETURNED",
                            f"{len(result_quads)} triplets/quads from chunk.",
                        )
                    except KeyboardInterrupt:
                        self._trace(
                            "SHUTDOWN",
                            "Interrupted during Teacher Extraction. Cancelling...",
                            color="RED",
                        )
                        for f in future_to_chunk:
                            f.cancel()
                        return
                    except Exception as exc:
                        error_log(f"Chunk processing generated an exception: {exc}")
        except KeyboardInterrupt:
            self._trace("SHUTDOWN", "File Ingestion manually canceled.", color="RED")
            return

        self.cursor.execute(
            """
            UPDATE sources SET status = 'processed' WHERE file_hash = ?
        """,
            (file_hash,),
        )
        self.conn.commit()
        self._trace("INGESTION COMPLETE", file_name, color="GREEN")

    def query_brain_cra(self, keywords: List[str], current_situation: str = "General") -> List[str]:
        """
        Phase 2: Contextual Resonant Activation lookup. Looks for matching keywords and
        modifies base strength via CRA math.
        """
        from core.math_utils import contextual_resonant_activation, spreading_activation_energy

        if not keywords:
            return []

        query = "SELECT subject, relation, object, context, strength FROM quadruplets WHERE "
        conditions = []
        params = []

        for kw in keywords:
            conditions.append("(subject LIKE ? OR object LIKE ?)")
            kw_param = f"%{kw}%"
            params.extend([kw_param, kw_param])

        query += " OR ".join(conditions)
        self.cursor.execute(query, params)
        results = self.cursor.fetchall()

        # Calculate Cra Math for each result
        scored_results = []
        energy_source = 1.0  # Base user energy

        for s, r, o, c, w in results:
            activation = contextual_resonant_activation(w, r, current_situation)
            
            # Phase 17: Context Match Multiplier
            # If the fact's metadata context matches the current situation, boost resonance
            if c.lower() == current_situation.lower():
                activation *= 1.5
            
            energy_target = spreading_activation_energy(energy_source, activation, decay=1.5)
            scored_results.append((energy_target, activation, s, r, o, c))

        # Sort by highest resonant energy
        scored_results.sort(key=lambda x: x[0], reverse=True)
        top_facts = scored_results[:2]  # NSCA: Singular Convergence (1 or 2 facts max)

        formatted = []
        for e, a, s, r, o, c in top_facts:
            # NSCA: Minimum energy threshold to avoid hallucinated garbage links
            if e > 0.3:
                # Log CRA decision trace with Energy (E) and Activation (A)
                self._trace(
                    "CRA Math",
                    f"Path: [{s} -> {r} -> {o}] | Activation(A): {a:.2f} | Energy(E): {e:.2f}",
                    color="CYAN",
                )
                formatted.append(f"${s} | {r} | {o} | {c}$")

                # Track the last spoken fact ID for this user (default 'User')
                self.cursor.execute(
                    "INSERT OR REPLACE INTO sessions (user_name, last_fact_id) VALUES ('User', (SELECT rowid FROM quadruplets WHERE subject=? AND relation=? AND object=? AND context=?))",
                    (s, r, o, c),
                )
        self.conn.commit()

        return formatted

    def backpropagate_feedback(self, correct: bool):
        """
        Adjusts fact strength based on user feedback.
        If correct=False, we lower the strength and truth_value.
        """
        self.cursor.execute("SELECT last_fact_id FROM sessions WHERE user_name = 'User'")
        row = self.cursor.fetchone()
        if not row or not row[0]:
            return

        fact_id = row[0]
        if correct:
            self.cursor.execute(
                "UPDATE quadruplets SET strength = MIN(2.0, strength + 0.2), truth_value = MIN(1.0, truth_value + 0.1) WHERE rowid = ?",
                (fact_id,),
            )
        else:
            self.cursor.execute(
                "UPDATE quadruplets SET strength = strength * 0.5, truth_value = truth_value * 0.5 WHERE rowid = ?",
                (fact_id,),
            )
            # Check for deletion
            self.cursor.execute(
                "DELETE FROM quadruplets WHERE rowid = ? AND strength < 0.1", (fact_id,)
            )
        self.conn.commit()

    def find_contradictions(self) -> List[tuple]:
        """
        Finds quadruplets with the same subject and relation but different objects.
        Returns a list of pairs (rowid1, rowid2).
        """
        self.cursor.execute("""
            SELECT a.rowid, b.rowid, a.subject, a.relation, a.object, b.object, a.context
            FROM quadruplets a
            JOIN quadruplets b ON a.subject = b.subject AND a.relation = b.relation 
            AND a.object != b.object AND a.context = b.context
            WHERE a.rowid < b.rowid
        """)
        return self.cursor.fetchall()

    def update_link_strengths(self):
        """D. Relational Link Strength calculation."""
        from datetime import datetime, timezone

        from core.math_utils import relational_link_strength

        self.cursor.execute(
            "SELECT rowid, occurrences, strftime('%Y-%m-%d %H:%M:%S', last_seen_at) "
            "FROM quadruplets"
        )
        updates = []
        for rowid, occ, last_seen in self.cursor.fetchall():
            if not last_seen:
                continue
            last_dt = datetime.strptime(last_seen, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            diff_seconds = (datetime.now(timezone.utc) - last_dt).total_seconds()
            strength = relational_link_strength(float(occ), max(1.0, diff_seconds))
            updates.append((strength, rowid))

        self.cursor.executemany("UPDATE quadruplets SET strength = ? WHERE rowid = ?", updates)
        self.conn.commit()

    def prune_weak_links(self):
        """B. Entropy Pruning: Deletes 'noisy' or 'obvious' links"""
        from core.math_utils import entropy_pruning

        self.cursor.execute("SELECT COUNT(*) FROM quadruplets")
        total_facts = self.cursor.fetchone()[0]
        if total_facts == 0:
            return

        self.cursor.execute("SELECT relation, COUNT(*) FROM quadruplets GROUP BY relation")
        rel_counts = dict(self.cursor.fetchall())

        self.cursor.execute("SELECT rowid, relation, strength FROM quadruplets")
        prune_ids = []
        for rowid, rel, strength in self.cursor.fetchall():
            d_i = rel_counts.get(rel, 1)
            importance = entropy_pruning(strength, total_facts, d_i)
            # Threshold could be 0.1 for pruning
            if importance < 0.1 and strength < 0.5:
                prune_ids.append((rowid,))

        if prune_ids:
            self.cursor.executemany("DELETE FROM quadruplets WHERE rowid = ?", prune_ids)
            self.conn.commit()
            self._trace("ENTROPY PRUNING", f"Forgot {len(prune_ids)} weak facts.", color="RED")

    def run_probabilistic_soft_logic(self):
        """C. Probabilistic Soft Logic - PSL (The Truth Verifier)"""
        # We find connections A->C and verify if their transitive truth is < 0.5
        # If truth_value < 0.5 we delete it.
        self.cursor.execute("SELECT rowid, truth_value FROM quadruplets WHERE truth_value < 0.5")
        mistakes = self.cursor.fetchall()
        if mistakes:
            self.cursor.executemany(
                "DELETE FROM quadruplets WHERE rowid = ?", [(m[0],) for m in mistakes]
            )
            self.conn.commit()
            self._trace(
                "PSL Math", f"Discarded {len(mistakes)} hallucinated mistakes.", color="RED"
            )

    def fuse_synonyms(self, teacher_verify_cb=None):
        """A. Cosine Fusion: Merges nodes by comparing connection patterns."""
        from core.math_utils import calculate_cosine_similarity

        self.cursor.execute("SELECT subject, relation, strength FROM quadruplets")
        nodes = {}
        for s, r, st in self.cursor.fetchall():
            if s not in nodes:
                nodes[s] = {}
            nodes[s][r] = st

        subjects = list(nodes.keys())
        fusions = []
        for i in range(len(subjects)):
            for j in range(i + 1, len(subjects)):
                subj_a = subjects[i]
                subj_b = subjects[j]
                sim = calculate_cosine_similarity(nodes[subj_a], nodes[subj_b])
                if sim > 0.85:
                    fusions.append((subj_a, subj_b, sim))

        for subj_a, subj_b, sim in fusions:
            self._trace("COSINE FUSION", f"Similarity ({sim:.2f}) between {subj_a} & {subj_b}")
            if teacher_verify_cb and teacher_verify_cb(subj_a, subj_b):
                self._trace("MERGING", f"{subj_b} into {subj_a}", color="YELLOW")
                self.cursor.execute(
                    "UPDATE OR IGNORE quadruplets SET subject = ? WHERE subject = ?",
                    (subj_a, subj_b),
                )
                self.cursor.execute(
                    "UPDATE OR IGNORE quadruplets SET object = ? WHERE object = ?", (subj_a, subj_b)
                )
                # Cleanup leftover un-merged duplicates (due to ignore)
                self.cursor.execute(
                    "DELETE FROM quadruplets WHERE subject = ? OR object = ?", (subj_b, subj_b)
                )
                self.conn.commit()
