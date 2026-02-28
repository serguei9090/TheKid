import json
import os

from core.engine import KidEngine
from core.teacher import is_teacher_present, vocalize

MISSIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'missions'))
LIBRARY_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), 'library'))

def get_new_missions() -> list:
    """Returns a list of uncompleted missions from /missions"""
    missions = []
    if not os.path.exists(MISSIONS_DIR):
        return missions
    
    for filename in os.listdir(MISSIONS_DIR):
        if filename.endswith(".json"):
            path = os.path.join(MISSIONS_DIR, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not data.get("completed", False):
                        missions.append((path, data))
            except Exception as e:
                print(f"[ERROR] Could not parse mission {filename}: {e}")
    return missions

def execute_learning_phase(engine: KidEngine):
    missions = get_new_missions()
    for path, data in missions:
        action = data.get("action")
        if action == "ingest_file":
            file_name = data.get("target_file")
            file_path = os.path.join(LIBRARY_DIR, file_name)
            
            print(f"[TRACE: LEARNING PHASE] Executing mission: {data.get('goal')}")
            engine.ingest_file(file_path)
            
            # Mark complete
            data["completed"] = True
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            print(f"[TRACE: MISSION COMPLETE] {path}")

def execute_dream_phase(engine: KidEngine):
    """
    Dream Phase: The core memory optimization logic using the New Math.
    Runs Cosine Fusion, Entropy Pruning, PSL, and updates Link Strengths.
    """
    print("[TRACE: DREAM PHASE] The Kid is sleeping... optimizing neural links.")
    
    # 1. Update Link Strengths (D. Relational Link Strength)
    engine.update_link_strengths()
    
    # 2. Entropy Pruning (B. Entropy Pruning)
    engine.prune_weak_links()
    
    # 3. Probabilistic Soft Logic (C. Probabilistic Soft Logic - PSL)
    engine.run_probabilistic_soft_logic()
    
    # 4. Cosine Fusion (A. Cosine Fusion)
    # We provide a simple callback to automatically verify the merger for now
    def auto_verify_merger(a, b):
        return True
        
    engine.fuse_synonyms(teacher_verify_cb=auto_verify_merger)

def execute_worker_phase(engine: KidEngine):
    """Relational lookup and Template response"""
    if not is_teacher_present():
        print("[ERROR] Teacher not present. The Kid cannot vocalize thoughts.")
        return
        
    print("\n--- Worker Phase Active. Type 'exit' to quit. ---")
    while True:
        try:
            user_input = input("USER: ")
            if user_input.lower() in ["exit", "quit", "q"]:
                break
                
            print("[TRACE: SEARCHING] Querying .rem database for concepts...")
            
            # Simple keyword extraction (words > 3 chars)
            keywords = [
                kw for kw in user_input.replace("?", "").replace(".", "").split() if len(kw) > 2
            ]
            
            facts = engine.query_brain(keywords)
            if not facts:
                print("THE KID: I don't know that yet, let me ask my Teacher.")
                
                # Proactive Learning Loop
                prompt = f"Please provide a concise answer to the user's question: '{user_input}'. Then format the core facts into $Subject | Relation | Object$ triplets."
                
                try:
                    from core.teacher import MODEL_NAME, client
                    response = client.generate(
                        model=MODEL_NAME,
                        prompt=prompt,
                        stream=False
                    )
                    teacher_answer = response.get("response", "")
                    
                    # Store any new triplets returned by the teacher
                    from core.teacher import translate_to_triplets
                    new_triplets = translate_to_triplets(teacher_answer)
                    if new_triplets:
                        print(f"[TRACE: LEARNING ON THE FLY] Extracted {len(new_triplets)} new facts.")
                        for tri in new_triplets:
                            engine.store_triplet(tri)
                            
                    print(f"TEACHER: {teacher_answer.split('$')[0].strip()}")
                        
                except Exception as e:
                    print(f"[ERROR] Could not ask Teacher: {e}")
            else:
                print(f"[TRACE: FOUND EXACT FACTS] {facts}")
                print(f"[TRACE: ASKING TEACHER] Sending {len(facts)} facts to vocal cords.")
                response = vocalize(facts, user_input)
                print(f"THE KID: {response}")
            print("-" * 50)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[ERROR] Worker phase encountered an error: {e}")

def main_loop():
    print("[TRACE: SYSTEM START] The Kid is awake.")
    engine = KidEngine()
    
    # We do a basic cycle
    if get_new_missions():
        print("[TRACE: NEW MISSIONS DETECTED]")
        execute_learning_phase(engine)
        
    execute_dream_phase(engine)
    
    execute_worker_phase(engine)

if __name__ == "__main__":
    main_loop()
