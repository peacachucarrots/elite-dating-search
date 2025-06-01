import click
from flask.cli import with_appcontext
from .models import Role
from .extensions import db

@click.command("seed-roles")
@with_appcontext
def seed_roles():
    """Insert visitor / rep / admin rows if they’re missing."""
    default_roles = [
        ("visitor", 10),
        ("rep",     20),
        ("admin",   30),
    ]

    created = 0
    for name, level in default_roles:
        if not Role.query.filter_by(name=name).first():
            db.session.add(Role(name=name, level=level))
            created += 1
    if created:
        db.session.commit()
        click.echo(f"✅  Added {created} role(s).")
    else:
        click.echo("ℹ️  Roles already present.")

def register_commands(app):
    """Attach custom CLI commands to the Flask app."""
    app.cli.add_command(seed_roles)