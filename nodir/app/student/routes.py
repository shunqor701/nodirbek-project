import os
from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, send_from_directory, url_for
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import FileField, IntegerField, SelectField, SubmitField, BooleanField
from wtforms.validators import DataRequired, NumberRange

from ..decorators import role_required
from ..extensions import db
from ..models import Order, OrderStatusHistory, Payment, PrintParameter, UploadedFile
from ..utils import allowed_pdf, calculate_price, hash_code, make_order_number, make_pickup_code, pdf_page_count, safe_stored_name

student = Blueprint("student", __name__, url_prefix="/student")


class OrderForm(FlaskForm):
    file = FileField("PDF fayl", validators=[DataRequired()])
    page_from = IntegerField("Boshlang‘ich bet", validators=[DataRequired(), NumberRange(min=1)])
    page_to = IntegerField("Oxirgi bet", validators=[DataRequired(), NumberRange(min=1)])
    copies = IntegerField("Nusxalar", validators=[DataRequired(), NumberRange(min=1, max=100)])
    color_mode = SelectField("Rang", choices=[("bw", "Oq-qora"), ("color", "Rangli")])
    side_mode = SelectField("Chop turi", choices=[("single", "Bir tomonlama"), ("double", "Ikki tomonlama")])
    binding_type = SelectField("Muqova", choices=[("none", "Muqovasiz"), ("simple", "Oddiy muqova"), ("spiral", "Spiral muqova")])
    is_urgent = BooleanField("Shoshilinch buyurtma")
    submit = SubmitField("Buyurtmani yaratish")


@student.route("/dashboard")
@role_required("student")
def dashboard():
    orders = Order.query.filter_by(student_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("student/dashboard.html", orders=orders)


@student.route("/orders/new", methods=["GET", "POST"])
@role_required("student")
def new_order():
    form = OrderForm()
    if form.validate_on_submit():
        upload = form.file.data
        if not allowed_pdf(upload.filename):
            flash("Faqat PDF fayl yuklash mumkin.", "danger")
            return render_template("student/new_order.html", form=form)
        try:
            upload.stream.seek(0)
            pages = pdf_page_count(upload)
            if form.page_to.data > pages or form.page_from.data > form.page_to.data:
                raise ValueError("Betlar oralig‘i hujjat sahifalariga mos emas.")
            values = calculate_price(pages, form.page_from.data, form.page_to.data, form.copies.data,
                                     form.color_mode.data, form.side_mode.data, form.binding_type.data,
                                     form.is_urgent.data)
        except Exception as exc:
            flash(f"PDF faylni tekshirishda xato: {exc}", "danger")
            return render_template("student/new_order.html", form=form)
        code = make_pickup_code()
        order = Order(order_number=make_order_number(), student_id=current_user.id,
                      pickup_code_hash=hash_code(code), total_price=values[-1], is_urgent=form.is_urgent.data)
        db.session.add(order)
        db.session.flush()
        upload.stream.seek(0)
        if upload.stream.read(5) != b"%PDF-":
            flash("Yuklangan fayl to‘liq va yaroqli PDF emas.", "danger")
            return render_template("student/new_order.html", form=form)
        upload.stream.seek(0)
        stored = safe_stored_name(upload.filename)
        upload.save(os.path.join(current_app.config["UPLOAD_FOLDER"], stored))
        db.session.add(UploadedFile(order_id=order.id, original_filename=upload.filename, stored_filename=stored,
                                    relative_path=stored, file_size=os.path.getsize(os.path.join(current_app.config["UPLOAD_FOLDER"], stored)),
                                    page_count=pages))
        db.session.add(PrintParameter(order_id=order.id, page_from=form.page_from.data, page_to=form.page_to.data,
                                      copies=form.copies.data, color_mode=form.color_mode.data, side_mode=form.side_mode.data,
                                      binding_type=form.binding_type.data, selected_page_count=values[0], total_printed_pages=values[1],
                                      calculated_sheet_count=values[2], print_cost=values[3], binding_cost=values[4], urgent_cost=values[5]))
        db.session.add(Payment(order_id=order.id, amount=values[-1]))
        db.session.add(OrderStatusHistory(order_id=order.id, new_status="new", changed_by=current_user.id, note="Buyurtma yaratildi"))
        db.session.commit()
        return render_template("student/created.html", order=order, pickup_code=code)
    return render_template("student/new_order.html", form=form)


@student.route("/orders/<int:order_id>")
@role_required("student")
def detail(order_id):
    order = Order.query.filter_by(id=order_id, student_id=current_user.id).first_or_404()
    return render_template("student/detail.html", order=order)


@student.route("/orders/<int:order_id>/cancel", methods=["POST"])
@role_required("student")
def cancel(order_id):
    order = Order.query.filter_by(id=order_id, student_id=current_user.id).first_or_404()
    if order.status not in {"new", "queued"}:
        flash("Bu holatda buyurtmani bekor qilib bo‘lmaydi.", "danger")
    else:
        order.status = "cancelled"
        order.cancelled_at = datetime.utcnow()
        db.session.add(OrderStatusHistory(order_id=order.id, old_status="new", new_status="cancelled", changed_by=current_user.id))
        db.session.commit()
        flash("Buyurtma bekor qilindi.", "success")
    return redirect(url_for("student.detail", order_id=order.id))
