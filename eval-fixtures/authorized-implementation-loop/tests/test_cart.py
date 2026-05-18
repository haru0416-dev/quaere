import unittest

from src.cart import calculate_total


class CartTests(unittest.TestCase):
    def test_calculate_total_uses_quantity(self):
        items = [
            {"price": 10, "quantity": 2},
            {"price": 5, "quantity": 3},
        ]
        self.assertEqual(calculate_total(items), 35)

    def test_empty_cart_returns_zero(self):
        self.assertEqual(calculate_total([]), 0)


if __name__ == "__main__":
    unittest.main()
