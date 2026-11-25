from io import BytesIO

from pypdf import PdfWriter, PdfReader

from app.extensions import db
from app.models import Order, UploadedFile, User


def make_pdf():
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(output)
    output.seek(0)
    return output


def login(client, username, password):
    return client.post("/auth/login", data={"username": username, "password": password})


def test_new_upload_remains_complete_pdf(app, client):
    with app.app_context():
        student = User(full_name="Student", username="student_upload", email="student_upload@test.local", role="student")
        student.set_password("Student123!")
        db.session.add(student)
        db.session.commit()

    login(client, "student_upload", "Student123!")
    pdf = make_pdf()
    response = client.post("/student/orders/new", data={
        "file": (pdf, "hujjat.pdf", "application/pdf"),
        "page_from": "1",
        "page_to": "1",
        "copies": "1",
        "color_mode": "bw",
        "side_mode": "single",
        "binding_type": "none",
        "is_urgent": "",
    })
    assert response.status_code == 200

    with app.app_context():
        uploaded = UploadedFile.query.first()
        assert uploaded is not None
        path = app.config["UPLOAD_FOLDER"] + "/" + uploaded.stored_filename
        with open(path, "rb") as file:
            assert file.read(5) == b"%PDF-"
        import os
        os.unlink(path)


def test_operator_can_open_pdf_and_move_order_to_printing(app, client):
    with app.app_context():
        operator = User(full_name="Operator", username="operator", email="operator@test.local", role="operator")
        operator.set_password("Operator123!")
        student = User(full_name="Student", username="student", email="student@test.local", role="student")
        student.set_password("Student123!")
        db.session.add_all([operator, student])
        db.session.flush()
        order = Order(
            order_number="TEST1234", student_id=student.id, status="new",
            pickup_code_hash="not-used", total_price=500,
        )
        db.session.add(order)
        db.session.flush()
        pdf = make_pdf()
        filename = "test_operator_flow.pdf"
        path = app.config["UPLOAD_FOLDER"] + "/" + filename
        with open(path, "wb") as file:
            file.write(pdf.read())
        db.session.add(UploadedFile(
            order_id=order.id, original_filename="hujjat.pdf", stored_filename=filename,
            relative_path=filename, file_size=0, page_count=1,
        ))
        db.session.commit()
        order_id = order.id

    login(client, "operator", "Operator123!")
    response = client.get(f"/operator/files/{order_id}")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.headers["Content-Disposition"].startswith("inline;")
    assert PdfReader(BytesIO(response.data)).pages

    response = client.post(f"/operator/orders/{order_id}/status/printing")
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Order, order_id).status == "printing"


def test_deleted_pdf_is_not_presented_as_404(app, client):
    with app.app_context():
        operator = User(full_name="Operator", username="operator_deleted", email="operator_deleted@test.local", role="operator")
        operator.set_password("Operator123!")
        student = User(full_name="Student", username="student_deleted", email="student_deleted@test.local", role="student")
        student.set_password("Student123!")
        db.session.add_all([operator, student])
        db.session.flush()
        order = Order(order_number="DELETED1", student_id=student.id, status="ready", pickup_code_hash="unused", total_price=500)
        db.session.add(order)
        db.session.flush()
        db.session.add(UploadedFile(order_id=order.id, original_filename="deleted.pdf", stored_filename="deleted.pdf", relative_path="deleted.pdf", file_size=10, page_count=1, file_deleted=True))
        db.session.commit()
        order_id = order.id

    login(client, "operator_deleted", "Operator123!")
    response = client.get(f"/operator/files/{order_id}", follow_redirects=False)
    assert response.status_code == 302
    assert "/operator/dashboard" in response.headers["Location"]
