import json
import os
import re
import socket
import threading
import time

from core.engine import KidEngine
from core.logger import clear_trace_log, error_log, trace_log
from core.vocal_cords import generate_sentence

MISSIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "missions"))
LIBRARY_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "library"))


def _create_mission(rel_path: str, mission_path: str, engine: KidEngine):
    """Helper to write mission file."""
    trace_log(
        "AUTONOMY",
        f"Discovered new knowledge: {rel_path}",
        color="YELLOW",
        show_in_console=not getattr(engine, "silent_trace", False),
    )
    mission_data = {
        "action": "ingest_file",
        "goal": f"Autonomous learning of {rel_path}",
        "target_file": rel_path,
        "completed": False,
    }
    try:
        os.makedirs(MISSIONS_DIR, exist_ok=True)
        with open(mission_path, "w", encoding="utf-8") as f:
            json.dump(mission_data, f, indent=4)
    except Exception as e:
        error_log(f"Failed to auto-generate mission for {rel_path}: {e}")


def auto_generate_missions(engine: KidEngine):
    """Recursively scans the library for new files and creates learning missions."""
    if not os.path.exists(LIBRARY_DIR):
        return

    for root, _, files in os.walk(LIBRARY_DIR):
        for filename in files:
            if filename.startswith("."):
                continue
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, LIBRARY_DIR)

            if engine.is_file_ingested(engine.hash_file(file_path)):
                continue

            mission_key = rel_path.replace(os.sep, "_")
            mission_path = os.path.join(MISSIONS_DIR, f"auto_learn_{mission_key}.json")

            if not os.path.exists(mission_path):
                _create_mission(rel_path, mission_path, engine)


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
    Pillar A: Autonomous Truth Audit.
    Finds conflicting nodes and uses the judicial protocol to prune lies.
    """
    contradictions = engine.find_contradictions()
    if not contradictions:
        return

    from core.teacher import adjudicate_facts

    # Limit per loop to prevent CPU spike
    for rid1, rid2, sub, rel, obj1, obj2, ctx in contradictions[:10]:
        trace_log("DISSONANCE", f"Self-Audit: {sub} | {rel} | {obj1} vs {obj2}", color="YELLOW")

        fact_a = f"${sub} | {rel} | {obj1} | {ctx}$"
        fact_b = f"${sub} | {rel} | {obj2} | {ctx}$"

        decision = adjudicate_facts(fact_a, fact_b)
        winner = decision.get("winner", "BOTH")
        reasoning = decision.get("reasoning", "No logic provided.")
        corrected = decision.get("corrected_quadruplet")
        log_tag = "AUDIT RESOLVED"

        if winner == "A":
            engine.cursor.execute(engine.DELETE_QUERY, (rid2,))
            trace_log(log_tag, f"Kept: {obj1} | Pruned: {obj2}. Logic: {reasoning}", color="GREEN")
        elif winner == "B":
            engine.cursor.execute(engine.DELETE_QUERY, (rid1,))
            trace_log(log_tag, f"Kept: {obj2} | Pruned: {obj1}. Logic: {reasoning}", color="GREEN")
        elif winner == "NEITHER":
            engine.cursor.execute("DELETE FROM quadruplets WHERE rowid IN (?, ?)", (rid1, rid2))
            trace_log(log_tag, f"Destroyed both {obj1} and {obj2}. Logic: {reasoning}", color="RED")

        if corrected:
            engine.store_quadruplet(corrected)
            trace_log(log_tag, f"Corrected to: {corrected}. Logic: {reasoning}", color="CYAN")

        # Commit per adjudication so the background process doesn't lock SQLite for 10 seconds.
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

    # Math Routing (Phase 18)
    # Check for numbers and math symbols
    if re.search(r"\d+", user_input) and any(op in user_input for op in "+-*/="):
        return "Math"

    if "hi" in user_input.lower() or "hello" in user_input.lower() or "hey" in user_input.lower():
        return "Social"

    return "General"


def extract_keywords(user_input: str) -> tuple[list[str], str, str]:
    """Intelligent Keyword Extraction (Phase 17/18)"""
    processed_input = user_input.replace("?", "").replace(".", "")
    for char in "+-*/=":
        processed_input = processed_input.replace(char, f" {char} ")

    raw_kws = [kw for kw in processed_input.split() if len(kw) > 0]

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
    keywords = [kw for kw in raw_kws if kw.lower() not in stop_words]
    if not keywords and raw_kws:
        keywords = raw_kws

    current_situation = get_user_context(user_input)
    if current_situation == "Identity":
        keywords.extend(["is_named", "identity", "am", "name", "Ali"])
    elif current_situation == "Math":
        # Specific Extraction for Math (Phase 18)
        # We look for the arithmetic pattern and put it at the start as a single keyword
        math_match = re.search(r"(\d+\s*[\+\-\*\/]\s*\d+)", processed_input)
        if math_match:
            # We put the whole expression as the first keyword, and individual numbers after
            expr = math_match.group(1).strip()
            # Remove spaces for tighter matching
            keywords = [expr, expr.replace(" ", "")] + keywords
    elif current_situation == "Social":
        # Template Resonance mapping for fast non-LLM responses
        lower_input = user_input.lower()
        if any(w in lower_input for w in ["bye", "goodbye", "later", "see you"]):
            keywords.extend(["parting", "template"])
        elif any(w in lower_input for w in ["right", "correct", "agree", "yes"]):
            keywords.extend(["agreement", "template", "confirmation"])
        elif any(w in lower_input for w in ["hello", "hi", "hey", "morning", "evening"]):
            keywords.extend(["greeting", "template", "casual"])

    return keywords, current_situation, processed_input


def handle_teacher_query(user_input: str, engine: KidEngine) -> str:
    """ALI'S GOLD-FISH FIX: Actually ask teacher and INGEST the knowledge"""
    trace_log("TEACHER", f"Ali is asking teacher for: {user_input}...", color="YELLOW")

    prompt = (
        f"You are a Teacher assisting Ali. Provide a concise answer to: '{user_input}'.\n"
        "Then, format the core knowledge into strictly formatted $Subject | Relation | Object | Context$ quadruplets.\n"
        "Use the 'Math' context for calculations, or 'Social' for conversation."
    )

    from core.teacher import MODEL_NAME, ollama_client, teacher_lock, translate_to_quadruplets

    try:
        with teacher_lock:
            resp = ollama_client.generate(model=MODEL_NAME, prompt=prompt, stream=False)

        full_response = resp.get("response", "")

        # Extract and Store for Future Memory (ALI LEARNS HERE)
        new_quads = translate_to_quadruplets(full_response)
        if new_quads:
            for quad in new_quads:
                engine.store_quadruplet(quad)
            engine.conn.commit()
            trace_log(
                "LEARNING",
                f"Ali just learned {len(new_quads)} new facts about this!",
                color="GREEN",
            )

        return f"TEACHER: {full_response.split('$')[0].strip()}"

    except Exception as e:
        error_log(f"Teacher ingestion failed: {e}")
        return "ALI: I am having trouble connecting to my Teacher right now."


def process_correction(
    user_input: str, processed_input: str, engine: KidEngine
) -> tuple[str, bool]:
    """Processes a user correction and attempts fast-learning + Preference Tracking (Pillar B)."""
    engine.backpropagate_feedback(correct=False)

    # Pillar B: Implicit Preference Learning
    # Track that the 'Father' (The User) corrected Ali on this specific topic
    # We use 'User' as a generic name for now unless identity is known
    pref_fact = f"$User | Prefers | Correction to {processed_input.strip()} | UserPreference$"
    engine.store_quadruplet(pref_fact)

    # Expanded patterns to handle "4+4 = 8" or "is 8"
    correction_patterns = [r"is\s+(.+)$", r"it\s+is\s+(.+)$", r"answer\s+is\s+(.+)$", r"=\s*(.*)$"]

    for pattern in correction_patterns:
        match = re.search(pattern, user_input.lower())
        if match:
            correction_value = match.group(1).strip()
            # Try to reconstruct a math fact
            # Check processed_input (original query) for arithmetic operators
            if any(op in processed_input for op in "+-*/"):
                expr_match = re.search(r"(\d+\s*[\+\-\*\/]\s*\d+)", processed_input)
                if expr_match:
                    expr = expr_match.group(1).strip()
                    new_fact = f"${expr} | Equals | {correction_value} | Math$"
                    engine.store_quadruplet(new_fact)
                    engine.conn.commit()
                    trace_log("FAST LEARNING", f"Intercepted correction: {new_fact}", color="GREEN")
                    return (
                        f"THE KID: I am sorry. I have updated my memory. It is indeed {correction_value}.",
                        False,
                    )

    return "THE KID: I am sorry. I have adjusted my memory based on your correction.", True


def execute_idle_curiosity_phase(engine: KidEngine):
    """
    The 'Greedy Learner' Loop. Ali picks a random subject from his brain
    and the Teacher provides a mission (Science, Logic, or History).
    """
    engine.cursor.execute("SELECT subject FROM quadruplets ORDER BY RANDOM() LIMIT 1")
    result = engine.cursor.fetchone()
    random_concept = result[0] if result else None

    from core.teacher import proactive_inquiry

    mission = proactive_inquiry(random_concept)

    if not mission or not mission.get("inquiry"):
        return

    trace_log(
        "CURIOSITY",
        f"Ali is thinking in {mission['style']} mode... '{mission['inquiry']}'",
        color="MAGENTA",
        show_in_console=True,
    )

    new_quads = mission.get("facts", [])
    if new_quads:
        trace_log(
            "LEARNING ON THE FLY",
            f"Curiosity satisfied! Extracted {len(new_quads)} new {mission['style']} facts.",
            color="GREEN",
            show_in_console=True,
        )
        for quad in new_quads:
            engine.store_quadruplet(quad)
        engine.conn.commit()


def process_cli_interaction(engine: KidEngine) -> bool:
    """Handles a single CLI interaction loop step. Returns False if exiting."""
    try:
        user_input = input("USER: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            return False

        trace_log("SEARCHING", f"Processing CLI Request: '{user_input}'", color="CYAN")

        # 1. Extraction & Retrieval & Inference (Pillar C)
        keywords, current_situation, processed_input = extract_keywords(user_input)
        facts = engine.query_brain_cra(keywords, current_situation)
        if not facts:
            # Deep Thinking fallback
            trace_log(
                "INFERENCE",
                f"No shallow hits for '{keywords}'. Transitioning to Pillar C: Deep Graph Traversal...",
                color="BLUE",
            )
            facts = engine.query_graph_inference(keywords, depth=2)

        final_response = ""
        needs_teacher = False

        # 2. Logic & Back-Prop (Phase 18: Enhanced Correction Detection)
        correction_prompts = [
            "no",
            "wrong",
            "incorrect",
            "false",
            "that is not true",
            "is wrong",
            "is incorrect",
        ]
        is_correction = any(cp in user_input.lower()[:15] for cp in correction_prompts)

        if is_correction:
            final_response, needs_teacher = process_correction(user_input, processed_input, engine)
        else:
            if facts:
                final_response = f"ALI: {generate_sentence(facts)}"
                engine.backpropagate_feedback(correct=True)
            else:
                final_response = "ALI: I don't know that yet, let me ask my Teacher."
                needs_teacher = True

        # 3. Teacher Fallback
        if needs_teacher:
            final_response = handle_teacher_query(user_input, engine)

        print(final_response)
        print("-" * 50)
        return True

    except Exception as e:
        error_log(f"Worker phase encountered an error: {e}")
        return True


def execute_worker_phase(engine: KidEngine):
    """Relational lookup and Algorithmic Native response (CLI version)"""
    print("\n--- Worker Phase Active. Type 'exit' to quit. ---")
    while process_cli_interaction(engine):
        time.sleep(0.1)  # Avoid busy-waiting CPU spin

    print("Shutting down CLI worker...")


def execute_server_worker(engine: KidEngine, port: int = 5050):
    """
    Acts as the Neural Hub. Listens for connections from chat_terminal.py.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(("0.0.0.0", port))
        server.listen(5)
        trace_log(
            "NEURAL HUB",
            f"Kid Server active on port {port}. Use chat_terminal.py to connect.",
            color="MAGENTA",
        )
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

        # 1. Shutdown processing
        if user_input.lower() in ["shutdown", "shutdown_server", "terminate_brain"]:
            client.send("SYSTEM: Brain server shutting down...".encode("utf-8"))
            client.close()
            os._exit(0)

        # 2. Information Extraction
        keywords, current_situation, processed_input = extract_keywords(user_input)

        # 3. Brain Retrieval & Inference (Pillar C)
        facts = engine.query_brain_cra(keywords, current_situation)
        if not facts:
            # Deep Thinking fallback
            trace_log(
                "INFERENCE",
                f"No shallow hits for '{keywords}'. Transitioning to Pillar C: Deep Graph Traversal...",
                color="BLUE",
            )
            facts = engine.query_graph_inference(keywords, depth=2)

        final_response = ""
        needs_teacher = False

        # 4. Correction handling (Phase 18: Enhanced Correction Detection)
        correction_prompts = [
            "no",
            "wrong",
            "incorrect",
            "false",
            "that is not true",
            "is wrong",
            "is incorrect",
        ]
        is_correction = any(cp in user_input.lower()[:15] for cp in correction_prompts)

        if is_correction:
            final_response, needs_teacher = process_correction(user_input, processed_input, engine)
        else:
            if facts:
                final_response = f"ALI: {generate_sentence(facts)}"
                engine.backpropagate_feedback(correct=True)
            else:
                final_response = "ALI: I don't know that yet, let me ask my Teacher."
                needs_teacher = True

        # 5. Teacher Fallback
        if needs_teacher:
            final_response = handle_teacher_query(user_input, engine)

        client.send(final_response.encode("utf-8"))
        client.close()
    except Exception as e:
        error_log(f"Handle client failed: {e}")
        client.close()


def execute_autonomous_audit(engine: KidEngine):
    """
    Pillar A: Self-Audit Mission. Ali scans his brain for conflicts
    and uses the Judicial Protocol (Teacher) to resolve them.
    """
    conflicts = engine.find_contradictions()
    if not conflicts:
        return

    from core.teacher import adjudicate_facts

    # Limit audit to a small cluster per loop for performance
    for id1, id2, s, r, o1, o2, context in conflicts[:5]:
        fact_a = f"${s} | {r} | {o1} | {context}$"
        fact_b = f"${s} | {r} | {o2} | {context}$"

        trace_log("JUDICIAL AUDIT", f"Conflict Detected on Node: {s} | {r}", color="RED")
        decision = adjudicate_facts(fact_a, fact_b)

        winner = decision.get("winner")
        reasoning = decision.get("reasoning", "No reasoning provided.")
        corrected = decision.get("corrected_quadruplet")
        log_tag = "AUDIT RESOLVED"

        if winner == "A":
            engine.cursor.execute(engine.DELETE_QUERY, (id2,))
            trace_log(log_tag, f"Kept: {o1} | Pruned: {o2}. Reasoning: {reasoning}", color="GREEN")
        elif winner == "B":
            engine.cursor.execute(engine.DELETE_QUERY, (id1,))
            trace_log(log_tag, f"Kept: {o2} | Pruned: {o1}. Reasoning: {reasoning}", color="GREEN")
        elif corrected:
            # Overwrite both with the corrected version from Teacher
            engine.cursor.execute(engine.DELETE_QUERY, (id1,))
            engine.cursor.execute(engine.DELETE_QUERY, (id2,))
            engine.store_quadruplet(corrected)
            trace_log(log_tag, f"Corrected to: {corrected}. Reasoning: {reasoning}", color="CYAN")

        engine.conn.commit()


def continuous_learning_loop():
    """Runs continuously in the background to handle library drops and math logic."""
    # Isolated Engine instance for parallel SQLite execution via WAL mode
    background_engine = KidEngine(silent_trace=True)
    while True:
        try:
            auto_generate_missions(background_engine)
            if get_new_missions():
                trace_log("AUTONOMY", "Background thread: Executing digestion.", color="YELLOW")
                execute_learning_phase(background_engine)
                execute_dream_phase(background_engine)
            else:
                execute_idle_curiosity_phase(background_engine)

            # Pillar A: Autonomous Contradiction Audit
            adjudicate_contradictions(background_engine)

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
