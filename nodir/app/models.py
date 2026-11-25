from datetime import datetime
from decimal import Decimal

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student", index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    orders = db.relationship("Order", back_populates="student", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="new", index=True)
    pickup_code_hash = db.Column(db.String(255), nullable=False)
    pickup_code_used = db.Column(db.Boolean, nullable=False, default=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    is_urgent = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    printing_started_at = db.Column(db.DateTime)
    ready_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    student = db.relationship("User", back_populates="orders")
    uploaded_file = db.relationship("UploadedFile", back_populates="order", uselist=False, cascade="all, delete-orphan")
    print_parameter = db.relationship("PrintParameter", back_populates="order", uselist=False, cascade="all, delete-orphan")
    payment = db.relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")
    history = db.relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")


class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), unique=True, nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    relative_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    page_count = db.Column(db.Integer, nullable=False)
    file_deleted = db.Column(db.Boolean, nullable=False, default=False)
    deleted_at = db.Column(db.DateTime)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    order = db.relationship("Order", back_populates="uploaded_file")


class PrintParameter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), unique=True, nullable=False)
    page_from = db.Column(db.Integer, nullable=False)
    page_to = db.Column(db.Integer, nullable=False)
    copies = db.Column(db.Integer, nullable=False)
    color_mode = db.Column(db.String(20), nullable=False)
    side_mode = db.Column(db.String(20), nullable=False)
    binding_type = db.Column(db.String(20), nullable=False)
    selected_page_count = db.Column(db.Integer, nullable=False)
    total_printed_pages = db.Column(db.Integer, nullable=False)
    calculated_sheet_count = db.Column(db.Integer, nullable=False)
    print_cost = db.Column(db.Numeric(10, 2), nullable=False)
    binding_cost = db.Column(db.Numeric(10, 2), nullable=False)
    urgent_cost = db.Column(db.Numeric(10, 2), nullable=False)
    order = db.relationship("Order", back_populates="print_parameter")


class PriceSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    black_white_page_price = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("500"))
    color_page_price = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("1500"))
    simple_binding_price = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("5000"))
    spiral_binding_price = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("10000"))
    urgent_percentage = db.Column(db.Numeric(5, 2), nullable=False, default=Decimal("20"))
    max_file_size_mb = db.Column(db.Integer, nullable=False, default=16)
    updated_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), unique=True, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(30), nullable=False, default="markazda")
    payment_status = db.Column(db.String(20), nullable=False, default="pending")
    paid_at = db.Column(db.DateTime)
    accepted_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    order = db.relationship("Order", back_populates="payment")


class OrderStatusHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    note = db.Column(db.String(255))
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    order = db.relationship("Order", back_populates="history")
