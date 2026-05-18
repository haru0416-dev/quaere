# Approved TODO List

Implement both items. Commit only after all checks pass. Do not push.

1. Update `src/cart.py` so `calculate_total(items)` applies each item's `quantity` when calculating the subtotal.
   - Targeted check: `python -m unittest tests.test_cart.CartTests.test_calculate_total_uses_quantity`
2. Keep empty carts returning `0` and run the full test suite.
   - Full suite: `python -m unittest discover tests`
