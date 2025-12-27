
import sqlite3

def migrate():
    print("Migrating database to make Operation.lot_id nullable...")
    
    # SQLite doesn't support ALTER COLUMN easily. 
    # We must:
    # 1. Rename table
    # 2. Create new table with correct schema
    # 3. Copy data
    # 4. Drop old table
    
    conn = sqlite3.connect("vigie.db")
    cursor = conn.cursor()
    
    try:
        # Check current schema
        cursor.execute("PRAGMA table_info(operation)")
        columns = cursor.fetchall()
        # (cid, name, type, notnull, dflt_value, pk)
        lot_col = next((c for c in columns if c[1] == 'lot_id'), None)
        
        if lot_col and lot_col[3] == 0:
            print("Operation.lot_id is already nullable. Skipping.")
            return

        print("Beginning schema update...")
        cursor.execute("BEGIN TRANSACTION")
        
        # 1. Rename
        cursor.execute("ALTER TABLE operation RENAME TO operation_old")
        
        # 2. Create New (From SQLModel schema, but manual here for script independence)
        # Note: We must match the EXACT schema defined in domain.py, but with lot_id NOT NULL removed.
        cursor.execute("""
            CREATE TABLE operation (
                id INTEGER PRIMARY KEY,
                date DATE NOT NULL,
                lot_id INTEGER,
                bank_account_id INTEGER NOT NULL,
                type VARCHAR NOT NULL,
                category VARCHAR NOT NULL,
                label VARCHAR NOT NULL,
                amount DECIMAL(14, 2) NOT NULL,
                paid_by_owner_id INTEGER,
                proof_filename VARCHAR,
                FOREIGN KEY (lot_id) REFERENCES lot (id),
                FOREIGN KEY (bank_account_id) REFERENCES bankaccount (id),
                FOREIGN KEY (paid_by_owner_id) REFERENCES owner (id)
            )
        """)
        
        # 3. Copy Data
        cursor.execute("""
            INSERT INTO operation (id, date, lot_id, bank_account_id, type, category, label, amount, paid_by_owner_id, proof_filename)
            SELECT id, date, lot_id, bank_account_id, type, category, label, amount, paid_by_owner_id, proof_filename
            FROM operation_old
        """)
        
        # 4. Drop Old
        cursor.execute("DROP TABLE operation_old")
        
        conn.commit()
        print("Migration successful.")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
