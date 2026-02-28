import logging
import os

from dotenv import load_dotenv
from ollama import Client

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

logger = logging.getLogger(__name__)

client = Client(host=OLLAMA_BASE_URL)

def is_teacher_present() -> bool:
    """Check if Ollama server is running and accessible."""
    try:
        # ps() will list running models. If it fails, the daemon is unreachable.
        client.ps()
        return True
    except Exception:
        print("[ERROR] Teacher is not present (Ollama server not found).")
        return False

def translate_to_triplets(text_chunk: str) -> list[str]:
    """
    Uses the Teacher to translate a chunk of text into knowledge triplets.
    Returns a list of strings formatted as "$Subject | Relation | Object$".
    """
    if not is_teacher_present():
        return []
    
    prompt = f"""You are a precise relational extractor. \\
Extract knowledge from the text into strictly formatted triplets.
Format each extracted fact on a new line as: $Subject | Relation | Object$
Do not include any other text, explanation, or conversational filler. Only the triplets.
Extract the most important facts from the following text:

TEXT:
{text_chunk}
"""
    try:
        response = client.generate(
            model=MODEL_NAME,
            prompt=prompt,
            stream=False,
            options={
                "temperature": 0.1,
            }
        )
        result = response.get("response", "")
        
        triplets = []
        for line in result.split("\n"):
            line = line.strip()
            if line.startswith("$") and line.endswith("$") and "|" in line:
                triplets.append(line)
        return triplets

    except Exception as e:
        print(f"[ERROR] Failed to communicate with Teacher during translation: {e}")
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
        response = client.generate(
            model=MODEL_NAME,
            prompt=prompt,
            stream=False,
            options={
                "temperature": 0.7,
            }
        )
        return response.get("response", "").strip()

    except Exception as e:
        print(f"[ERROR] Failed to communicate with Teacher during vocalization: {e}")
        return "Error: Could not speak due to Teacher unavailability."
