import sqlite3
import os

DB_PATH = r"i:\01-Master_Code\Apps\REM\TheKid\brain\synapses.rem"

def audit():
    if not os.path.exists(DB_PATH):
        print("DB not found at", DB_PATH)
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- CONTEXT DISTRIBUTION ---")
    cursor.execute("SELECT context, count(*) FROM quadruplets GROUP BY context ORDER BY count(*) DESC;")
    for row in cursor.fetchall():
        print(f"{row[0]:<20} | {row[1]}")
        
    print("\n--- SAMPLE MATH FACTS ---")
    cursor.execute("SELECT subject, relation, object FROM quadruplets WHERE context='Math' ORDER BY rowid DESC LIMIT 10;")
    for row in cursor.fetchall():
        print(f"{row[0]} | {row[1]} | {row[2]}")

    print("\n--- RECENT USER PREFERENCES ---")
    cursor.execute("SELECT subject, relation, object FROM quadruplets WHERE context='UserPreference' ORDER BY rowid DESC LIMIT 5;")
    for row in cursor.fetchall():
        print(f"{row[0]} | {row[1]} | {row[2]}")

    print("\n--- POTENTIAL CONTRADICTIONS ---")
    cursor.execute("""
        SELECT a.subject, a.relation, a.object, b.object 
        FROM quadruplets a 
        JOIN quadruplets b ON a.subject = b.subject AND a.relation = b.relation AND a.object != b.object
        WHERE a.rowid < b.rowid
        LIMIT 10;
    """)
    for row in cursor.fetchall():
        print(f"CONFLICT: {row[0]} {row[1]} -> {row[2]} vs {row[3]}")

    conn.close()

if __name__ == "__main__":
    audit()
