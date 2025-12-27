from app.database import get_session
from app.models.domain import Owner, UserRole
from sqlmodel import select

def promote_admin():
    email = "mlgvalentin@gmail.com"
    with next(get_session()) as session:
        owner = session.exec(select(Owner).where(Owner.email == email)).first()
        if owner:
            owner.role = UserRole.ADMIN
            session.add(owner)
            session.commit()
            print(f"User {email} promoted to ADMIN.")
        else:
            print(f"User {email} not found.")

if __name__ == "__main__":
    promote_admin()
