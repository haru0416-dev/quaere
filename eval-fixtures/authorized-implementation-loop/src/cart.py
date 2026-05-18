def calculate_total(items):
    """Return the total price for cart items."""
    return sum(item["price"] for item in items)
