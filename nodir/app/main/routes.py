from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    send_from_directory,
    url_for,
)
from flask_login import current_user

main = Blueprint("main", __name__)


@main.route("/")
def index():
    if current_app.static_folder:
        frontend_index = Path(current_app.static_folder) / "index.html"
        if frontend_index.is_file():
            return send_from_directory(current_app.static_folder, "index.html")

    if current_user.is_authenticated:
        targets = {"student": "student.dashboard", "operator": "operator.dashboard", "owner": "owner.dashboard"}
        target = targets.get(current_user.role)
        if target is None:
            return render_template("errors/403.html"), 403
        return redirect(url_for(target))
    return render_template("index.html", user=current_user)
