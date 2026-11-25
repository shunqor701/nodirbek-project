from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user

main = Blueprint("main", __name__)


@main.route("/")
def index():
    if current_user.is_authenticated:
        targets = {"student": "student.dashboard", "operator": "operator.dashboard", "owner": "owner.dashboard"}
        return redirect(url_for(targets[current_user.role]))
    return render_template("index.html", user=current_user)
