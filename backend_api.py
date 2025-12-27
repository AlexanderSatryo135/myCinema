import eel
import tkinter as tk
from tkinter import filedialog
import os
import database

@eel.expose
def api_get_movies():
    return database.get_all_data()

# FUNGSI 1: Hanya membuka dialog Windows untuk ambil Path file
@eel.expose
def api_pick_file():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    file_path = filedialog.askopenfilename(
        title="Pilih Film",
        filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov")]
    )
    root.destroy()
    
    if file_path:
        # Kembalikan path dan nama file otomatis ke JavaScript
        filename = os.path.basename(file_path)
        title = os.path.splitext(filename)[0]
        return {"found": True, "path": file_path, "default_title": title}
    
    return {"found": False}

# FUNGSI 2: Menyimpan data setelah user input Genre di UI
@eel.expose
def api_save_movie_data(title, genre, path):
    return database.save_new_movie(title, genre, path)

@eel.expose
def api_play_video(path):
    if os.path.exists(path):
        os.startfile(path)
    else:
        print("File not found")

@eel.expose
def api_delete_movie(path):
    return database.delete_movie_by_path(path)