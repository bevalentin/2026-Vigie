import sqlite3

def migrate():
    print("Migrating: Adding 'theme' column to 'owner' table...")
    conn = sqlite3.connect('vigie.db')
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(owner)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'theme' not in columns:
            print("Adding column 'theme'...")
            cursor.execute("ALTER TABLE owner ADD COLUMN theme TEXT DEFAULT 'LIGHT'")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column 'theme' already exists.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
