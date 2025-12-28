import eel
import os
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog
import json
import re
import time 
import sys 

# --- KONFIGURASI PATH SISTEM ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    eel.init(os.path.join(sys._MEIPASS, 'web'))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    eel.init('web')

# Path absolut ke folder movies
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'web', 'movies')
DB_FILE = os.path.join(BASE_DIR, 'database.json')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- DATABASE HANDLER ---
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: return []
    return []

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)

# --- FUNGSI SCAN SUBTITLE (DENGAN PATH YANG AMAN) ---
def extract_best_subtitle(video_path, output_vtt_path):
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    if os.path.exists(output_vtt_path): os.remove(output_vtt_path)

    # Strategi 1: Cek Label Bahasa (Indo/Eng)
    for lang in ['ind', 'id', 'eng', 'en']:
        cmd = ['ffmpeg', '-y', '-i', video_path, '-map', f'0:m:language:{lang}?', '-c:s', 'webvtt', output_vtt_path]
        subprocess.run(cmd, startupinfo=startupinfo, stderr=subprocess.PIPE)
        if os.path.exists(output_vtt_path) and os.path.getsize(output_vtt_path) > 150:
            return True

    # Strategi 2: Bruteforce Track 0-30
    for i in range(31):
        cmd = ['ffmpeg', '-y', '-i', video_path, '-map', f'0:s:{i}', '-c:s', 'webvtt', output_vtt_path]
        subprocess.run(cmd, startupinfo=startupinfo, stderr=subprocess.PIPE)
        if os.path.exists(output_vtt_path) and os.path.getsize(output_vtt_path) > 150:
            return True
    return False

# --- API EEL ---
@eel.expose
def get_all_movies():
    return load_db()

@eel.expose
def rescan_single_movie_subtitle(movie_id):
    db = load_db()
    movie = next((m for m in db if m["id"] == movie_id), None)
    if not movie: return "Film tidak ditemukan."

    # Gunakan UPLOAD_FOLDER (Absolut) untuk operasi file sistem
    video_filename = os.path.basename(movie['video']) # Ambil nama file saja "jurassic_park.mp4"
    video_abs_path = os.path.join(UPLOAD_FOLDER, video_filename)
    
    # Path output subtitle
    sub_filename = f"{movie_id}.vtt"
    sub_abs_path = os.path.join(UPLOAD_FOLDER, sub_filename)
    
    if os.path.exists(video_abs_path):
        if extract_best_subtitle(video_abs_path, sub_abs_path):
            # Update DB dengan path relatif web
            for m in db:
                if m["id"] == movie_id:
                    m['subtitle'] = f"movies/{sub_filename}"
            save_db(db)
            return "SUKSES: Subtitle ditemukan & dipasang!"
        return "GAGAL: Tidak ada subtitle teks di dalam file."
    return f"ERROR: File video tidak ada di {video_abs_path}"

@eel.expose
def process_upload(judul, genre, sinopsis, v_path, p_path, s_path):
    # 1. BERSIHKAN NAMA FILE DARI SPASI (FIX UTAMA)
    clean_judul = judul.replace(" ", "_").replace(":", "").replace("-", "_")
    clean_judul = "".join(x for x in clean_judul if x.isalnum() or x == "_")
    
    timestamp = str(int(time.time()))
    movie_id = f"{timestamp}_{clean_judul}" # Contoh: 123456_Jurassic_Park
    
    # Nama File Output
    v_name = f"{movie_id}.mp4"
    p_name = f"{movie_id}_poster{os.path.splitext(p_path)[1]}"
    s_name = f"{movie_id}.vtt"

    # Path Absolut (Untuk Python copy file)
    v_abs = os.path.join(UPLOAD_FOLDER, v_name)
    p_abs = os.path.join(UPLOAD_FOLDER, p_name)
    s_abs = os.path.join(UPLOAD_FOLDER, s_name)

    # Proses Copy Video
    if v_path.lower().endswith('.mp4'):
        shutil.copy(v_path, v_abs)
    else:
        # Konversi non-mp4
        subprocess.run(['ffmpeg', '-y', '-i', v_path, '-c:v', 'copy', '-c:a', 'aac', v_abs])

    # Proses Subtitle
    has_sub = False
    if s_path: # Jika upload manual
        subprocess.run(['ffmpeg', '-y', '-i', s_path, s_abs])
        has_sub = os.path.exists(s_abs)
    else: # Scan otomatis
        has_sub = extract_best_subtitle(v_abs, s_abs)

    shutil.copy(p_path, p_abs)

    # Simpan ke DB (Path Relatif untuk Browser)
    movie = {
        "id": movie_id,
        "title": judul, # Judul asli dengan spasi untuk tampilan
        "genre": genre,
        "synopsis": sinopsis,
        "video": f"movies/{v_name}", # Link video TANPA SPASI
        "poster": f"movies/{p_name}",
        "subtitle": f"movies/{s_name}" if has_sub else None
    }
    
    db = load_db()
    db.append(movie)
    save_db(db)
    return {"status": "success", "data": movie}

# --- LAIN-LAIN ---
@eel.expose
def delete_movie(movie_id):
    db = load_db()
    movie = next((m for m in db if m["id"] == movie_id), None)
    if movie:
        try:
            for k in ['video', 'poster', 'subtitle']:
                if movie[k]:
                    p = os.path.join(BASE_DIR, 'web', movie[k].replace('/', os.sep))
                    if os.path.exists(p): os.remove(p)
        except: pass
        db = [m for m in db if m["id"] != movie_id]
        save_db(db)
        return {"status": "success"}
    return {"status": "error"}

@eel.expose
def update_movie_data(movie_id, title, genre, synopsis):
    db = load_db()
    for m in db:
        if m['id'] == movie_id:
            m['title'] = title
            m['genre'] = genre
            m['synopsis'] = synopsis
            save_db(db)
            return {"status": "success"}
    return {"status": "error"}

@eel.expose
def open_file_dialog(type):
    root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
    path = filedialog.askopenfilename()
    root.destroy(); return path

def on_close(p, s):
    if not s: os._exit(0)

eel.start('index.html', size=(1280, 800), close_callback=on_close)