"""
Database Viewer for DailyHands
Run: python view_db.py
"""
import sqlite3

def view_database():
    conn = sqlite3.connect('dailyhands.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("\n" + "="*50)
    print("  DAILYHANDS DATABASE VIEWER")
    print("="*50)
    
    print("\n📋 TABLES IN DATABASE:")
    for table in tables:
        print(f"   • {table[0]}")
    
    print("\n" + "-"*50)
    
    # Show data from each table
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        print(f"\n📁 {table_name.upper()} ({count} records)")
        
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"   Columns: {', '.join(columns)}")
            
            for row in rows:
                print(f"   → {row}")
        else:
            print("   (empty)")
    
    conn.close()
    print("\n" + "="*50)
    print("  To run the app: python app.py")
    print("  Then open: http://127.0.0.1:5000")
    print("="*50 + "\n")

if __name__ == '__main__':
    view_database()
