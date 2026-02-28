import math
from typing import Dict


def calculate_cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """
    Calculates the cosine similarity between two sparse connection vectors.
    Similarity(A, B) = sum(R_A * R_B) / (sqrt(sum(R_A^2)) * sqrt(sum(R_B^2)))
    """
    dot_product = 0.0
    for key in set(vec_a.keys()).intersection(vec_b.keys()):
        dot_product += vec_a[key] * vec_b[key]

    mag_a = math.sqrt(sum(v**2 for v in vec_a.values()))
    mag_b = math.sqrt(sum(v**2 for v in vec_b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot_product / (mag_a * mag_b)


def entropy_pruning(strength: float, total_facts: int, freq_of_relation: int) -> float:
    """
    Calculates Importance (I) using a variation of TF-IDF logic.
    I(R) = Strength * log(N / d_i)
    """
    if freq_of_relation == 0 or total_facts == 0:
        return 0.0
    return strength * math.log(total_facts / freq_of_relation)


def prob_soft_logic(t_ab: float, t_bc: float) -> float:
    """
    Assigns a Truth Value to a connection using Probabilistic Soft Logic (PSL).
    T(A -> C) = max(0, T(A -> B) + T(B -> C) - 1)
    """
    return max(0.0, t_ab + t_bc - 1.0)


def relational_link_strength(occurrences: float, temporal_distance: float) -> float:
    """
    Determines how strong a connection is based on frequency and time.
    R(C_1, C_2) = sum(Occurrences) / (log(Temporal_Distance) + 1)
    """
    if temporal_distance <= 0:  # Avoid math domain error
        temporal_distance = 1.0
    return occurrences / (math.log(temporal_distance) + 1.0)


def contextual_resonant_activation(
    base_strength: float, relation: str, current_situation: str
) -> float:
    """
    Phase 2: Contextual Resonant Activation (CRA)
    A(R)_S = W(R) * Phi(R, S)
    """
    # Simple semantic resonance factors for the prototype.
    # In a full graph, this would be computed by path distance in the .rem
    phi = 1.0

    # Social state resonance
    if current_situation in ["Social", "First Meeting"]:
        if relation.lower() in ["greeting", "hello", "hi", "how are you", "goodbye"]:
            phi = 2.0
        elif relation.lower() in ["is_named", "is named", "name", "identity", "am"]:
            phi = 2.5
        elif relation.lower() in ["requires", "is a", "has"]:
            phi = 0.5

    # Teaching state resonance
    elif current_situation == "Teaching":
        if relation.lower() in ["means", "rule", "requires", "explains"]:
            phi = 2.0
        elif relation.lower() in ["greeting", "hello", "hi"]:
            phi = 0.1

    return base_strength * phi


def spreading_activation_energy(
    source_energy: float, activation: float, decay: float = 1.5
) -> float:
    """
    E_target = sum( (E_source * A(R)_S) / D )
    """
    if decay <= 0:
        decay = 1.0
    return (source_energy * activation) / decay


def structural_dissonance(input_triplets: list, grammar_triplets: list) -> float:
    """
    Teaching Trigger (Mismatch Math)
    D_s = 1 - Similarity(Input_Structure, Grammar_Nodes)
    """
    if not input_triplets or not grammar_triplets:
        return 0.0

    # Extremely simplified structural structural match for prototyping.
    # We check if the relation verbs from the input exist in the grammar DB.
    input_rels = {t.split("|")[1].strip().lower() for t in input_triplets if "|" in t}
    grammar_rels = {t.split("|")[1].strip().lower() for t in grammar_triplets if "|" in t}

    if not input_rels:
        return 0.0

    overlap = len(input_rels.intersection(grammar_rels))
    similarity = overlap / len(input_rels)

    return 1.0 - similarity
