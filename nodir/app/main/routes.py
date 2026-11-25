from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user

main = Blueprint("main", __name__)


@main.route("/")
def index():
    if current_user.is_authenticated:
        targets = {"student": "student.dashboard", "operator": "operator.dashboard", "owner": "owner.dashboard"}
        target = targets.get(current_user.role)
        if target is None:
            return render_template("errors/403.html"), 403
        return redirect(url_for(target))
    return render_template("index.html", user=current_user)
