# 01 - The Kid: Core Logic Flow Diagram
**Date:** 2026-02-28

This diagram represents the core Metabolic Switch logic loop for "The Kid".

```mermaid
flowchart TD
    subgraph The_Father[The Father]
        USER((User Context))
        MISSIONS((/missions/ *.json))
        USER --> |Chats| W_PHASE
        MISSIONS --> |Drops task| LOOP
    end

    subgraph The_Kid_Engine["The Kid Engine (Python / SQLite)"]
        LOOP{Metabolic Toggle}
        
        %% GREEDY MODE
        L_PHASE["GREEDY MODE\n(School Phase)"]
        L_CHECK{"Is Library Empty?"}
        
        %% REFINEMENT MODE
        D_PHASE["REFINEMENT MODE\n(Dreaming Phase)"]
        OPT_1[Update Relational Strength]
        OPT_2[Cosine Fusion]
        OPT_3[Entropy Pruning]
        OPT_4[PSL Verification]
        
        %% WORKER PHASE
        W_PHASE["WORKER PHASE\n(Chat Interface)"]
        BRAIN[(synapses.rem\n4GB Relational Map)]
        LOGGER[["trace.log (Background)"]]
        Q_SOLVED{"Found in .rem?"}
    end

    subgraph The_Teacher[The Teacher - Local LLM]
        OLLAMA[Ollama 3.1 8B]
        LLM_EXTRACT["Slave Processor:\nText -> Quadruplets"]
        LLM_VOCAL["Vocal Cords:\nKnowledge -> Natural Chat"]
    end

    %% Flow Definitions
    LOOP --> |Missions Found| L_PHASE
    LOOP --> |No Missions| D_PHASE

    %% School Flow
    L_PHASE --> L_CHECK
    L_CHECK -->|No| EXTRACT_SRC[Read next file\nfrom /library]
    EXTRACT_SRC --> LLM_EXTRACT
    LLM_EXTRACT -->|Returns\n$S | R | O | C$| BRAIN
    L_CHECK -->|Yes| D_PHASE

    %% Dream Flow
    D_PHASE --> OPT_1 --> OPT_2 --> OPT_3 --> OPT_4
    OPT_1 <--> BRAIN
    OPT_2 <--> BRAIN
    OPT_3 <--> BRAIN
    OPT_4 <--> BRAIN

    %% Worker Flow
    W_PHASE --> |1. Searches keywords| BRAIN
    BRAIN -.-> Q_SOLVED
    Q_SOLVED -->|Yes| LLM_VOCAL
    Q_SOLVED -->|No| LLM_ASK[Ask Teacher on the fly]
    LLM_ASK --> OLLAMA
    OLLAMA -->|Save new Quadruplet| BRAIN
    OLLAMA -->|Speak| W_PHASE
    LLM_VOCAL -.-> W_PHASE
    
    %% Logger connections
    L_PHASE -.-> LOGGER
    W_PHASE -.-> LOGGER
    D_PHASE -.-> LOGGER

    %% Styling
    classDef greedy fill:#1c5521,stroke:#4caf50,stroke-width:2px,color:#fff;
    classDef dream fill:#003459,stroke:#00a8e8,stroke-width:2px,color:#fff;
    classDef worker fill:#4a192c,stroke:#e91e63,stroke-width:2px,color:#fff;
    classDef teacher fill:#333333,stroke:#ff9800,stroke-width:2px,color:#fff;
    
    class L_PHASE greedy;
    class D_PHASE dream;
    class W_PHASE worker;
    class The_Teacher,OLLAMA,LLM_EXTRACT,LLM_VOCAL teacher;
```
