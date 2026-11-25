from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, send_from_directory, url_for
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

from ..decorators import role_required
from ..extensions import db
from ..models import Order, OrderStatusHistory
from ..utils import verify_code

operator = Blueprint("operator", __name__, url_prefix="/operator")


class PickupForm(FlaskForm):
    code = StringField("Olish kodi", validators=[DataRequired()])
    submit = SubmitField("Tekshirish")


@operator.route("/dashboard")
@role_required("operator")
def dashboard():
    orders = Order.query.filter(Order.status.in_(("new", "queued", "printing", "ready"))).order_by(Order.is_urgent.desc(), Order.created_at.asc()).all()
    return render_template("operator/dashboard.html", orders=orders, action_form=FlaskForm())


@operator.route("/orders/<int:order_id>/status/<status>", methods=["POST"])
@role_required("operator")
def set_status(order_id, status):
    order = db.session.get(Order, order_id)
    if not order or status not in {"printing", "ready"}:
        return render_template("errors/404.html"), 404
    allowed = {"new": "printing", "queued": "printing", "printing": "ready"}
    if allowed.get(order.status) != status:
        flash("Buyurtma holatini bu tarzda o‘zgartirib bo‘lmaydi.", "danger")
    else:
        old = order.status
        order.status = status
        if status == "printing":
            order.printing_started_at = datetime.utcnow()
        else:
            order.ready_at = datetime.utcnow()
        db.session.add(OrderStatusHistory(order_id=order.id, old_status=old, new_status=status, changed_by=current_user.id))
        db.session.commit()
    return redirect(url_for("operator.dashboard"))


@operator.route("/pickup", methods=["GET", "POST"])
@role_required("operator")
def pickup():
    form = PickupForm()
    order = None
    if form.validate_on_submit():
        order = next((item for item in Order.query.filter_by(status="ready", pickup_code_used=False).all()
                      if verify_code(form.code.data, item.pickup_code_hash)), None)
        if order:
            order.status = "completed"
            order.pickup_code_used = True
            order.completed_at = datetime.utcnow()
            db.session.add(OrderStatusHistory(order_id=order.id, old_status="ready", new_status="completed", changed_by=current_user.id))
            db.session.commit()
            flash(f"{order.order_number} buyurtmasi topshirildi.", "success")
        else:
            flash("Olish kodi noto‘g‘ri yoki buyurtma tayyor emas.", "danger")
    return render_template("operator/pickup.html", form=form, order=order)


@operator.route("/files/<int:order_id>")
@role_required("operator")
def download(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return render_template("errors/404.html"), 404
    if not order.uploaded_file or order.uploaded_file.file_deleted:
        flash("Bu buyurtmaning PDF fayli mavjud emas. Talabadan faylni qayta yuklashini so‘rang.", "warning")
        return redirect(url_for("operator.dashboard"))
    response = send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        order.uploaded_file.stored_filename,
        mimetype="application/pdf",
        as_attachment=False,
        conditional=True,
    )
    response.headers["Content-Disposition"] = f'inline; filename="{order.uploaded_file.original_filename}"'
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "private, no-store, max-age=0"
    return response
