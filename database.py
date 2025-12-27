import json
import os

DB_FILE = "library.json"

def get_all_data():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except: return []

# Update: Menerima parameter genre
def save_new_movie(title, genre, path):
    movies = get_all_data()
    
    # Cek duplikat
    for m in movies:
        if m['path'] == path:
            return False 

    # Simpan dengan struktur baru
    movies.append({
        "title": title, 
        "genre": genre, 
        "path": path
    })
    
    with open(DB_FILE, 'w') as f:
        json.dump(movies, f, indent=4)
    return True

def delete_movie_by_path(path):
    movies = get_all_data()
    new_list = [m for m in movies if m['path'] != path]
    with open(DB_FILE, 'w') as f:
        json.dump(new_list, f, indent=4)
    return True