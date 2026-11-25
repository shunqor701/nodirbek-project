from datetime import datetime
from decimal import Decimal, InvalidOperation
import os

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_login import current_user, login_user, logout_user
from flask_wtf.csrf import generate_csrf
from email_validator import EmailNotValidError, validate_email
from pypdf.errors import PdfReadError

from .decorators import role_required
from .extensions import db
from .models import (
    Order,
    OrderStatusHistory,
    Payment,
    PriceSetting,
    PrintParameter,
    UploadedFile,
    User,
)
from .utils import (
    allowed_pdf,
    calculate_price,
    hash_code,
    make_order_number,
    make_pickup_code,
    pdf_page_count,
    safe_stored_name,
    verify_code,
)

api = Blueprint("api", __name__, url_prefix="/api")


def _json_body():
    values = request.get_json(silent=True)
    return values if isinstance(values, dict) else {}


def _serialize_user(user):
    return {
        "id": user.id,
        "fullName": user.full_name,
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }


def _serialize_order(order):
    parameters = order.print_parameter
    uploaded_file = order.uploaded_file
    return {
        "id": order.id,
        "number": order.order_number,
        "status": order.status,
        "totalPrice": str(order.total_price),
        "urgent": order.is_urgent,
        "createdAt": order.created_at.isoformat(),
        "student": {
            "id": order.student.id,
            "fullName": order.student.full_name,
            "username": order.student.username,
        },
        "file": (
            {
                "name": uploaded_file.original_filename,
                "pages": uploaded_file.page_count,
                "deleted": uploaded_file.file_deleted,
            }
            if uploaded_file
            else None
        ),
        "print": (
            {
                "pageFrom": parameters.page_from,
                "pageTo": parameters.page_to,
                "copies": parameters.copies,
                "colorMode": parameters.color_mode,
                "sideMode": parameters.side_mode,
                "bindingType": parameters.binding_type,
                "printedPages": parameters.total_printed_pages,
                "sheets": parameters.calculated_sheet_count,
            }
            if parameters
            else None
        ),
    }


def _serialize_prices(prices):
    return {
        "blackWhitePagePrice": str(prices.black_white_page_price),
        "colorPagePrice": str(prices.color_page_price),
        "simpleBindingPrice": str(prices.simple_binding_price),
        "spiralBindingPrice": str(prices.spiral_binding_price),
        "urgentPercentage": str(prices.urgent_percentage),
        "maxFileSizeMb": prices.max_file_size_mb,
    }


def _get_or_create_prices():
    prices = PriceSetting.query.first()
    if prices is None:
        prices = PriceSetting()
        db.session.add(prices)
        db.session.flush()
    return prices


@api.get("/session")
def session_info():
    user = _serialize_user(current_user) if current_user.is_authenticated else None
    response = jsonify({"user": user, "csrfToken": generate_csrf()})
    response.headers["Cache-Control"] = "no-store"
    return response


@api.post("/auth/register")
def register():
    values = _json_body()
    full_name = str(values.get("fullName", "")).strip()
    username = str(values.get("username", "")).strip()
    email = str(values.get("email", "")).strip()
    password = str(values.get("password", ""))
    confirmation = str(values.get("confirm", ""))

    if len(full_name) < 3 or len(full_name) > 120:
        return jsonify(error="F.I.Sh. 3–120 ta belgidan iborat bo‘lishi kerak."), 400
    if len(username) < 3 or len(username) > 64:
        return jsonify(error="Login 3–64 ta belgidan iborat bo‘lishi kerak."), 400
    if len(email) > 120:
        return jsonify(error="Email manzilini tekshiring."), 400
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return jsonify(error="Email manzilini tekshiring."), 400
    if len(password) < 8:
        return jsonify(error="Parol kamida 8 ta belgidan iborat bo‘lishi kerak."), 400
    if password != confirmation:
        return jsonify(error="Parol tasdiqlanishi bilan mos kelmadi."), 400
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify(error="Bu login yoki email allaqachon ishlatilgan."), 409

    user = User(full_name=full_name, username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(user=_serialize_user(user)), 201


@api.post("/auth/login")
def login():
    values = _json_body()
    username = str(values.get("username", "")).strip()
    password = str(values.get("password", ""))
    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()
    if not user or not user.check_password(password):
        return jsonify(error="Login yoki parol noto‘g‘ri."), 401
    login_user(user)
    return jsonify(user=_serialize_user(user))


@api.post("/auth/logout")
def logout():
    logout_user()
    return jsonify(message="Tizimdan chiqildi.")


@api.get("/student/orders")
@role_required("student")
def student_orders():
    orders = (
        Order.query.filter_by(student_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return jsonify(orders=[_serialize_order(order) for order in orders])


@api.get("/student/orders/<int:order_id>")
@role_required("student")
def student_order(order_id):
    order = Order.query.filter_by(
        id=order_id, student_id=current_user.id
    ).first_or_404()
    return jsonify(order=_serialize_order(order))


@api.post("/student/orders")
@role_required("student")
def create_order():
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return jsonify(error="PDF faylni tanlang."), 400
    if not allowed_pdf(upload.filename):
        return jsonify(error="Faqat PDF fayl yuklash mumkin."), 400

    try:
        page_from = int(request.form.get("pageFrom", ""))
        page_to = int(request.form.get("pageTo", ""))
        copies = int(request.form.get("copies", ""))
    except ValueError:
        return jsonify(error="Betlar va nusxalar sonini to‘g‘ri kiriting."), 400

    color_mode = request.form.get("colorMode", "bw")
    side_mode = request.form.get("sideMode", "single")
    binding_type = request.form.get("bindingType", "none")
    urgent = request.form.get("urgent", "").lower() in {"1", "true", "on", "yes"}
    if page_from < 1 or page_to < page_from or copies < 1 or copies > 100:
        return jsonify(error="Betlar oralig‘i yoki nusxalar soni noto‘g‘ri."), 400
    if color_mode not in {"bw", "color"}:
        return jsonify(error="Chop rangini tanlang."), 400
    if side_mode not in {"single", "double"}:
        return jsonify(error="Chop tomonini tanlang."), 400
    if binding_type not in {"none", "simple", "spiral"}:
        return jsonify(error="Muqova turini tanlang."), 400

    upload.stream.seek(0)
    try:
        pages = pdf_page_count(upload)
    except (PdfReadError, ValueError, OSError):
        return jsonify(error="PDF faylni o‘qib bo‘lmadi. Boshqa faylni tanlang."), 400
    if page_to > pages:
        return jsonify(error=f"PDF faylda faqat {pages} ta bet bor."), 400
    upload.stream.seek(0)
    if upload.stream.read(5) != b"%PDF-":
        return jsonify(error="Yuklangan fayl yaroqli PDF emas."), 400
    upload.stream.seek(0)

    prices = PriceSetting.query.first()
    values = calculate_price(
        pages,
        page_from,
        page_to,
        copies,
        color_mode,
        side_mode,
        binding_type,
        urgent,
        prices,
    )
    pickup_code = make_pickup_code()
    order = Order(
        order_number=make_order_number(),
        student_id=current_user.id,
        pickup_code_hash=hash_code(pickup_code),
        total_price=values[-1],
        is_urgent=urgent,
    )
    db.session.add(order)
    db.session.flush()

    stored_name = safe_stored_name(upload.filename)
    stored_path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)
    upload.save(stored_path)
    db.session.add(
        UploadedFile(
            order_id=order.id,
            original_filename=upload.filename,
            stored_filename=stored_name,
            relative_path=stored_name,
            file_size=os.path.getsize(stored_path),
            page_count=pages,
        )
    )
    db.session.add(
        PrintParameter(
            order_id=order.id,
            page_from=page_from,
            page_to=page_to,
            copies=copies,
            color_mode=color_mode,
            side_mode=side_mode,
            binding_type=binding_type,
            selected_page_count=values[0],
            total_printed_pages=values[1],
            calculated_sheet_count=values[2],
            print_cost=values[3],
            binding_cost=values[4],
            urgent_cost=values[5],
        )
    )
    db.session.add(Payment(order_id=order.id, amount=values[-1]))
    db.session.add(
        OrderStatusHistory(
            order_id=order.id,
            new_status="new",
            changed_by=current_user.id,
            note="Buyurtma yaratildi",
        )
    )
    db.session.commit()
    return jsonify(
        order=_serialize_order(order),
        totalPrice=str(values[-1]),
        pickupCode=pickup_code,
    ), 201


@api.post("/student/orders/<int:order_id>/cancel")
@role_required("student")
def cancel_order(order_id):
    order = Order.query.filter_by(
        id=order_id, student_id=current_user.id
    ).first_or_404()
    if order.status not in {"new", "queued"}:
        return jsonify(error="Bu holatda buyurtmani bekor qilib bo‘lmaydi."), 409

    old_status = order.status
    order.status = "cancelled"
    order.cancelled_at = datetime.utcnow()
    db.session.add(
        OrderStatusHistory(
            order_id=order.id,
            old_status=old_status,
            new_status="cancelled",
            changed_by=current_user.id,
        )
    )
    db.session.commit()
    return jsonify(order=_serialize_order(order))


@api.get("/operator/orders")
@role_required("operator")
def operator_orders():
    orders = (
        Order.query.filter(Order.status.in_(("new", "queued", "printing", "ready")))
        .order_by(Order.is_urgent.desc(), Order.created_at.asc())
        .all()
    )
    return jsonify(orders=[_serialize_order(order) for order in orders])


@api.patch("/operator/orders/<int:order_id>/status")
@role_required("operator")
def update_order_status(order_id):
    order = db.session.get(Order, order_id)
    status = _json_body().get("status")
    if not order:
        return jsonify(error="Buyurtma topilmadi."), 404
    allowed = {"new": "printing", "queued": "printing", "printing": "ready"}
    if allowed.get(order.status) != status:
        return jsonify(error="Buyurtma holatini bu tarzda o‘zgartirib bo‘lmaydi."), 409

    old_status = order.status
    order.status = status
    if status == "printing":
        order.printing_started_at = datetime.utcnow()
    else:
        order.ready_at = datetime.utcnow()
    db.session.add(
        OrderStatusHistory(
            order_id=order.id,
            old_status=old_status,
            new_status=status,
            changed_by=current_user.id,
        )
    )
    db.session.commit()
    return jsonify(order=_serialize_order(order))


@api.post("/operator/pickup")
@role_required("operator")
def complete_pickup():
    code = str(_json_body().get("code", "")).strip()
    order = next(
        (
            item
            for item in Order.query.filter_by(
                status="ready", pickup_code_used=False
            ).all()
            if verify_code(code, item.pickup_code_hash)
        ),
        None,
    )
    if order is None:
        return jsonify(error="Olish kodi noto‘g‘ri yoki buyurtma tayyor emas."), 404

    order.status = "completed"
    order.pickup_code_used = True
    order.completed_at = datetime.utcnow()
    db.session.add(
        OrderStatusHistory(
            order_id=order.id,
            old_status="ready",
            new_status="completed",
            changed_by=current_user.id,
        )
    )
    db.session.commit()
    return jsonify(order=_serialize_order(order))


@api.get("/operator/orders/<int:order_id>/file")
@role_required("operator")
def download_order_file(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify(error="Buyurtma topilmadi."), 404
    if not order.uploaded_file or order.uploaded_file.file_deleted:
        return jsonify(error="Buyurtmaning PDF fayli mavjud emas."), 404
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        order.uploaded_file.stored_filename,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=order.uploaded_file.original_filename,
        conditional=True,
    )


@api.get("/owner/dashboard")
@role_required("owner")
def owner_dashboard():
    orders = Order.query.order_by(Order.created_at.desc()).limit(50).all()
    return jsonify(
        orders=[_serialize_order(order) for order in orders],
        prices=_serialize_prices(_get_or_create_prices()),
    )


@api.put("/owner/prices")
@role_required("owner")
def update_prices():
    values = _json_body()
    fields = {
        "blackWhitePagePrice": "black_white_page_price",
        "colorPagePrice": "color_page_price",
        "simpleBindingPrice": "simple_binding_price",
        "spiralBindingPrice": "spiral_binding_price",
        "urgentPercentage": "urgent_percentage",
    }
    try:
        converted = {field: Decimal(str(values[key])) for key, field in fields.items()}
        max_file_size = int(values["maxFileSizeMb"])
    except (KeyError, TypeError, ValueError, InvalidOperation):
        return jsonify(error="Narx sozlamalaridagi qiymatlarni tekshiring."), 400
    if any(not value.is_finite() or value < 0 for value in converted.values()):
        return jsonify(error="Narxlar manfiy bo‘lishi mumkin emas."), 400
    if converted["urgent_percentage"] > 100 or not 1 <= max_file_size <= 100:
        return jsonify(error="Shoshilinch foiz yoki fayl hajmi chegaradan tashqarida."), 400

    prices = _get_or_create_prices()
    for field, value in converted.items():
        setattr(prices, field, value)
    prices.max_file_size_mb = max_file_size
    prices.updated_by = current_user.id
    db.session.commit()
    return jsonify(prices=_serialize_prices(prices))
