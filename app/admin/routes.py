# app/admin/routes.py
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user

from app.auth.permissions import require_level
from ..models import User, Role, db
from . import bp

def get_rep_role():
    # first call is after the app context exists; result is cached
    return Role.query.filter_by(name="rep").one()

@bp.route("/users")
@require_level(30)
def users():
    page = request.args.get("p", 1, type=int)
    users = (User.query
                  .order_by(User.created_at.desc())
                  .paginate(page=page, per_page=25, error_out=False))
    return render_template("admin/users.html", users=users)

@bp.route("/toggle-rep/<int:uid>", methods=["POST"])
@require_level(30)
def toggle_rep(uid):
    user = User.query.get_or_404(uid)
    rep_role = get_rep_role()

    if rep_role in user.roles:
        user.roles.remove(rep_role)
        flash(f"{user.display_name} ({user.email}) is no longer a representative.", "info")
    else:
        user.roles.append(rep_role)
        flash(f"{user.display_name} ({user.email}) promoted to representative.", "success")

    db.session.commit()
    return redirect(url_for("admin.users", p=request.args.get("p", 1)))