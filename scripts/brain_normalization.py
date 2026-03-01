import sqlite3
import os
import re

DB_PATH = r"i:\01-Master_Code\Apps\REM\TheKid\brain\synapses.rem"

CORE_PILLARS = {
    "Math": ["math", "arithmetic", "algebra", "geometry", "calculus", "calculating", "number"],
    "Language": ["language", "grammar", "etymology", "linguistics", "vocab", "speech", "words", "sentence"],
    "Logic": ["logic", "reasoning", "deduction", "syllogism", "cause", "condition"],
    "Social": ["social", "conversation", "greeting", "interaction", "empathy", "identity", "relationship"],
    "Identity": ["identity", "name", "who am i", "ali"],
}

def normalize_context(ctx):
    ctx_lower = ctx.lower()
    for pillar, keywords in CORE_PILLARS.items():
        if any(kw in ctx_lower for kw in keywords):
            return pillar
    return "General"

def run_normalization():
    if not os.path.exists(DB_PATH):
        print("DB not found at", DB_PATH)
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Purge Garbage Strings (the "ssss2+2" and junk)
    print("Purging garbage strings...")
    cursor.execute("DELETE FROM quadruplets WHERE subject LIKE 'ssss%' OR subject LIKE '% % % % %' OR length(subject) > 200;")
    print(f"Purged {cursor.rowcount} garbage rows.")

    # 2. Context Normalization
    print("Normalizing 200+ contexts into Core Pillars...")
    cursor.execute("SELECT DISTINCT context FROM quadruplets;")
    all_contexts = [row[0] for row in cursor.fetchall()]
    
    changed_count = 0
    for old_ctx in all_contexts:
        new_ctx = normalize_context(old_ctx)
        if new_ctx != old_ctx:
            cursor.execute("UPDATE quadruplets SET context = ? WHERE context = ?", (new_ctx, old_ctx))
            changed_count += cursor.rowcount
            
    print(f"Successfully normalized contexts across {changed_count} rows.")

    # 3. Deduplicate
    # SQLite doesn't have an easy way to dedupe on UNIQUE constraint after updating and ignoring errors.
    # We will just merge occurrences for duplicate (S,R,O,C)
    print("Merging duplicate facts created by normalization...")
    cursor.execute("""
        CREATE TABLE quadruplets_new AS 
        SELECT subject, relation, object, context, MAX(strength) as strength, MAX(truth_value) as truth_value, 
               SUM(occurrences) as occurrences, MAX(last_seen_at) as last_seen_at
        FROM quadruplets
        GROUP BY subject, relation, object, context;
    """)
    cursor.execute("DROP TABLE quadruplets;")
    cursor.execute("ALTER TABLE quadruplets_new RENAME TO quadruplets;")
    # Re-create the index/unique constraint
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_quad_unique ON quadruplets(subject, relation, object, context);")
    
    conn.commit()
    conn.close()
    print("Brain Normalization Phase 20 Complete.")

if __name__ == "__main__":
    run_normalization()
