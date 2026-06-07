import sqlite3
import os

DATABASE_PATH = r"c:\Users\Asus\OneDrive\Documents\Tunely\Backend\tunely_v3.db"

def clear_bailando_cache():
    if not os.path.exists(DATABASE_PATH):
        print("Database file does not exist.")
        return
        
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if enrique_iglesias_bailando exists
        cursor.execute("SELECT song_id, artist, title FROM lyrics_timestamps WHERE song_id LIKE '%bailando%'")
        rows = cursor.fetchall()
        if rows:
            print("Found cached Bailando records:")
            for r in rows:
                print(f"  {r[0]}: {r[1]} - {r[2]}")
                
            # Delete them
            cursor.execute("DELETE FROM lyrics_timestamps WHERE song_id LIKE '%bailando%'")
            conn.commit()
            print("Successfully deleted cached Bailando records.")
        else:
            print("No cached Bailando records found.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clear_bailando_cache()
