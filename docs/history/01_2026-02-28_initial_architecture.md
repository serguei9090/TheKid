# 01 - Initial Architecture & The New Math
**Date:** 2026-02-28

## Overview (The Idea & Core Theory)
Project "The Kid" is a Neuro-Symbolic Specialist designed to operate on the "Pentium 4 Brain" theory. Current AI is inefficient because it relies on massive associative matrix multiplication. The Kid solves this by using **Relational Mapping**. Knowledge is stored not as probability weights, but as explicit Triplets (`$Subject | Relation | Object$`) managed within an efficient 4GB SQLite database (`synapses.rem`). 

Because the math relies on Hyperdimensional Vectors and Graph Traversal, The Kid requires significantly less overhead and can run at "superhuman" capability on an NVIDIA RTX 3060 with 12GB VRAM and 32GB RAM, drawing roughly 20 watts sequentially.

We utilize a **Teacher-Student** dynamic:
* **The Teacher:** A localized LLM (Ollama) used exclusively as sensory organs (to interpret unstructured text into triplets) and vocal cords (to formulate natural responses).
* **The Student (The Kid):** The Python architecture that controls the core knowledge logic, stores memories, and asks questions. 

In this first stage, we built the `.rem` database, parallel file chunk ingestion, the LLM interface (Teacher), and established the Operational Loop: Learning Phase (reading text), Worker Phase (chatting), and Dream Phase (optimization). We also implemented **Proactive Learning** where The Kid will ask the Teacher on the fly if it encounters a concept it doesn't know, dynamically translating the Teacher's answer into new triplets to save permanently.

## Mathematical Framework (The New Math)
During the "Dream Phase" cycle, The Kid optimizes its brain using four core formulas to prevent hallucinations and optimize out its 4GB memory limit:

### A. Cosine Fusion (The Synonym Solver)
Merges nodes (e.g., "Motor" and "Engine") by comparing their connection patterns using Cosine Similarity ($\cos \theta$). If similarities exceed an 85% threshold, they are identified as synonyms and consolidated.
$$\text{Similarity}(A, B) = \frac{\sum (R_{A} \cdot R_{B})}{\sqrt{\sum R_{A}^2} \cdot \sqrt{\sum R_{B}^2}}$$

### B. Entropy Pruning (The 4GB Optimizer)
Deletes "noisy" or "obvious" links to keep the memory dense with high-value knowledge. It uses a variation of TF-IDF logic. Low-importance links are pruned permanently.
$$I(R) = \text{Strength} \times \log\left(\frac{N}{d_i}\right)$$

### C. Probabilistic Soft Logic - PSL (The Truth Verifier)
Examines logical associations transitively, assigning a "Truth Value" to logical jumps (e.g. $A \rightarrow B$, $B \rightarrow C$, inferring $A \rightarrow C$). If the calculated likelihood drops below 0.5, the connection is flagged as a hallucinated "Mistake" and pruned.
$$T(A \rightarrow C) = \max(0, T(A \rightarrow B) + T(B \rightarrow C) - 1)$$

### D. Relational Link Strength (The Learning Rule)
Determines how strong a connection is continuously based on how frequently it occurs over rolling time periods.
$$R(C_1, C_2) = \frac{\sum (Occurrences)}{\log(Temporal\_Distance) + 1}$$
