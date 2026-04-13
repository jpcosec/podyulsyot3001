# Workflow Map

This diagram shows the execution workflow across roles, context files, and lifecycle tasks.

```mermaid
flowchart TD
    O[Orchestrator / Supervisor]
    CC[Context Compiler]
    EX[Executor]

    ST[`STANDARDS.md`]
    IDX[`plan_docs/issues/Index.md`]
    SUP[`plan_docs/supervisor-instructions.md`]
    EXI[`plan_docs/executor-instructions.md`]
    CCI[`plan_docs/context_compiler-instructions.md`]
    CPR[`plan_docs/context/README.md`]
    CPA[`plan_docs/context-pill-audit.md`]
    ISSUE[`plan_docs/issues/{issue}.md`]
    PILLS[`plan_docs/context/*.md`]
    CHANGE[`changelog.md`]
    REPORT[`plan_docs/reports/*`]
    CODE[`src/* + tests/*`]
    GIT[(git commit)]

    subgraph Init[Initialization Ritual]
        I1[Atomize work]
        I2[Merge redundant issues]
        I3[Delete legacy issues]
        I4[Resolve contradictions]
        I5[Inject context pills]
        I6[Dispatch one context compiler per issue]
        I7[Run pill audit]
        I8[Update Index and dependency map]
    end

    subgraph Compile[Context Compiler Pass]
        C1[Review issue file]
        C2[Review linked pills]
        C3[Check staleness against context README]
        C4[Add / recreate missing pills]
        C5[Clarify dependencies and references]
        C6[Return issue package ready for execution]
    end

    subgraph Execute[Executor Flow]
        E1[Read issue and context]
        E2{Clarity gate passes?}
        E3[Implement fix]
        E4[Update or delete invalid tests]
        E5[Add and run relevant tests]
        E6[Verify standards compliance]
        E7[Update changelog]
        E8[Create exactly one issue commit]
        E9[Report commit id in Index entry]
        E10[Leave Index bookkeeping dirty if needed]
        E11[Leave issue file in place for review]
    end

    subgraph Review[Supervisor Review]
        R1[Review exact closing commit]
        R2{Accepted?}
        R3[Keep commit and tracking artifacts]
        R4[Revert exact commit]
        R5[Update issue file with failures and extra context]
        R6[Dispatch new executor]
    end

    subgraph Phase[Phase-Closing Ritual]
        P1[Freeze phase boundary]
        P2[Review every issue entry]
        P3[Inspect every closing commit]
        P4[Run architecture and validation gates]
        P5[Update reports and phase status]
        P6[Finalize Index bookkeeping if still dirty]
        P7[Delete resolved issue files]
        P8[Remove resolved Index entries]
        P9[Mark phase completed]
    end

    O --> ST
    O --> IDX
    O --> SUP
    O --> CPA
    O --> ISSUE
    O --> PILLS

    ST --> Init
    IDX --> Init
    SUP --> Init
    CPA --> I7
    ISSUE --> I1
    PILLS --> I5

    O --> I1 --> I2 --> I3 --> I4 --> I5 --> I6 --> I7 --> I8

    I6 --> CC
    CC --> CCI
    CC --> CPR
    CC --> ISSUE
    CC --> PILLS
    CCI --> Compile
    CPR --> C3
    CC --> C1 --> C2 --> C3 --> C4 --> C5 --> C6
    C6 --> O

    O --> EX
    EX --> EXI
    EX --> ST
    EX --> ISSUE
    EX --> PILLS
    EXI --> Execute
    EX --> E1 --> E2
    E2 -- No --> CC
    E2 -- Yes --> E3 --> CODE
    E3 --> E4 --> E5 --> E6 --> E7 --> CHANGE --> E8 --> GIT --> E9 --> IDX --> E10 --> E11

    O --> R1
    GIT --> R1
    IDX --> R1
    ISSUE --> R1
    SUP --> Review
    R1 --> R2
    R2 -- Yes --> R3
    R2 -- No --> R4 --> GIT
    R4 --> R5 --> ISSUE --> R6 --> EX

    O --> P1 --> P2 --> P3 --> P4 --> P5 --> REPORT --> P6 --> IDX --> P7 --> ISSUE --> P8 --> IDX --> P9
    SUP --> Phase
    IDX --> P2
    GIT --> P3
```
