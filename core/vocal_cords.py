import random

from core.logger import trace_log


def _parse_quadruplet(quad_str: str) -> tuple[str, str, str, str] | None:
    """Takes a raw '$Subject | Relation | Object | Context$' string and extracts the parts."""
    clean_str = quad_str.strip()
    if not (clean_str.startswith("$") and clean_str.endswith("$")):
        return None

    parts = [p.strip() for p in clean_str[1:-1].split("|")]
    if len(parts) >= 4:
        return parts[0], parts[1], parts[2], parts[3]
    if len(parts) == 3:
        return parts[0], parts[1], parts[2], "General"

    return None


def _get_identity_sentence(clean_relation: str, obj: str) -> str:
    """Specialized synthesis for Ali's identity."""
    if "is" in clean_relation:
        return f"I am {obj}."
    if "is_named" in clean_relation or "name" in clean_relation:
        return "My name is Ali."
    if "am" in clean_relation:
        return "I am indeed your neuro-symbolic specialist."
    return f"I {clean_relation} {obj}."

def _get_logic_sentence(subject: str, clean_relation: str, obj: str) -> str:
    """Synthesis for causal and logical connections."""
    if any(r in clean_relation for r in ["leads to", "causes", "because"]):
        return f"{subject} because {obj}."
    if any(r in clean_relation for r in ["requires", "condition"]):
        return f"If {subject}, then {obj}."
    if any(r in clean_relation for r in ["contrasts with", "opposite"]):
        return f"{subject}, however {obj}."
    if any(r in clean_relation for r in ["adds to", "also"]):
        return f"{subject}. Furthermore, {obj}."
    return f"{subject} {clean_relation} {obj}."

def _synthesize_fact(subject: str, relation: str, obj: str, context: str) -> str:
    """Synthesizes a single fact into a natural English sentence."""
    clean_relation = relation.replace("_", " ").lower()
    
    # 1. Identity & Greeting
    if "ali" in subject.lower() or "ali" in obj.lower() or context.lower() == "identity":
        return _get_identity_sentence(clean_relation, obj)

    # 2. Causality & Logic
    logic_words = ["leads to", "causes", "because", "requires", "condition", "contrasts", "opposite", "adds to", "also"]
    if any(rw in clean_relation for rw in logic_words):
        return _get_logic_sentence(subject, clean_relation, obj)

    # 3. Conversational Relations
    conversational_list = ["responded", "replied", "asking", "stated", "phrase", "words"]
    if any(cr in clean_relation for cr in conversational_list):
        return obj.strip().strip('"').strip("'")

    # 4. Standard Templates
    return _synthesize_default(subject, clean_relation, obj)

def _synthesize_default(subject: str, clean_relation: str, obj: str) -> str:
    """Fallback standard synthesis."""
    intro_templates = ["Well, according to my memory, ", "I recall that ", "My database shows that ", "Thinking about it... ", "I am quite certain that ", ""]
    intro = random.choice(intro_templates)
    punctuation = "?" if "question" in obj.lower() or "ask" in clean_relation else "."
    sentence = f"{intro}{subject} {clean_relation} {obj}{punctuation}"
    return sentence[0].upper() + sentence[1:]


def generate_sentence(context_facts: list[str]) -> str:
    """
    Synthesizes multiple quadruplets into natural flow.
    Uses 'Math Approach': joins facts that share a subject or context.
    """
    if not context_facts:
        return "I don't have enough resonant facts in my memory to answer that at the moment."

    trace_log("VOCAL CORDS", f"Synthesizing {len(context_facts)} facts algorithmically...")

    results = []
    for fact in context_facts:
        parsed = _parse_quadruplet(fact)
        if parsed:
            results.append(_synthesize_fact(*parsed))

    # Basic join for now. We can make this even smarter (e.g., using 'and' or 'also').
    # Using 'Furthermore' or 'Also' as a joiner between distinct facts.
    unique_sentences = list(dict.fromkeys(results)) # Dedupe while preserving order
    
    if len(unique_sentences) > 1:
        return unique_sentences[0] + " Plus, " + unique_sentences[1].lower()
    
    return unique_sentences[0] if unique_sentences else "I cannot find the words for that yet."
