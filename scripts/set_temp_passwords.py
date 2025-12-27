from app.database import get_session
from app.models.domain import Owner, UserRole
from app.services.auth import get_password_hash
from sqlmodel import select

def set_passwords():
    print("Setting temporary passwords...")
    pwd_hash = get_password_hash("vigie2026")
    
    with next(get_session()) as session:
        owners = session.exec(select(Owner)).all()
        count = 0
        for o in owners:
            o.password_hash = pwd_hash
            # Default to WRITE so user can test features
            if o.role == UserRole.READ: 
                o.role = UserRole.WRITE
            session.add(o)
            count += 1
            print(f"Updated {o.name} ({o.email})")
        
        session.commit()
    print(f"Done. {count} owners updated with password 'vigie2026'.")

if __name__ == "__main__":
    set_passwords()
