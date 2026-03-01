import json
import os
import socket
import threading
import time

from core.engine import KidEngine
from core.logger import clear_trace_log, error_log, trace_log
from core.vocal_cords import generate_sentence

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

    # 5. Adjudicate Contradictions (Phase 10: Truth Verification)
    adjudicate_contradictions(engine)


def adjudicate_contradictions(engine: KidEngine):
    """
    Automated Truth adjudication. Finds contradictory nodes
    and asks the Teacher to resolve the tie.
    """
    contradictions = engine.find_contradictions()
    if not contradictions:
        return

    from core.teacher import adjudicate_facts

    for rid1, rid2, sub, rel, obj1, obj2, ctx in contradictions:
        trace_log(
            "DISSONANCE", f"Contradiction found: {sub} {rel} {obj1} vs {obj2}", color="YELLOW"
        )

        fact_a = f"${sub} | {rel} | {obj1} | {ctx}$"
        fact_b = f"${sub} | {rel} | {obj2} | {ctx}$"

        decision = adjudicate_facts(fact_a, fact_b)
        winner = decision.get("winner", "BOTH")
        reasoning = decision.get("reasoning", "")
        corrected = decision.get("corrected_quadruplet")

        if winner == "A":
            engine.cursor.execute(
                "UPDATE quadruplets SET strength = MIN(2.0, strength+0.1) WHERE rowid = ?", (rid1,)
            )
            engine.cursor.execute(
                "UPDATE quadruplets SET strength = strength * 0.1 WHERE rowid = ?", (rid2,)
            )
        elif winner == "B":
            engine.cursor.execute(
                "UPDATE quadruplets SET strength = MIN(2.0, strength+0.1) WHERE rowid = ?", (rid2,)
            )
            engine.cursor.execute(
                "UPDATE quadruplets SET strength = strength * 0.1 WHERE rowid = ?", (rid1,)
            )
        elif winner == "NEITHER":
            engine.cursor.execute("DELETE FROM quadruplets WHERE rowid IN (?, ?)", (rid1, rid2))

        if corrected:
            engine.store_quadruplet(corrected)

        trace_log("ADJUDICATION", f"Winner: {winner}. Reasoning: {reasoning}", color="CYAN")

    engine.conn.commit()


def get_user_context(user_input: str) -> str:
    """
    Identifies if this is a 'First Meeting', 'Social', or 'Teaching' interaction.
    A true implementation would check the DB for first-time user recognition.
    """
    if len(user_input.split()) > 10 or "why" in user_input.lower() or "how" in user_input.lower():
        return "Teaching"

    # Identity Routing (Phase 17)
    identity_keywords = ["who", "name", "who are you", "what is your name", "your name"]
    if any(ik in user_input.lower() for ik in identity_keywords):
        return "Identity"
    
    if "hi" in user_input.lower() or "hello" in user_input.lower() or "hey" in user_input.lower():
        return "Social"

    return "General"


def execute_idle_curiosity_phase(engine: KidEngine):
    """
    The 'Greedy Learner' Loop. If The Kid has no incoming Library files,
    he randomly picks a topic from his brain and asks the Teacher to expand on it!
    """
    engine.cursor.execute("SELECT subject FROM quadruplets ORDER BY RANDOM() LIMIT 1")
    result = engine.cursor.fetchone()
    if not result:
        return  # Brain is totally empty, nothing to be curious about yet.

    random_concept = result[0]

    trace_log(
        "CURIOSITY",
        f"Idle brain thinking... 'I wonder what else I can learn about {random_concept}?'",
        color="MAGENTA",
        show_in_console=True,
    )

    prompt = (
        f"You are a Teacher. Provide a completely new, deeper, or different perspective on the concept: '{random_concept}'.\n"
        "Explain it clearly in a few sentences.\n"
        "Then format the core facts into $Subject | Relation | Object | Context$ quadruplets."
    )

    try:
        from core.teacher import MODEL_NAME, ollama_client, teacher_lock
        from core.teacher import translate_to_quadruplets

        with teacher_lock:
            response = ollama_client.generate(model=MODEL_NAME, prompt=prompt, stream=False)
        teacher_answer = response.get("response", "")

        new_quads = translate_to_quadruplets(teacher_answer)
        if new_quads:
            trace_log(
                "LEARNING ON THE FLY",
                f"Curiosity satisfied! Extracted {len(new_quads)} new facts about {random_concept}.",
                color="GREEN",
                show_in_console=True,
            )
            for quad in new_quads:
                engine.store_quadruplet(quad)
            engine.conn.commit()

    except Exception as e:
        error_log(f"Curiosity phase failed: {e}")


def execute_worker_phase(engine: KidEngine):
    """Relational lookup and Algorithmic Native response"""
    print("\n--- Worker Phase Active. Type 'exit' to quit. ---")
    while True:
        try:
            user_input = input("USER: ")
            if user_input.lower() in ["exit", "quit", "q"]:
                break

            trace_log("SEARCHING", "Querying .rem database for concepts...")

            # Advanced keyword extraction (omit functional stop words)
            stop_words = {
                "are",
                "is",
                "the",
                "a",
                "an",
                "am",
                "of",
                "to",
                "in",
                "it",
                "that",
                "this",
                "my",
                "your",
                "for",
                "do",
                "how",
                "what",
                "where",
                "when",
                "why",
                "you",
            }
            raw_kws = [
                kw for kw in user_input.replace("?", "").replace(".", "").split() if len(kw) > 0
            ]

            keywords = [kw for kw in raw_kws if kw.lower() not in stop_words]
            if not keywords and raw_kws:
                keywords = raw_kws  # Fallback if they only type stop words

            # Situational Context Logic
            current_situation = get_user_context(user_input)

            if current_situation == "Teaching":
                trace_log(
                    "CONTEXT SWITCH",
                    f"Structural Dissonance triggered -> {current_situation}",
                    color="YELLOW",
                )
            elif current_situation == "Identity":
                trace_log(
                    "CONTEXT SWITCH",
                    f"Identity query detected -> {current_situation}",
                    color="YELLOW",
                )
                # GUARDRAIL: Injecting identity words directly into the solver to avoid
                # general dictionary matches pulling completely wrong data
                keywords.extend(["is_named", "identity", "am", "name", "Ali"])

            facts = engine.query_brain_cra(keywords, current_situation)

            # --- PHASE 10: CORRECTION DETECTION ---
            corrections = ["no", "wrong", "incorrect", "false", "that is not true"]
            if any(user_input.lower().startswith(c) for c in corrections):
                trace_log(
                    "FEEDBACK",
                    "User reported an error. Back-propagating truth values...",
                    color="RED",
                )
                engine.backpropagate_feedback(correct=False)
                print("THE KID: I am sorry. I have adjusted my memory based on your correction.")
                # After a correction, we ask the teacher to explain why or provide the truth
                needs_teacher = True
            else:
                if facts:
                    trace_log("FOUND EXACT FACTS", str(facts), color="GREEN")
                    trace_log(
                        "ALGORITHMIC VOCAL CORDS", f"Synthesizing {len(facts)} internal facts."
                    )
                    response = generate_sentence(facts)
                    print(f"ALI: {response}")
                    # Reinforce the fact we just told the user (implicit positive feedback)
                    engine.backpropagate_feedback(correct=True)

            needs_teacher = False
            if not facts:
                print("ALI: I don't know that yet, let me ask my Teacher.")
                needs_teacher = True
            elif any(w in user_input.lower() for w in ["explain", "meaning", "learn", "better"]):
                print("ALI: *Thinking... I should learn more about this from my Teacher.*")
                needs_teacher = True

            if needs_teacher:
                # Proactive Learning Loop
                prompt = (
                    f"Please provide a concise answer to the user's question: '{user_input}'.\n"
                    "Then format the core facts into $Subject | Relation | Object | Context$ "
                    "quadruplets.\nUse a brief Context like 'Science', 'Social', 'Math', etc."
                )

                try:
                    from core.teacher import MODEL_NAME, ollama_client, teacher_lock

                    with teacher_lock:
                        response_teacher = ollama_client.generate(
                            model=MODEL_NAME, prompt=prompt, stream=False
                        )
                    teacher_answer = response_teacher.get("response", "")

                    # Store any new quadruplets returned by the teacher
                    from core.teacher import translate_to_quadruplets

                    new_quads = translate_to_quadruplets(teacher_answer)
                    if new_quads:
                        trace_log(
                            "LEARNING ON THE FLY",
                            f"Extracted {len(new_quads)} new facts from Teacher.",
                            color="GREEN",
                        )
                        for quad in new_quads:
                            engine.store_quadruplet(quad)
                        engine.conn.commit()  # ADDED: Commit facts to DB immediately

                    if not facts:
                        print(f"TEACHER: {teacher_answer.split('$')[0].strip()}")
                    else:
                        trace_log(
                            "TEACHER BACKGROUND",
                            "Teacher provided extra context. Brain expanded.",
                            color="CYAN",
                        )

                except Exception as e:
                    error_log(f"Could not ask Teacher: {e}")
            print("-" * 50)

        except KeyboardInterrupt:
            print("\nShutting down The Kid forcefully...")
            os._exit(0)
        except Exception as e:
            error_log(f"Worker phase encountered an error: {e}")


def execute_server_worker(engine: KidEngine, port: int = 5050):
    """
    Acts as the Neural Hub. Listens for connections from chat_terminal.py.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(("0.0.0.0", port))
        server.listen(5)
        trace_log("NEURAL HUB", f"Kid Server active on port {port}. Use chat_terminal.py to connect.", color="MAGENTA")
    except Exception as e:
        error_log(f"Failed to bind Neural Hub: {e}")
        return

    while True:
        client, _ = server.accept()
        # Handle each client in a short-lived thread or sequentially if low load
        threading.Thread(target=handle_client_request, args=(client, engine), daemon=True).start()


def handle_client_request(client, engine: KidEngine):
    """Processes a single interaction from the chat client."""
    try:
        data = client.recv(4096).decode("utf-8")
        if not data:
            client.close()
            return

        user_input = data.strip()
        trace_log("SEARCHING", f"Processing Neural Request: '{user_input}'", color="CYAN")

        # --- PHASE 12: SHUTDOWN COMMAND ---
        if user_input.lower() in ["shutdown", "shutdown_server", "terminate_brain"]:
            client.send("SYSTEM: Brain server shutting down...".encode("utf-8"))
            client.close()
            trace_log("SYSTEM", "Remote shutdown command received. Closing...", color="RED")
            os._exit(0)

        # 1. Extraction & Context
        stop_words = {"are", "is", "the", "a", "an", "am", "of", "to", "in", "it", "that", "this", "my", "your", "for", "do", "how", "what", "where", "when", "why", "you"}
        raw_kws = [kw for kw in user_input.replace("?", "").replace(".", "").split() if len(kw) > 0]
        keywords = [kw for kw in raw_kws if kw.lower() not in stop_words]
        if not keywords and raw_kws: keywords = raw_kws
        
        current_situation = get_user_context(user_input)
        if current_situation == "Identity":
            keywords.extend(["is_named", "identity", "am", "name", "Ali"])

        # 2. Brain Retrieval (CRA Math)
        facts = engine.query_brain_cra(keywords, current_situation)
        
        final_response = ""
        needs_teacher = False

        # 3. Logic & Back-Prop
        corrections = ["no", "wrong", "incorrect", "false", "that is not true"]
        if any(user_input.lower().startswith(c) for c in corrections):
            engine.backpropagate_feedback(correct=False)
            final_response = "THE KID: I am sorry. I have adjusted my memory based on your correction."
            needs_teacher = True
        else:
            if facts:
                response_text = generate_sentence(facts)
                final_response = f"ALI: {response_text}"
                engine.backpropagate_feedback(correct=True)
            else:
                final_response = "ALI: I don't know that yet, let me ask my Teacher."
                needs_teacher = True

        # 4. Teacher Fallback (Background/Proactive)
        if needs_teacher:
            # We return the initial "I don't know" immediately, and let the teacher work in background
            # For a better UI, we can wait 1-2 seconds for a teacher summary if facts were empty
            if not facts:
                prompt = f"Provide a concise answer and quadruplets for: '{user_input}'"
                from core.teacher import MODEL_NAME, ollama_client, teacher_lock
                with teacher_lock:
                    resp = ollama_client.generate(model=MODEL_NAME, prompt=prompt, stream=False)
                teacher_text = resp.get("response", "").split("$")[0].strip()
                final_response = f"TEACHER: {teacher_text}"

        client.send(final_response.encode("utf-8"))
        client.close()

    except Exception as e:
        error_log(f"Handle client failed: {e}")
        client.close()


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
            else:
                # Idle state -> Start Curiosity (Greedy Learning)
                execute_idle_curiosity_phase(background_engine)

        except Exception as e:
            error_log(f"Background thread crashed but catching internally: {e}")
        time.sleep(10)  # Check for new PDFs every 10 seconds


def main_loop():
    clear_trace_log()
    trace_log("SYSTEM START", "Ali is awake.", color="MAGENTA")

    # Launch purely biological parallel background processing (Breathing / Reading)
    learning_thread = threading.Thread(target=continuous_learning_loop, daemon=True)
    learning_thread.start()

    # Launch Foreground logic (Vocal Interface Server)
    foreground_engine = KidEngine()
    execute_server_worker(foreground_engine)


if __name__ == "__main__":
    main_loop()
