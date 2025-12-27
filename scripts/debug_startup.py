import sys
import os

print("1. Starting Debug Script...")
try:
    print("2. Importing SQLModel...")
    from sqlmodel import select
    print("   Success.")

    print("3. Importing Domain Models...")
    from app.models.domain import Owner
    print("   Success.")

    print("4. Importing Auth Service...")
    from app.services.auth import get_password_hash
    print("   Success.")
    
    print("5. Testing Password Hash (Argon2)...")
    hash = get_password_hash("test")
    print(f"   Success: {hash[:10]}...")

    print("6. Importing Database...")
    from app.database import get_session, create_db_and_tables
    print("   Success.")

    print("7. Testing DB Connection...")
    create_db_and_tables()
    with next(get_session()) as session:
        owners = session.exec(select(Owner)).all()
        print(f"   Success. Found {len(owners)} owners.")

    print("8. Importing Main App...")
    from app.main import main
    print("   Success.")
    
    print("\nALL CHECKS PASSED. The backend code is fine.")

except Exception as e:
    print(f"\nCRITICAL FAILURE: {e}")
    import traceback
    traceback.print_exc()
