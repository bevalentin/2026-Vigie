from app.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as connection:
        print("Migrating Owner table...")
        try:
            connection.execute(text("ALTER TABLE owner ADD COLUMN password_hash VARCHAR"))
            print("Added password_hash column.")
        except Exception as e:
            print(f"Skipping password_hash (maybe exists): {e}")

        try:
            connection.execute(text("ALTER TABLE owner ADD COLUMN role VARCHAR DEFAULT 'READ'"))
            print("Added role column.")
        except Exception as e:
            print(f"Skipping role (maybe exists): {e}")
        
        connection.commit()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
