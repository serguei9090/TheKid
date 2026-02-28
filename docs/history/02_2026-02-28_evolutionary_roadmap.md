# 02 - Evolutionary Roadmap & Philosophy
**Date:** 2026-02-28

## 1. Project Philosophy
"The Kid" is a Neuro-Symbolic Specialist designed to mimic biological learning. Unlike traditional LLMs that are static and "black box," The Kid is dynamic, persistent, and relational. It runs on consumer hardware (NVIDIA RTX 3060 12GB VRAM / 32GB RAM) using a 4GB `.rem` (Relational Entropy Mapping) file as its primary synaptic map.

## 2. The "Metabolic Switch" (Core Learning Loop)
The Kid operates in two primary states, managed by a metabolic toggle:

### A. GREEDY MODE (The School Phase)
* **Behavior:** High-speed ingestion. The Kid prioritizes reading every unread file in the `/library` folder.
* **Mechanism:** Uses parallel worker pools to call the Teacher (Ollama 3.1 8B) to extract triplets (`$Subject | Relation | Object$`) at 50+ t/s.
* **Completion Logic:** Once the library is empty, the Kid does not sleep; it pivots to "Internal Growth."

### B. REFINEMENT MODE (The Dreaming Phase)
* **Behavior:** Internal digestion and logic hardening.
* **Mechanism:**
  * **Self-Generated Missions:** The Kid identifies "Lone Nodes" (concepts with few links) and generates missions to fill gaps.
  * **Consolidation:** Uses Cosine Fusion to merge synonyms and Entropy Pruning to delete useless data.
  * **Verification:** Uses Probabilistic Soft Logic (PSL) to verify "hallucinated" links by asking the Teacher for confirmation.

## 3. The Father-Student Relationship
The interaction is split into two specialized roles:

### The Father (User):
* **Mission Control:** Drops JSON files into `/missions` to override current focus.
* **The Guardrail:** (Future) Provides a list of behaviors or logic types to avoid.
* **Feedback:** Reviews "Homework" resumes to confirm if the Kid's learned logic is "Right or Wrong."

### The Teacher (Ollama):
* A slave processor used for text-to-triplet translation and natural language vocalization.

## 4. Linguistic Specialization (Phase 1)
To become "Superhuman," the Kid first undergoes a Linguistic Skeleton phase:
* **Dictionary Ingestion:** Reading a full English dictionary to map all available "Nodes."
* **Grammar Logic:** Processing a specialized `language_grammar.md` to learn how nodes relate (e.g., `[Subject] -> [requires] -> [Verb]`).
* **Traceable Talk:** The Kid answers "Hi" or "Who are you?" by querying the `.rem` file directly. If no link exists, it proactively asks the Teacher and saves the result for next time.

## 5. Mathematical Safeguards
* **Deduplication:** File hashes are stored in SQLite to prevent the Kid from reading the same book twice.
* **Deterministic Inference:** The Kid only uses the LLM to speak; the data must come from the `.rem` file path (e.g., `Door -> Oak -> Wood -> Flammable`).
* **Trace Debugging:** Every thought process is visible in the terminal to allow for immediate theory testing and debugging.

## 6. The 4GB Goal
By using Binary Relation Mapping and ID-based Hashing, the goal is to store over **30 million high-quality connections** in a single 4GB file. This allows for an Einstein-level specialist that is portable and lightning-fast on a standard PC.
