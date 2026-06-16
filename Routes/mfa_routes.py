from flask import Blueprint

mfa_bp = Blueprint("mfa", __name__)

@mfa_bp.route("/mfa-test")
def mfa_test():
    return "MFA Module Working 🔐"
