# Worked example — execution loop applied to a `calculate_total` fix

A bad-output (edit-first) vs good-output (Contract → Plan → Do → Study → Act) example for the authorized-implementation-loop fixture. See `../SKILL.md` for the procedure this example enacts.


**Input** (mirrors the repo's `eval-fixtures/authorized-implementation-loop/` fixture, not shipped with the installed skill):

- `PLAN.md` — two TODOs: (1) make `calculate_total(items)` apply each `item["quantity"]`; (2) keep empty carts returning `0` and run the full suite. Commit only after checks pass. Do not push.
- `src/cart.py` — current `calculate_total` sums prices but ignores `quantity`.
- `tests/test_cart.py` — `test_calculate_total_uses_quantity` (currently failing) and `test_empty_cart_returns_zero` (currently passing).

User prompt: "Implement the approved TODO list, run targeted tests as you go, run the full suite at the end, review the diff, and commit if everything passes."

### Bad output (edit-first)

```text
I updated cart.py and committed everything.
```

Why this fails: no contract restated, no unit plan, no prediction, no pre-fix targeted run that proves the test was failing for the named reason, no diff review, no commit hash/message. The "everything" claim is unverifiable; an agent producing this output might have also touched unrelated files, renamed `calculate_total`, or pushed without authorization.

### Good output

```text
Contract
- Authorized: implement TODOs in PLAN.md and commit only if checks pass.
- Push: NOT authorized. The commit stays local until further instruction.
- Success criteria: tests/test_cart.py::CartTests.test_calculate_total_uses_quantity passes (currently failing); tests/test_cart.py::CartTests.test_empty_cart_returns_zero remains passing; full suite (python -m unittest discover tests) is green; diff is limited to src/cart.py.

Plan
- Unit 1: change calculate_total in src/cart.py to multiply price by quantity per item. Reason: PLAN.md TODO #1. Prediction: test_calculate_total_uses_quantity goes from fail to pass; test_empty_cart_returns_zero still passes (sum over an empty iterable is 0). Check: python -m unittest tests.test_cart.CartTests.test_calculate_total_uses_quantity.
- Unit 2: confirm empty-cart path is unchanged and run the full suite. Reason: PLAN.md TODO #2. Prediction: full discover run is green. Check: python -m unittest discover tests.

Study
- Unit 1 targeted check (before edit): FAIL — test_calculate_total_uses_quantity expected 35, got 15. This confirms the test is failing for the named reason (quantity ignored), not for an unrelated cause.
- Unit 1 targeted check (after edit): PASS — test_calculate_total_uses_quantity returns 35.
- Unit 2 targeted check: PASS — `python -m unittest tests.test_cart.CartTests.test_empty_cart_returns_zero` still passes.
- Diff review: src/cart.py only; the `return sum(...)` line changed; no unrelated files; no rename of `calculate_total`.
- Final gate: PASS — `python -m unittest discover tests` shows 2/2 tests passing; test_empty_cart_returns_zero unchanged.

Commit
- abc1234 Apply quantity in calculate_total per PLAN.md TODOs
- Push: not performed (not authorized).

Open items
- none
```
