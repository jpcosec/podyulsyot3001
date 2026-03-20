# Planning Dependency Tree Template

Use this template for new plans.

## 1. Context

- current state
- why this change exists
- relevant constraints

## 2. Objective

- desired end state
- what will change
- what must remain unchanged

## 3. Dependency tree of work

```text
Root objective
├── Workstream A
│   ├── Step A1
│   └── Step A2
└── Workstream B
    ├── Step B1
    └── Step B2
```

For each node in the tree, note blockers and dependents.

## 4. Code impact tree

```text
Change area
├── module/file
│   ├── downstream consumers
│   └── tests to rerun
└── module/file
```

Use `src/DEPENDENCY_GRAPH.md` when useful and add/update local dependency notes if the area is large.

## 5. Libraries / tools involved

- runtime deps
- test tools
- browser/dev tools

## 6. Implementation approach

- pseudocode
- architecture notes
- links to examples or code to imitate

## 7. Step contract

For each step include:

- objective
- files/modules touched
- what not to do
- how to test
- expected docs update
- expected changelog update
- commit message shape

## 8. Done definition

- code done
- tests passing
- docs updated
- changelog updated
- verification evidence captured where appropriate

## 9. Commit slicing

- commit 1:
- commit 2:
- commit 3:

Each commit should be reviewable on its own.
