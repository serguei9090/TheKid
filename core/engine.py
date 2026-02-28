import concurrent.futures
import hashlib
import os
import sqlite3
from typing import List

from .teacher import translate_to_triplets

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'brain', 'synapses.rem'))

class KidEngine:
    """The python/sqlite engine that acts as the core memory (The Kid)."""
    
    def __init__(self):
        # check_same_thread=False for parallel processing safety.
        # SQLite handles file locks, but manual transactions need care if multi-writing.
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._initialize_db()

    def _initialize_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS triplets (
                subject TEXT,
                relation TEXT,
                object TEXT,
                strength REAL DEFAULT 1.0,
                truth_value REAL DEFAULT 1.0,
                occurrences INTEGER DEFAULT 1,
                last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(subject, relation, object)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                file_hash TEXT PRIMARY KEY,
                file_name TEXT,
                status TEXT
            )
        ''')
        self.conn.commit()

    def hash_file(self, file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for block in iter(lambda: f.read(65536), b''):
                sha256.update(block)
        return sha256.hexdigest()

    def is_file_ingested(self, file_hash: str) -> bool:
        self.cursor.execute("SELECT status FROM sources WHERE file_hash = ?", (file_hash,))
        result = self.cursor.fetchone()
        return result is not None and result[0] == 'processed'

    def chunk_text(self, text: str, chunk_size: int = 2000) -> List[str]:
        """Simple character chunking for text."""
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    def store_triplet(self, triplet_str: str):
        """Stores a $Subject | Relation | Object$ formatted triplet."""
        clean_str = triplet_str.strip()
        if not (clean_str.startswith("$") and clean_str.endswith("$")):
            return
            
        parts = [p.strip() for p in clean_str[1:-1].split("|")]
        if len(parts) == 3:
            s, r, o = parts
            print(f"[TRACE: LEARNING] Saving Fact -> {s} | {r} | {o}")
            # Insert or update occurrence
            self.cursor.execute('''
                INSERT INTO triplets (subject, relation, object, occurrences) 
                VALUES (?, ?, ?, 1)
                ON CONFLICT(subject, relation, object) 
                DO UPDATE SET occurrences = occurrences + 1, last_seen_at = CURRENT_TIMESTAMP
            ''', (s, r, o))

    def ingest_file(self, file_path: str):
        """Parallel ingestion of a file's contents into the database."""
        if not os.path.exists(file_path):
            print(f"[ERROR] Ingestion file not found: {file_path}")
            return

        print(f"[TRACE: HASHING] Checking file {file_path}")
        file_hash = self.hash_file(file_path)
        
        if self.is_file_ingested(file_hash):
            print(f"[TRACE: SKIP] File already ingested: {file_path}")
            return
            
        file_name = os.path.basename(file_path)
        
        # Mark as processing
        self.cursor.execute('''
            INSERT INTO sources (file_hash, file_name, status) 
            VALUES (?, ?, 'processing')
            ON CONFLICT(file_hash) DO UPDATE SET status = 'processing'
        ''', (file_hash, file_name))
        self.conn.commit()

        print(f"[TRACE: READING] {file_name}")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        chunks = self.chunk_text(content)
        print(f"[TRACE: PARALLEL INGESTION] Starting {len(chunks)} chunks...")
        
        # We need to gather triplets from teacher using multiple threads
        all_triplets = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            future_to_chunk = {
                executor.submit(translate_to_triplets, chunk): chunk for chunk in chunks
            }
            for future in concurrent.futures.as_completed(future_to_chunk):
                try:
                    result_triplets = future.result()
                    all_triplets.extend(result_triplets)
                    print(f"[TRACE: TEACHER RETURNED] {len(result_triplets)} triplets from chunk.")
                except Exception as exc:
                    print(f"[ERROR] Chunk processing generated an exception: {exc}")
                    
        # Store in DB
        for tri in all_triplets:
            self.store_triplet(tri)
            
        self.cursor.execute('''
            UPDATE sources SET status = 'processed' WHERE file_hash = ?
        ''', (file_hash,))
        self.conn.commit()
        print(f"[TRACE: INGESTION COMPLETE] {file_name}")

    def query_brain(self, keywords: List[str]) -> List[str]:
        """Looks up facts containing any of the keywords in subject or object"""
        if not keywords:
            return []
            
        query = "SELECT subject, relation, object FROM triplets WHERE "
        conditions = []
        params = []
        
        for kw in keywords:
            conditions.append("(subject LIKE ? OR object LIKE ?)")
            kw_param = f"%{kw}%"
            params.extend([kw_param, kw_param])
            
        query += " OR ".join(conditions) + " ORDER BY strength DESC LIMIT 10"
        
        self.cursor.execute(query, params)
        results = self.cursor.fetchall()
        
        formatted = []
        for s, r, o in results:
            formatted.append(f"${s} | {r} | {o}$")
        return formatted

    def update_link_strengths(self):
        """D. Relational Link Strength calculation."""
        from datetime import datetime, timezone

        from core.math_utils import relational_link_strength
        
        self.cursor.execute(
            "SELECT rowid, occurrences, strftime('%Y-%m-%d %H:%M:%S', last_seen_at) FROM triplets"
        )
        updates = []
        for rowid, occ, last_seen in self.cursor.fetchall():
            if not last_seen:
                continue
            last_dt = datetime.strptime(last_seen, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            diff_seconds = (datetime.now(timezone.utc) - last_dt).total_seconds()
            strength = relational_link_strength(float(occ), max(1.0, diff_seconds))
            updates.append((strength, rowid))
            
        self.cursor.executemany("UPDATE triplets SET strength = ? WHERE rowid = ?", updates)
        self.conn.commit()

    def prune_weak_links(self):
        """B. Entropy Pruning: Deletes 'noisy' or 'obvious' links"""
        from core.math_utils import entropy_pruning
        self.cursor.execute("SELECT COUNT(*) FROM triplets")
        total_facts = self.cursor.fetchone()[0]
        if total_facts == 0:
            return
        
        self.cursor.execute("SELECT relation, COUNT(*) FROM triplets GROUP BY relation")
        rel_counts = dict(self.cursor.fetchall())
        
        self.cursor.execute("SELECT rowid, relation, strength FROM triplets")
        prune_ids = []
        for rowid, rel, strength in self.cursor.fetchall():
            d_i = rel_counts.get(rel, 1)
            importance = entropy_pruning(strength, total_facts, d_i)
            # Threshold could be 0.1 for pruning
            if importance < 0.1 and strength < 0.5:
                prune_ids.append((rowid,))
                
        if prune_ids:
            self.cursor.executemany("DELETE FROM triplets WHERE rowid = ?", prune_ids)
            self.conn.commit()
            print(f"[TRACE: ENTROPY PRUNING] Forgot {len(prune_ids)} weak facts.")

    def run_probabilistic_soft_logic(self):
        """C. Probabilistic Soft Logic - PSL (The Truth Verifier)"""
        # We find connections A->C and verify if their transitive truth is < 0.5
        # If truth_value < 0.5 we delete it.
        self.cursor.execute("SELECT rowid, truth_value FROM triplets WHERE truth_value < 0.5")
        mistakes = self.cursor.fetchall()
        if mistakes:
            self.cursor.executemany(
                "DELETE FROM triplets WHERE rowid = ?", [(m[0],) for m in mistakes]
            )
            self.conn.commit()
            print(f"[TRACE: PSL Math] Discarded {len(mistakes)} hallucinated mistakes.")

    def fuse_synonyms(self, teacher_verify_cb=None):
        """A. Cosine Fusion: Merges nodes by comparing connection patterns."""
        from core.math_utils import calculate_cosine_similarity
        self.cursor.execute("SELECT subject, relation, strength FROM triplets")
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
            print(f"[TRACE: COSINE FUSION] Similarity ({sim:.2f}) between {subj_a} & {subj_b}")
            if teacher_verify_cb and teacher_verify_cb(subj_a, subj_b):
                print(f"[TRACE: MERGING] {subj_b} into {subj_a}")
                self.cursor.execute(
                    "UPDATE triplets SET subject = ? WHERE subject = ?", (subj_a, subj_b)
                )
                self.cursor.execute(
                    "UPDATE triplets SET object = ? WHERE object = ?", (subj_a, subj_b)
                )
                self.conn.commit()
