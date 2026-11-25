from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFError

from config import Config
from .extensions import csrf, db, login_manager


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder="../views",
        static_folder="../public",
        static_url_path="",
    )
    app.config.from_object(config_class)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    if not app.config["IS_VERCEL"]:
        Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    from .models import PriceSetting, User

    @app.before_request
    def set_upload_size_limit():
        if request.path in {"/student/orders/new", "/api/student/orders"}:
            max_size_mb = db.session.scalar(db.select(PriceSetting.max_file_size_mb)) or 16
            request.max_content_length = max_size_mb * 1024 * 1024 + 1024 * 1024

    csrf.init_app(app)

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/api/"):
            return jsonify(error="Tizimga kirish talab qilinadi."), 401
        return redirect(url_for(login_manager.login_view))

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from .auth.routes import auth
    from .main.routes import main
    from .student.routes import student
    from .operator.routes import operator
    from .owner.routes import owner
    from .api import api
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(student)
    app.register_blueprint(operator)
    app.register_blueprint(owner)
    app.register_blueprint(api)

    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith("/api/"):
            return jsonify(error="Bu amal uchun ruxsatingiz yo‘q."), 403
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify(error="So‘ralgan ma’lumot topilmadi."), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(error):
        if request.path.startswith("/api/"):
            return jsonify(error="Yuklangan fayl ruxsat etilgan hajmdan katta."), 413
        return render_template("errors/413.html"), 413

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        if request.path.startswith("/api/"):
            return jsonify(error="CSRF token noto‘g‘ri yoki eskirgan."), 400
        return error.description, 400

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        if request.path.startswith("/api/"):
            return jsonify(error="Serverda kutilmagan xatolik yuz berdi."), 500
        return render_template("errors/500.html"), 500

    with app.app_context():
        db.create_all()
    return app
