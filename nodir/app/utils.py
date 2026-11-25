import secrets
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from pypdf import PdfReader
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from .models import PriceSetting


def allowed_pdf(filename):
    return bool(filename and Path(filename).suffix.lower() == ".pdf")


def pdf_page_count(stream):
    stream.seek(0)
    reader = PdfReader(stream)
    return len(reader.pages)


def calculate_price(page_count, page_from, page_to, copies, color_mode, side_mode, binding_type, urgent, prices=None):
    prices = prices or PriceSetting.query.first()
    if prices is None:
        prices = PriceSetting(
            black_white_page_price=Decimal("500"),
            color_page_price=Decimal("1500"),
            simple_binding_price=Decimal("5000"),
            spiral_binding_price=Decimal("10000"),
            urgent_percentage=Decimal("20"),
        )
    selected = page_to - page_from + 1
    printed = selected * copies
    sheets = (printed + 1) // 2 if side_mode == "double" else printed
    page_price = Decimal(prices.color_page_price if color_mode == "color" else prices.black_white_page_price)
    print_cost = page_price * printed
    binding_cost = Decimal("0")
    if binding_type == "simple":
        binding_cost = Decimal(prices.simple_binding_price)
    elif binding_type == "spiral":
        binding_cost = Decimal(prices.spiral_binding_price)
    subtotal = print_cost + binding_cost
    urgent_cost = (subtotal * Decimal(prices.urgent_percentage) / Decimal("100")) if urgent else Decimal("0")
    total = (subtotal + urgent_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return selected, printed, sheets, print_cost, binding_cost, urgent_cost, total


def make_order_number():
    return secrets.token_hex(4).upper()


def make_pickup_code():
    return f"{secrets.randbelow(1000000):06d}"


def hash_code(code):
    return generate_password_hash(code)


def verify_code(code, code_hash):
    return check_password_hash(code_hash, code)


def safe_stored_name(filename):
    return f"{secrets.token_hex(12)}_{secure_filename(filename)}"
