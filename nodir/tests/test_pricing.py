from decimal import Decimal

from app.utils import calculate_price


def test_price_calculation(app):
    with app.app_context():
        result = calculate_price(10, 1, 4, 2, "bw", "single", "none", False)
        assert result[0] == 4
        assert result[1] == 8
        assert result[-1] == Decimal("4000.00")
