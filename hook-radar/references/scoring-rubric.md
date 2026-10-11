# Scoring Rubric: Agent Re-ranking

The `run.py` script generates an initial mechanical candidate list. This rubric guides agent-side evaluation and refinement based on contextual analysis.

## Script Metric Evaluation

| Score | Inputs | Limitations |
|---|---|---|
| **hook** (0-100) | Lexicon matches, numbers, question markers, penalties | Cannot evaluate acoustic delivery, irony, or comedic timing |
| **retention** (0-100) | Most-Replayed curve delta against baseline | Unavailable on low-traffic videos; cannot distinguish between high density and true focal moments |
| **fit** (0-100) | Duration window and relative positioning | Does not evaluate topical alignment |

Composite weightings:
- When heatmap data is present: hook 0.45, retention 0.35, fit 0.20.
- When heatmap data is absent: hook 0.65, retention 0.10, fit 0.25.

## Five-Stage Judgement Workflow

Evaluate top candidates through the following criteria in order:

### 1. Standalone Completeness
Review the candidate text from `candidates.json` alongside preceding phrases in `transcript_packed.md`. If understanding requires prior conversational context, mark the candidate as `context-dependent` and demote or reject it.

### 2. Single-Premise Focus
Ensure each window centers on one core thought. If a candidate spans two separate ideas, propose a trimmed re-cut or split into two distinct segments.

### 3. Hook Positioning
The script scores the opening phrase. If the most compelling line appears 5-10 seconds into the candidate, adjust the clip start timestamp to begin directly on that line.

### 4. Narrative Resolution
Verify that the resolution or punchline occurs inside the selected segment. If the segment cuts off prematurely before the premise concludes, extend the duration or reject the segment.

### 5. Format Parameters
- Clips under 8 seconds lack sufficient narrative depth.
- Standard clips for reward monetization should target 60-85 seconds.
- Segments without tension or contrasting perspectives should be flagged.

## Confidence Ratings

Assign each selected clip a confidence rating:

| Level | Definition |
|---|---|
| **high** | Supported by retention data, strong standalone hook, clear narrative resolution |
| **medium** | Strong premise but lacking retention validation, or requires slight boundary trimming |
| **low** | Derived purely from text heuristics, context-dependent, or relies on unseen physical delivery |

## Rejection Criteria

- Context traps: "as discussed earlier", "in the previous slide", "like we mentioned".
- Clips whose meaning alters when isolated from the original context.
- Segments under 8 seconds that lack a self-contained conclusion.
- Duplicate candidates covering the identical segment across shifted windows.
- Windows composed primarily of non-substantive filler dialogue.

## Required Reporting Fields

1. **`rejected`**: Explicit list of eliminated candidates with reasons.
2. **`caveats`**: Missing heatmap data, sparse audio transcription, or unverified visual cues.
3. **Discrepancy Notes**: Explicit rationale when manual ranking alters algorithmic ordering.

## Quality Standards

Do not represent text-only candidate scoring as audience-validated. Mechanical scores serve as prioritisation filters, not guarantees of reach or view counts. State the specific empirical basis for every selected candidate.
