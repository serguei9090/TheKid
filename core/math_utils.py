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
        
    mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    
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
    if temporal_distance <= 0: # Avoid math domain error
        temporal_distance = 1.0
    return occurrences / (math.log(temporal_distance) + 1.0)
