import logging
import os
import threading

from dotenv import load_dotenv
from ollama import Client as OllamaClient

from .logger import error_log, trace_log

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
USE_GEMINI = os.getenv("USE_GEMINI", "true").lower() == "true"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-native-audio-preview-12-2025")

logger = logging.getLogger(__name__)

# Ollama Setup (Local Personality)
ollama_client = OllamaClient(host=OLLAMA_BASE_URL)
teacher_lock = threading.Lock()

# Gemini Setup (Cloud Reader)
gemini_client = None
if GOOGLE_API_KEY and USE_GEMINI:
    try:
        from google import genai

        # Initialize with v1alpha explicitly to support experimental native-audio models
        gemini_client = genai.Client(
            api_key=GOOGLE_API_KEY, http_options={"api_version": "v1alpha"}
        )
        trace_log("TEACHER", "Gemini API initialized for background reading.", color="GREEN")
    except ImportError:
        error_log("google-genai module not found. Run 'uv add google-genai'.")
    except Exception as e:
        error_log(f"Failed to initialize Gemini: {e}")


def is_teacher_present() -> bool:
    """Check if Ollama server is running and accessible."""
    try:
        # ps() will list running models. If it fails, the daemon is unreachable.
        ollama_client.ps()
        return True
    except Exception:
        error_log("Teacher is not present (Ollama server not found).")
        return False


def translate_to_quadruplets(text_chunk: str) -> list[str]:
    """
    Uses the Teacher to translate a chunk of text into knowledge quadruplets.
    Returns a list of strings formatted as "$Subject | Relation | Object | Context$".
    """
    if not is_teacher_present():
        return []

    prompt = f"""You are a precise relational extractor. \\
Extract knowledge from the text into strictly formatted quadruplets.
Format each extracted fact on a new line as: $Subject | Relation | Object | Context$
Do not include any other text, explanation, or conversational filler. Only the quadruplets.
Context should be a single brief word like "Science", "History", "Grammar", "Identity", or "Social".
If the text contains personality or identity traits, use the "Identity" or "Social" Context, 
and relations like "is_named", "is", or "has".

***ADVANCED LOGIC INSTRUCTIONS***
If the text contains compound reasoning, use the following Relations and Contexts:
- Causality (because, therefore): $Fact A | leads_to | Fact B | Causality$
- Conditionality (if, then, unless): $Condition A | requires | Condition B | Conditionality$
- Contrast (however, although): $Fact A | contrasts_with | Fact B | Contrast$
- Addition (furthermore, moreover): $Fact A | adds_to | Fact B | Addition$

Extract the most important facts from the following text:

TEXT:
{text_chunk}
"""
    result = ""
    used_gemini = False

    # 1. Try Gemini (High-Speed Cloud)
    if gemini_client:
        try:
            # Note: We do NOT lock Gemini. The cloud handles concurrent connections perfectly,
            # allowing maximum parallel PDF ingestion.
            response = gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            result = response.text
            used_gemini = True
        except Exception as e:
            error_log(f"Gemini translation failed, falling back to Ollama: {e}")

    # 2. Fallback to Ollama (Local)
    if not used_gemini:
        try:
            with teacher_lock:
                response = ollama_client.generate(
                    model=MODEL_NAME,
                    prompt=prompt,
                    stream=False,
                    options={
                        "temperature": 0.1,
                    },
                )
            result = response.get("response", "")
        except Exception as e:
            error_log(f"Failed to communicate with local Teacher during translation: {e}")
            return []

    quads = []
    for line in result.split("\n"):
        line = line.strip()
        if line.startswith("$") and line.endswith("$") and line.count("|") >= 3:
            quads.append(line)
    return quads


def vocalize(context_facts: list[str], user_input: str) -> str:
    """
    Uses the Teacher as vocal cords to chat with the user based on provided context facts.
    """
    if not is_teacher_present():
        return "Teacher is not present. I cannot speak."

    facts_str = "\n".join(context_facts)
    prompt = f"""You are the vocal cords of an AI agent named The Kid. \\
The Kid has queried its own brain and found the following facts.
Use ONLY these facts to answer the user's input. Answer naturally.

KNOWLEDGE BASE:
{facts_str}

USER INPUT:
{user_input}
"""
    try:
        with teacher_lock:
            response = ollama_client.generate(
                model=MODEL_NAME,
                prompt=prompt,
                stream=False,
                options={
                    "temperature": 0.7,
                },
            )
        return response.get("response", "").strip()

    except Exception as e:
        error_log(f"Failed to communicate with Teacher during vocalization: {e}")
        return "Error: Could not speak due to Teacher unavailability."


def adjudicate_facts(fact_a: str, fact_b: str) -> dict:
    """
    Uses the Teacher to resolve contradictions between two facts.
    Returns a dict with 'winner' (A, B, or BOTH), 'reasoning', and 'corrected_quadruplet'.
    """
    if not is_teacher_present():
        return {"winner": "BOTH", "reasoning": "Teacher absent.", "corrected_quadruplet": None}

    prompt = f"""You are a logical adjudicator. Two conflicting facts have been found in a knowledge base.
FACT A: {fact_a}
FACT B: {fact_b}

Analyze which fact is more likely to be true for a Grade 1 level understanding of the world.
Respond in JSON format:
{{
  "winner": "A" or "B" or "NEITHER" or "BOTH",
  "reasoning": "brief explanation",
  "corrected_quadruplet": "$Subject | Relation | Object | Context$" or null
}}
"""
    try:
        with teacher_lock:
            response = ollama_client.generate(
                model=MODEL_NAME,
                prompt=prompt,
                format="json",
                stream=False,
                options={"temperature": 0.1},
            )
        import json

        return json.loads(response.get("response", "{}"))
    except Exception as e:
        error_log(f"Adjudication failed: {e}")
        return {"winner": "BOTH", "reasoning": str(e), "corrected_quadruplet": None}


def proactive_inquiry(focus_topic: str = None) -> dict:
    """
    Teacher generates a proactive learning mission.
    Styles: 'Investigative' (Science), 'Postulate' (Logic), 'Recall' (History), 'Synthesis' (General).
    """
    if not is_teacher_present():
        return {}

    # Focused on top mathematician/linguist goal (Phase 18)
    styles = ["Arithmetic", "Algebra", "Logic", "Grammar", "Etymology", "Socratic"]
    import random
    style = random.choice(styles)
    
    topic_str = f"the concept of '{focus_topic}'" if focus_topic else "a foundational mathematical or linguistic concept"
    
    prompt = f"""You are a Proactive Master Teacher. Focus ONLY on Math and Language Mastery for Ali.
Mission Style: {style}
Target Topic: {topic_str}

If the style is:
- Arithmetic: Focus on addition, subtraction, multiplication, division facts.
- Algebra: Focus on variables, equations (like x+y=z), and unknowns.
- Logic: Focus on logical connectors, boolean truth, and syllogisms.
- Grammar: Focus on sentence structure, parts of speech, and syntax rules.
- Etymology: Focus on the origins and meanings of specific words.
- Socratic: Ask a deep 'Why' or 'How' question about numbers or words.

Generate a brief (1-2 sentence) inquiry to Ali.
Then, provide 5-8 $Subject | Relation | Object | Context$ quadruplets that answer or expand on this inquiry.
Make sure the Context is 'Math' or 'Language'.

Response Format:
[INQUIRY]: Your question or statement to Ali.
[FACTS]:
$Subject | Relation | Object | Context$
...
"""
    try:
        with teacher_lock:
            # Use Gemini if available for higher quality variety, else Ollama
            if gemini_client:
                 response = gemini_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
                 result = response.text
            else:
                response = ollama_client.generate(model=MODEL_NAME, prompt=prompt, stream=False)
                result = response.get("response", "")

        lines = result.split("\n")
        inquiry = ""
        facts = []
        for line in lines:
            if line.startswith("[INQUIRY]:"):
                inquiry = line.replace("[INQUIRY]:", "").strip()
            elif line.startswith("$") and line.endswith("$"):
                facts.append(line.strip())
        
        return {"style": style, "inquiry": inquiry, "facts": facts}

    except Exception as e:
        error_log(f"Proactive inquiry failed: {e}")
        return {}
