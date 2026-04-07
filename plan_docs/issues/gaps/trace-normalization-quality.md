# Trace Normalization Quality

## Explanation

Promotion exists, but the normalizer still infers steps and states with placeholder heuristics. That keeps promoted maps usable only for simple traces and makes canonical output noisy.

## Reference in src

- `src/automation/ariadne/normalizer.py`
- `src/automation/ariadne/trace_models.py`

## What to fix

Improve state inference, observation synthesis, and action grouping so promoted maps look like stable Ariadne maps instead of thin drafts.

## How to do it

Infer states from screenshots, selectors, and navigation boundaries; generate `observe.required_elements` from repeated evidence; and add tests that compare normalized output against expected canonical maps.

## Does it depend on another issue?

No.
