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


def generate_sentence(context_facts: list[str]) -> str:
    """
    Pure algorithmic NLP parser that converts quadruplets directly into English
    sentences without relying on an LLM for token generation.
    """
    if not context_facts:
        return "I don't have enough information in my memory to say anything about that."

    trace_log("VOCAL CORDS", f"Synthesizing {len(context_facts)} facts algorithmically...")

    # Define some random personality templates so he doesn't sound entirely robotic
    intro_templates = [
        "Well, according to my memory, ",
        "I recall that ",
        "My database shows that ",
        "Thinking about it... ",
        "I am quite certain that ",
        "",  # Sometimes just say the fact directly
    ]

    sentences = []

    for fact in context_facts:
        parsed = _parse_quadruplet(fact)
        if not parsed:
            continue

        subject, relation, obj, _ = parsed
        clean_relation = relation.replace("_", " ")

        # --- 1. CONVERSATIONAL TEMPLATING ---
        # If the math indicates this is a direct conversational response, say it directly!
        conversational_relations = [
            "is responded to by saying",
            "is replied to with",
            "defaults to asking",
            "is rewarded by saying",
            "are accepted cheerfully by stating",
            "is celebrated with the phrase",
        ]

        if any(cr in clean_relation.lower() for cr in conversational_relations):
            # Extract the raw conversational object and clean any quotes around it
            sentence = obj.strip().strip('"').strip("'")
            # Don't add an intro template to a direct conversational response
            sentences.append(sentence)
            continue

        # --- 2. VERB & ARTICLE MATHEMATICS (NLP) ---
        intro = random.choice(intro_templates)

        # Punctuation logic
        if clean_relation.lower() == "asked" or "defaults to asking" in clean_relation.lower():
            punctuation = "?" if "question" in obj.lower() else "."
        else:
            punctuation = "."

        # Synthesize standard fact
        sentence = f"{intro}{subject} {clean_relation} {obj}{punctuation}"

        # Capitalize first letter
        sentence = sentence[0].upper() + sentence[1:]
        sentences.append(sentence)

    # --- 3. DEDUPLICATION AND CLEANUP ---
    unique_sentences = []
    for s in sentences:
        if s not in unique_sentences:
            unique_sentences.append(s)

    # Limit to top 3 facts to avoid a wall of text
    final_text = " ".join(unique_sentences[:3])

    return final_text
