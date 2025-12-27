from app.database import get_session
from app.services.auth import get_password_hash
from app.models.domain import Owner, UserRole
from sqlmodel import select

def bootstrap_data():
    """
    Creates an initial admin user if the database is empty.
    """
    with next(get_session()) as session:
        # Check if any owner exists
        owners = session.exec(select(Owner)).all()
        if not owners:
            print("Database empty. Creating initial admin user...")
            admin = Owner(
                name="Administrateur",
                email="admin@vigie.local",
                role=UserRole.ADMIN,
                theme="DARK",
                password_hash=get_password_hash("vigie2026")
            )
            session.add(admin)
            session.commit()
            print("Admin user created: admin@vigie.local / vigie2026")
        else:
            # Optionally check if certain specific users exist
            pass
