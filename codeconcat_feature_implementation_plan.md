# Codeconcat: Advanced Analysis Feature Implementation Plan

This document outlines the consensus-driven implementation plan for adding advanced static analysis features to `codeconcat`. The plan is the result of a multi-model "Zen" reflection designed to produce a practical, high-value, and phased roadmap.

## Guiding Philosophy

The core philosophy is to **enhance, not replace**. The features will be implemented as lightweight, inline annotations that enrich the existing concatenated output. This maintains `codeconcat`'s core value proposition as a simple, single-file context generator.

Key principles are:
1.  **Annotation-Based:** All new information will be injected as language-specific comments directly into the code.
2.  **Configuration-Driven:** Features will be opt-in via a new `--analyze` flag and highly configurable to manage noise and performance.
3.  **Performance Aware:** The fast, core concatenation functionality must not be degraded. Analysis, especially project-wide analysis, is a slower path and must be treated as such.

---

## Phase 1: Quick Wins & Foundation (MVP)

**Goal:** Deliver immediate, high-value insights with low implementation complexity.

### Feature 1: Inline Security Findings

*   **Implementation:** Leverage the existing `semgrep_validator.py`. For each issue found by Semgrep, inject a formatted, machine-readable comment directly above the offending line of code.
*   **Annotation Format:** `# SEMGREP-WARN [rule-id]: Human-readable message.`
*   **CLI Flag:** `--analyze=security`
*   **Justification:** This is the highest value-to-effort feature. It makes critical security issues unmissable by placing them directly in the developer's context.

### Feature 2: Code Quality Metrics

*   **Implementation:** For each function, calculate its Cyclomatic Complexity and line count. Inject this information as a comment above the function definition.
*   **Annotation Format:** `# METRICS: Complexity=8, Lines=45`
*   **CLI Flag:** `--analyze=metrics`
*   **Configuration:** Add a threshold flag (e.g., `--metrics-min-complexity=10`) to only show annotations for functions exceeding a certain complexity, reducing noise.
*   **Justification:** Provides an instant, at-a-glance heuristic for identifying complex code that may need refactoring.

### Foundational Work

*   **Annotation Engine:** Develop the core logic in `annotator.py` to handle injecting language-specific comments (e.g., `#`, `//`, `/* ... */`) without breaking the code. The engine must insert annotations from the bottom of the file upwards to maintain correct line offsets.
*   **Configuration:** Implement the `--analyze` flag and the associated configuration to control which analyses run.

---

## Phase 2: Project-Wide Analysis Engine

**Goal:** Build the core infrastructure for project-wide analysis, starting with a single language to prove feasibility.

### Feature 3: Dependency Analysis (File-Level)

*   **Implementation:** This requires a significant architectural shift. `codeconcat` must first parse **all** files in the project to build a global import index. Once the index is built, inject a header at the top of each file's output.
*   **Annotation Format (at top of file block):**
    ```
    # --- File: src/api.py ---
    # IMPORTS: flask, ./db.py
    # IMPORTED_BY: app.py, tests/test_api.py
    ```
*   **CLI Flag:** `--analyze=dependencies`
*   **Justification:** Provides crucial context about a file's role within the broader architecture.

### Foundational Work

*   **Analysis Pipeline:** Refactor the core logic to support a multi-pass approach: `1. Index All Files -> 2. Analyze -> 3. Annotate & Concatenate`.
*   **Language Scope:** Implement this feature for **Python only** first. This isolates the complexity of handling different module systems and proves the architecture before expanding.
*   **Performance:** For this phase, focus on correctness. Performance optimizations like caching will be addressed in Phase 3.

---

## Phase 3: Advanced Analysis & Scalability

**Goal:** Build upon the project-wide analysis engine to deliver more advanced insights and ensure performance on large codebases.

### Feature 4: Call Graph Analysis (Function-Level)

*   **Implementation:** Using the global index from Phase 2, resolve function calls within each function body. Annotate each function with its immediate callers and callees.
*   **Annotation Format:** `# CALLS: get_user_from_db, format_response`
*   **CLI Flag:** `--analyze=call-graph`
*   **Configuration:** Add a verbosity setting (e.g., `--analysis-level=light/full`) or thresholds to limit the number of callers/callees listed to prevent overwhelming annotations on central utility functions.
*   **Justification:** This is the deepest level of context, showing the direct execution flow of the code.

### Feature 5: Dead Code Analysis

*   **Implementation:** Using the completed call graph, identify declared internal functions (e.g., prefixed with `_`) that are never called.
*   **Annotation Format:** `# CODECONCAT-WARN: Potentially unused function. No calls were found in this context.`
*   **CLI Flag:** `--analyze=dead-code`
*   **Justification:** Provides actionable hints for code cleanup and maintenance, with a conservative scope to minimize false positives.

### Scalability & Performance

*   **Caching:** Implement a caching mechanism. Store the analysis index (ASTs, symbol tables) and only re-process files that have changed since the last run. This is critical for making the `--analyze` flag usable on large projects.
*   **Parallelization:** Investigate parallelizing the initial file parsing and indexing step to improve performance.

---

## Critical Risks & Mitigation

1.  **Performance Degradation:**
    *   **Risk:** Project-wide analysis could make `codeconcat` too slow.
    *   **Mitigation:** The `--analyze` flag is a non-negotiable opt-in. The core concatenation logic must remain fast. Caching is the primary long-term solution.

2.  **Analysis Accuracy:**
    *   **Risk:** Call graphs and dead code analysis can be inaccurate in dynamic languages.
    *   **Mitigation:** Clearly document that these are **heuristic-based** analyses. Start with a single, well-understood language (Python). Consider allowing integration with external, language-specific tools for users who need higher accuracy.

3.  **Annotation Noise:**
    *   **Risk:** Too many annotations can make the output unreadable.
    *   **Mitigation:** Implement robust configuration from day one: granular flags for each analysis type, complexity/verbosity thresholds, and an inline suppression comment (e.g., `# codeconcat:ignore-dead-code`).
