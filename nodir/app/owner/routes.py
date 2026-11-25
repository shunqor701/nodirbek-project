from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import DecimalField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange

from ..decorators import role_required
from ..extensions import db
from ..models import Order, PriceSetting

owner = Blueprint("owner", __name__, url_prefix="/owner")


class PriceForm(FlaskForm):
    black_white_page_price = DecimalField("Oq-qora bet narxi", validators=[DataRequired(), NumberRange(min=0)])
    color_page_price = DecimalField("Rangli bet narxi", validators=[DataRequired(), NumberRange(min=0)])
    simple_binding_price = DecimalField("Oddiy muqova", validators=[DataRequired(), NumberRange(min=0)])
    spiral_binding_price = DecimalField("Spiral muqova", validators=[DataRequired(), NumberRange(min=0)])
    urgent_percentage = DecimalField("Shoshilinch ustama (%)", validators=[DataRequired(), NumberRange(min=0, max=100)])
    max_file_size_mb = IntegerField("Maksimal fayl hajmi (MB)", validators=[DataRequired(), NumberRange(min=1, max=100)])
    submit = SubmitField("Saqlash")


@owner.route("/dashboard")
@role_required("owner")
def dashboard():
    return render_template("owner/dashboard.html", orders=Order.query.order_by(Order.created_at.desc()).limit(20).all(),
                           prices=PriceSetting.query.first())


@owner.route("/prices", methods=["GET", "POST"])
@role_required("owner")
def prices():
    setting = PriceSetting.query.first() or PriceSetting()
    form = PriceForm(obj=setting)
    if form.validate_on_submit():
        for field in ("black_white_page_price", "color_page_price", "simple_binding_price", "spiral_binding_price",
                      "urgent_percentage", "max_file_size_mb"):
            setattr(setting, field, getattr(form, field).data)
        setting.updated_by = current_user.id
        db.session.add(setting)
        db.session.commit()
        flash("Narxlar saqlandi. Eski buyurtmalar narxi o‘zgarmaydi.", "success")
        return redirect(url_for("owner.prices"))
    return render_template("owner/prices.html", form=form)
