# The Kid (Ali) - Neuro-Symbolic Architecture & Technology Stack
*Last Updated: Phase 20 (Neural Hard Reset & Prefrontal Cortex)*

## 1. The Technology Stack

"The Kid" is designed to be a lightweight, highly-efficient AGI prototype capable of running locally on a standard PC or GPU. The stack is carefully chosen to minimize dependencies and maximize neuro-symbolic operations.

| Component | Technology | Purpose in Biological Model |
| :--- | :--- | :--- |
| **Brain/Memory (LTM)** | SQLite w/ WAL Journaling | The physical synapses. High-speed, persistent storage for `$Subject | Relation | Object | Context$` quadruplets. Completely eliminates LLM context-window drift. |
| **Teacher/Interpreter (Wernicke's Area)** | Ollama / LLaMA 3 / Gemini | Translates raw PDF/text into structured neuro-symbolic facts. Synthesizes final answers based *strictly* on facts pulled from the SQLite brain. |
| **The Gatekeeper (Prefrontal Cortex)** | SymPy / Regex Validation | The critical filter. Uses the `sympy` mathematical library to independently verify logical/mathematical facts *before* they enter long-term storage. Prunes LLM hallucinations. |
| **Reasoning Engine (Hippocampal routing)** | Python (`KidEngine`) | Executes Contextual Resonant Activation (CRA) and Multi-Step Graph Inference. Calculates associative energy pathways instead of using semantic vector embeddings. |
| **Package Management / Linting** | `uv`, Ruff | Follows global Antigravity standards for extreme speed and Python correctness. |

---

## 2. Phase 20 Enhancements: The Prefrontal Cortex

### The Context Explosion Problem
Prior to Phase 20, the "Teacher" module was allowed to invent arbitrary context labels (e.g., "Context: DIY cat entertainment"), leading to over 200 fragmented neural pathways. This caused the Contextual Resonant Activation (CRA) energy to leak and fail during retrieval. Memory was also polluted with mathematically impossible LLM hallucinations (e.g., `ssss2+2 | equals | 20`).

### The Gatekeeper Solution
We executed a "Neural Hard Reset" (deleting the database) and implemented a Prefrontal Cortex (PFC) module:

1.  **Pillar Normalization:** All new incoming facts are aggressively normalized into 5 core pillars: `Math`, `Language`, `Logic`, `Social`, or `Identity`. Any extraneous context is merged into `General`.
2.  **Structural Validation:** Facts with chaotic formatting (subjects > 100 characters) are rejected before being written to disk.
3.  **SymPy Reality Check:** If the LLM generates a math fact (e.g., `4 + 4 | equals | 10`), the PFC intercepts it. It uses Python's `sympy` library to calculate `4 + 4` natively. It compares the true result (`8`) to the LLM's object (`10`). Seeing they do not match, **the memory is destroyed before the database learns the lie.**

---

## 3. Data Flow and Architecture Diagram

The following diagram illustrates how raw text becomes highly verified neural connections, and how Ali synthesizes responses without hallucinating.

```mermaid
graph TD
    %% Ingestion Flow
    subgraph "External World"
        A[Raw Input: PDFs, Text, Chat]
    end

    subgraph "Sensory Processing (Teacher)"
        B[LLM Parser]
        A -->|Unstructured Text| B
        B -->|Draft Fact: S|R|O|C| C
    end

    subgraph "Prefrontal Cortex (The Gatekeeper)"
        C{Is Context Valid?}
        C -->|No| D[Normalize to Core Pillars]
        C -->|Yes| E
        D --> E{Is Math Logically Sound?}
        E -->|No: SymPy calculates discrepancy| F[(Reject Memory)]
        E -->|Yes: Fact is true| G
    end

    subgraph "Long Term Memory (SQLite Brain)"
        G[(SYNAPSES.REM)]
        G -->|Update Occurrence/Strength| H[Recency & Resonant Weight]
    end

    %% Retrieval Flow
    subgraph "Retrieval & Response"
        I[User Question]
        I --> J[Contextual Resonant Activation]
        J -->|Shallow Search| K{Direct Match Found?}
        K -->|Yes| L[Activate Neural Path]
        K -->|No| M[Pillar C: Multi-Step Graph Walk]
        M --> L
        
        L -->|Verified Quadruplets| N[Synthesize Vocal Cords]
        N --> O[Ali's Output Speech]
    end

    H -.->|Stored Data| J

    %% Styling
    classDef cortex fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef reject fill:#ffcdd2,stroke:#b71c1c,stroke-width:2px;
    classDef ltm fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px;
    
    class C,D,E cortex;
    class F reject;
    class G ltm;
```

## 4. Operational Usage

### Autonomous Deep Learning
To train Ali on new knowledge:
1. Place `.txt`, `.md`, or `.pdf` files inside `library/` (supports recursive sub-directories).
2. Start the main loop.
3. Ali will continuously sweep the library, extracting facts via the LLM, verifying them through the Math/SymPy Gatekeeper, and compiling them into `synapses.rem`.

### Chat Interface
Execute `python chat_terminal.py` to speak with Ali. He will pull from his verified memory and utilize Multi-Step Graph inference to walk relationships (e.g., `Fire -> Wood -> Flammable`), circumventing the standard "black box" limitations of standard LLMs.
