import json
import os
import threading
import time

from core.engine import KidEngine
from core.logger import clear_trace_log, error_log, trace_log
from core.teacher import is_teacher_present, vocalize

MISSIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "missions"))
LIBRARY_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "library"))


def auto_generate_missions(engine: KidEngine):
    """Scans the library for new files and automatically creates learning missions for them."""
    if not os.path.exists(LIBRARY_DIR):
        return

    for filename in os.listdir(LIBRARY_DIR):
        file_path = os.path.join(LIBRARY_DIR, filename)
        if not os.path.isfile(file_path):
            continue

        # Check if already ingested using Engine's file hash tracker
        file_hash = engine.hash_file(file_path)
        if engine.is_file_ingested(file_hash):
            continue

        mission_filename = f"auto_learn_{filename}.json"
        mission_path = os.path.join(MISSIONS_DIR, mission_filename)

        if not os.path.exists(mission_path):
            trace_log(
                "AUTONOMY",
                f"Discovered new knowledge source: {filename}",
                color="YELLOW",
                show_in_console=not getattr(engine, "silent_trace", False),
            )
            mission_data = {
                "action": "ingest_file",
                "goal": f"Autonomous learning of {filename}",
                "target_file": filename,
                "completed": False,
            }
            try:
                os.makedirs(MISSIONS_DIR, exist_ok=True)
                with open(mission_path, "w", encoding="utf-8") as f:
                    json.dump(mission_data, f, indent=4)
            except Exception as e:
                error_log(f"Failed to auto-generate mission for {filename}: {e}")


def get_new_missions() -> list:
    """Returns a list of uncompleted missions from /missions"""
    missions = []
    if not os.path.exists(MISSIONS_DIR):
        return missions

    for filename in os.listdir(MISSIONS_DIR):
        if filename.endswith(".json"):
            path = os.path.join(MISSIONS_DIR, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not data.get("completed", False):
                        missions.append((path, data))
            except Exception as e:
                error_log(f"Could not parse mission {filename}: {e}")
    return missions


def execute_learning_phase(engine: KidEngine):
    missions = get_new_missions()
    for path, data in missions:
        action = data.get("action")
        if action == "ingest_file":
            file_name = data.get("target_file")
            file_path = os.path.join(LIBRARY_DIR, file_name)

            trace_log(
                "LEARNING PHASE",
                f"Executing mission: {data.get('goal')}",
                show_in_console=not getattr(engine, "silent_trace", False),
            )
            engine.ingest_file(file_path)

            # Mark complete
            data["completed"] = True
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            trace_log(
                "MISSION COMPLETE",
                path,
                color="GREEN",
                show_in_console=not getattr(engine, "silent_trace", False),
            )


def execute_dream_phase(engine: KidEngine):
    """
    Dream Phase: The core memory optimization logic using the New Math.
    Runs Cosine Fusion, Entropy Pruning, PSL, and updates Link Strengths.
    """
    trace_log(
        "DREAM PHASE",
        "The Kid is sleeping... optimizing neural links.",
        color="BLUE",
        show_in_console=not getattr(engine, "silent_trace", False),
    )

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


def get_user_context(user_input: str) -> str:
    """
    Identifies if this is a 'First Meeting', 'Social', or 'Teaching' interaction.
    A true implementation would check the DB for first-time user recognition.
    """
    if len(user_input.split()) > 10 or "why" in user_input.lower() or "how" in user_input.lower():
        return "Teaching"

    # Defaulting to 'First Meeting' logic for prototypes when identity is queried
    if "hi" in user_input.lower() or "who" in user_input.lower():
        return "First Meeting"
    return "Social"


def execute_worker_phase(engine: KidEngine):
    """Relational lookup and Template response"""
    if not is_teacher_present():
        error_log("Teacher not present. The Kid cannot vocalize thoughts.")
        return

    print("\n--- Worker Phase Active. Type 'exit' to quit. ---")
    while True:
        try:
            user_input = input("USER: ")
            if user_input.lower() in ["exit", "quit", "q"]:
                break

            trace_log("SEARCHING", "Querying .rem database for concepts...")

            # Simple keyword extraction (ignore empty strings, allow 'hi')
            keywords = [
                kw for kw in user_input.replace("?", "").replace(".", "").split() if len(kw) > 0
            ]

            # Situational Context Logic
            current_situation = get_user_context(user_input)

            if current_situation == "Teaching":
                trace_log(
                    "CONTEXT SWITCH",
                    f"Structural Dissonance triggered -> {current_situation}",
                    color="YELLOW",
                )
            elif current_situation == "First Meeting":
                trace_log(
                    "CONTEXT SWITCH",
                    f"First Contact detected -> {current_situation}",
                    color="YELLOW",
                )
                # GUARDRAIL: Injecting identity words directly into the solver to avoid
                # general dictionary matches pulling completely wrong data
                keywords.extend(["is_named", "identity", "am", "name"])

            facts = engine.query_brain_cra(keywords, current_situation)
            if not facts:
                print("THE KID: I don't know that yet, let me ask my Teacher.")

                # Proactive Learning Loop
                prompt = (
                    f"Please provide a concise answer to the user's question: '{user_input}'.\n"
                    "Then format the core facts into $Subject | Relation | Object | Context$ "
                    "quadruplets.\nUse a brief Context like 'Science', 'Social', 'Math', etc."
                )

                try:
                    from core.teacher import MODEL_NAME, client, teacher_lock

                    with teacher_lock:
                        response = client.generate(model=MODEL_NAME, prompt=prompt, stream=False)
                    teacher_answer = response.get("response", "")

                    # Store any new quadruplets returned by the teacher
                    from core.teacher import translate_to_quadruplets

                    new_quads = translate_to_quadruplets(teacher_answer)
                    if new_quads:
                        trace_log(
                            "LEARNING ON THE FLY",
                            f"Extracted {len(new_quads)} new facts.",
                            color="GREEN",
                        )
                        for quad in new_quads:
                            engine.store_quadruplet(quad)
                        engine.conn.commit()  # ADDED: Commit facts to DB immediately

                    print(f"TEACHER: {teacher_answer.split('$')[0].strip()}")

                except Exception as e:
                    error_log(f"Could not ask Teacher: {e}")
            else:
                trace_log("FOUND EXACT FACTS", str(facts), color="GREEN")
                trace_log("ASKING TEACHER", f"Sending {len(facts)} facts to vocal cords.")
                response = vocalize(facts, user_input)
                print(f"THE KID: {response}")
            print("-" * 50)

        except KeyboardInterrupt:
            print("\nShutting down The Kid forcefully...")
            os._exit(0)
        except Exception as e:
            error_log(f"Worker phase encountered an error: {e}")


def continuous_learning_loop():
    """Runs continuously in the background to handle library drops and math logic."""
    # Isolated Engine instance for parallel SQLite execution via WAL mode
    background_engine = KidEngine(silent_trace=True)
    while True:
        try:
            auto_generate_missions(background_engine)
            if get_new_missions():
                trace_log(
                    "AUTONOMY",
                    "Background thread executing new knowledge ingestion...",
                    color="YELLOW",
                    show_in_console=False,
                )
                execute_learning_phase(background_engine)
                execute_dream_phase(background_engine)
                trace_log(
                    "AUTONOMY",
                    "Background digestion complete. Matrices optimized.",
                    color="BLUE",
                    show_in_console=False,
                )
        except Exception as e:
            error_log(f"Background thread crashed but catching internally: {e}")
        time.sleep(10)  # Check for new PDFs every 10 seconds


def main_loop():
    clear_trace_log()
    trace_log("SYSTEM START", "The Kid is awake.", color="MAGENTA")

    # Launch purely biological parallel background processing (Breathing / Reading)
    learning_thread = threading.Thread(target=continuous_learning_loop, daemon=True)
    learning_thread.start()

    # Launch Foreground logic (Speaking)
    foreground_engine = KidEngine()
    execute_worker_phase(foreground_engine)


if __name__ == "__main__":
    main_loop()
