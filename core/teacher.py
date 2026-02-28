import logging
import os

from ollama import Client

from .logger import error_log

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

logger = logging.getLogger(__name__)

client = Client(host=OLLAMA_BASE_URL)
teacher_lock = threading.Lock()


def is_teacher_present() -> bool:
    """Check if Ollama server is running and accessible."""
    try:
        # ps() will list running models. If it fails, the daemon is unreachable.
        client.ps()
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
Extract the most important facts from the following text:

TEXT:
{text_chunk}
"""
    try:
        with teacher_lock:
            response = client.generate(
                model=MODEL_NAME,
                prompt=prompt,
                stream=False,
                options={
                    "temperature": 0.1,
                },
            )
        result = response.get("response", "")

        quads = []
        for line in result.split("\n"):
            line = line.strip()
            if line.startswith("$") and line.endswith("$") and line.count("|") >= 3:
                quads.append(line)
        return quads

    except Exception as e:
        error_log(f"Failed to communicate with Teacher during translation: {e}")
        return []


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
            response = client.generate(
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
