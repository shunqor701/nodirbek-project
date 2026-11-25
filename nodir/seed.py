from app import create_app
from app.extensions import db
from app.models import PriceSetting, User

app = create_app()
with app.app_context():
    for username, email, name, role, password in (
        ("operator", "operator@example.com", "Operator", "operator", "Operator123!"),
        ("owner", "owner@example.com", "Markaz egasi", "owner", "Owner123!"),
    ):
        if not User.query.filter_by(username=username).first():
            user = User(username=username, email=email, full_name=name, role=role)
            user.set_password(password)
            db.session.add(user)
    if not PriceSetting.query.first():
        db.session.add(PriceSetting())
    db.session.commit()
    print("Seed bajarildi. Operator: operator / Operator123!, Owner: owner / Owner123!")
