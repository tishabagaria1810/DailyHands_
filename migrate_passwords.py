"""
One-time migration script to hash existing plain text passwords
Run this ONCE before deploying password hashing changes
"""
import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = 'dailyhands.db'

def migrate_passwords():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("  PASSWORD MIGRATION SCRIPT")
    print("=" * 60)
    
    # Migrate users (contractors) table
    print("\n[1/2] Migrating USERS (Contractors) passwords...")
    cursor.execute("SELECT id, password FROM users")
    users = cursor.fetchall()
    
    users_migrated = 0
    for user_id, password in users:
        # Check if already hashed (bcrypt hashes start with $2b$)
        if not password.startswith('pbkdf2:sha256:') and not password.startswith('scrypt:'):
            hashed = generate_password_hash(password)
            cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed, user_id))
            users_migrated += 1
    
    print(f"   ✓ Migrated {users_migrated} contractor passwords")
    
    # Migrate agencies table
    print("\n[2/2] Migrating AGENCIES passwords...")
    cursor.execute("SELECT id, password FROM agencies")
    agencies = cursor.fetchall()
    
    agencies_migrated = 0
    for agency_id, password in agencies:
        # Check if already hashed
        if not password.startswith('pbkdf2:sha256:') and not password.startswith('scrypt:'):
            hashed = generate_password_hash(password)
            cursor.execute("UPDATE agencies SET password = ? WHERE id = ?", (hashed, agency_id))
            agencies_migrated += 1
    
    print(f"   ✓ Migrated {agencies_migrated} agency passwords")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"  MIGRATION COMPLETE!")
    print(f"  Total: {users_migrated + agencies_migrated} passwords hashed")
    print("=" * 60)
    print("\n⚠️  IMPORTANT: Existing users can still login with their")
    print("   original passwords. The system now stores them securely.\n")

if __name__ == '__main__':
    try:
        migrate_passwords()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("   Make sure dailyhands.db exists in the current directory.\n")
