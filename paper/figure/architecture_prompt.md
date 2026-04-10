# Architecture Diagram Prompt for IntentChecker

## Goal
Draw a layered system architecture diagram for IntentChecker, suitable for an academic paper (clean, black/white with minimal shading, high readability). The diagram should be horizontally oriented, with layers stacked vertically from bottom to top (input at bottom, output at top), or left-to-right if that fits better.

## Overall Style
- Clean, minimalist academic style (no 3D effects, no gradients, no icons)
- Black outlines, light gray/white fills. Use dotted or dashed borders to distinguish "reused from SolQDebug" modules vs "new in IntentChecker" modules
- Font: sans-serif, consistent size
- Arrows show data flow between layers/modules
- Every module and arrow should be labeled

## Layer Structure (bottom to top)

### Layer 0: Input (bottom)
Three input types entering the system from below:
1. **Solidity Source** (Statement) — incrementally provided as developer writes code
2. **Debug Annotations** — @StateVar, @LocalVar, @GlobalVar, @IReturn (all inject developer-specified ranges at unknown-value program points)
3. **Intent Annotations** — @During, @Post (declare intended numeric relationships)

Also show as a side input:
4. **Dependency CFGs** (.pkl) — pre-analyzed library/contract CFGs, cached

### Layer 1: Parsing Module [label: "from SolQDebug"]
- ANTLR-based parser for Solidity fragments + annotation comment syntax
- Solidity compiler for semantic validation
- Output: parsed AST fragments + parsed annotation objects
- Arrow down from Layer 0 inputs
- Arrow up to Layer 2

### Layer 2: Analysis Module
This layer has two visual sub-regions:

**Sub-region A [label: "from SolQDebug"]:**
- Incremental CFG Builder (line-to-node index, partial re-parse)
- Interval-Domain Abstract Interpreter (fixpoint iteration, widening)
- Snapshot Manager (saves/restores analysis state for debug annotation injection)

**Sub-region B [label: "New in IntentChecker"]:**
- Multi-Contract Scope Extensions:
  - C3 Inheritance Resolution
  - Library / Using-Directive Handler (delegatecall semantics)
  - IReturn Registry + Resolver (interface call value injection)
  - Arithmetic Yul Visitor (subset of inline assembly)

The Dependency CFGs (.pkl) side-input arrow enters Sub-region B (loaded by the multi-contract extensions).

- Arrow up: computed variable intervals (per program point) flow to Layer 3

### Layer 3: Validation Engine [label: "New in IntentChecker" — core contribution]
This is the core new contribution. Show it prominently (slightly larger or with a distinct border).
- Receives: computed variable intervals from Analysis Module + parsed intent annotations from Parsing Module
- Internal steps (can show as sub-boxes or just label):
  1. Clause-to-Interval Mapping (maps each @During/@Post clause to interval comparison inputs L, R)
  2. Interval Comparison Algorithm (partitions into Satisfied/Warning/Violated regions)
  3. Risk Score Computation (0-10 scale based on region proportions)

### Layer 4: Output (top)
Three output items:
1. **Validation Result** — Satisfied / Warning / Violated
2. **Risk Score** — 0.0 to 10.0
3. **Violated Region** — specific sub-intervals where intent may be violated

## Key Arrows / Data Flow
- Solidity Source → Parsing Module → Analysis Module (CFG construction + interpretation)
- Debug Annotations → Parsing Module → Analysis Module (value injection at unknown points)
- Intent Annotations → Parsing Module → Validation Engine (annotation clauses)
- Dependency CFGs → Analysis Module (pre-analyzed libraries/contracts)
- Analysis Module → Validation Engine (computed variable intervals per program point, including before_env, after_env, entry_env, exit_env, assign_env)
- Validation Engine → Output (result + risk score + violated region)

## Visual Distinction
- Modules originating from SolQDebug: dashed border or light gray fill, labeled "(SolQDebug)"
- Modules new in IntentChecker: solid border or slightly darker fill, labeled "(New)"
- The Validation Engine layer should be visually emphasized as the core contribution (e.g., thicker border, or a subtle accent)

## Size
- Target size: single-column width (~8.5cm) or full page width (~17cm), whichever the requester prefers
- Should be legible when printed at the target size

## Notes
- Do NOT include any specific code syntax in the diagram
- Do NOT include algorithm pseudocode — just module names and data flow
- The layered structure should convey: "SolQDebug provides the analysis foundation (Layers 1-2A), IntentChecker adds multi-contract extensions (Layer 2B) and the validation engine (Layer 3)"
