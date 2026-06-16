from flask import Blueprint, render_template, session, redirect, url_for
from database.db import mysql

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    print("SESSION DATA:", session)   # 🔥 ADD THIS

    username = session.get("username")

    return render_template("dashboard.html", username=username)
