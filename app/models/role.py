# models/role.py
from ..extensions import db

user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
)

class Role(db.Model):
    __tablename__ = "roles"
    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(32), unique=True, nullable=False)   # visitor/candidate, client, rep, admin
    level     = db.Column(db.Integer, nullable=False, default=0)        # 0                , 10    , 20 , 30

    def __repr__(self) -> str:
        return f"<Role {self.name}({self.level})>"