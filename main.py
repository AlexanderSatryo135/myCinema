import eel
import os
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog
import json
import re
import time 
import sys # Tambahan hanya untuk mendeteksi mode .exe

# --- PENYESUAIAN PATH UNTUK .EXE ---
if getattr(sys, 'frozen', False):
    # Jika berjalan sebagai .exe
    BASE_DIR = os.path.dirname(sys.executable)
    eel.init(os.path.join(sys._MEIPASS, 'web'))
else:
    # Jika berjalan sebagai .py biasa
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    eel.init('web')

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'web', 'movies')
DB_FILE = os.path.join(BASE_DIR, 'database.json')

# Pastikan folder ada
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Dapatkan Path Absolut Folder Project
ABS_UPLOAD_FOLDER = UPLOAD_FOLDER

# --- DATABASE HANDLER ---
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: return []
    return []

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)

def parse_time_to_seconds(time_str):
    try:
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    except: return 0

# --- EEL EXPOSED FUNCTIONS ---

@eel.expose
def get_all_movies():
    return load_db()

@eel.expose
def delete_movie(movie_id):
    db = load_db()
    movie = next((item for item in db if item["id"] == movie_id), None)
    
    if movie:
        print(f"Menghapus film: {movie['title']}...")
        try:
            # Hapus File di folder web/movies
            vid_path = os.path.join(ABS_UPLOAD_FOLDER, os.path.basename(movie['video']))
            if os.path.exists(vid_path): os.remove(vid_path)

            post_path = os.path.join(ABS_UPLOAD_FOLDER, os.path.basename(movie['poster']))
            if os.path.exists(post_path): os.remove(post_path)

            if movie['subtitle']:
                sub_path = os.path.join(ABS_UPLOAD_FOLDER, os.path.basename(movie['subtitle']))
                if os.path.exists(sub_path): os.remove(sub_path)
        except Exception as e:
            print(f"Error hapus file: {e}")

        # Hapus dari DB
        db = [item for item in db if item["id"] != movie_id]
        save_db(db)
        return {"status": "success", "msg": "Film dihapus dari library."}
    
    return {"status": "error", "msg": "Film tidak ditemukan."}

@eel.expose
def update_movie_data(movie_id, new_title, new_genre, new_synopsis):
    db = load_db()
    for movie in db:
        if movie['id'] == movie_id:
            movie['title'] = new_title
            movie['genre'] = new_genre
            movie['synopsis'] = new_synopsis
            save_db(db)
            return {"status": "success", "msg": "Data diupdate."}
    return {"status": "error", "msg": "Gagal update."}

@eel.expose
def open_file_dialog(file_type):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    path = ""
    if file_type == 'video':
        path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.mkv *.mov *.avi *.webm")])
    elif file_type == 'image':
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])
    elif file_type == 'sub':
        path = filedialog.askopenfilename(filetypes=[("Subtitle", "*.srt *.vtt *.ass")])
    
    root.destroy() # Membersihkan memori tkinter
    return path

@eel.expose
def process_upload(judul, genre, sinopsis, video_path, poster_path, sub_path):
    print(f"Memproses: {judul}...")
    
    # Gunakan timestamp agar ID unik dan file tidak tertabrak jika judul sama
    timestamp = str(int(time.time()))
    safe_name = "".join(x for x in judul if x.isalnum() or x in " -_").strip()
    movie_id = f"{timestamp}_{safe_name}"
    
    # Path Output
    final_video_name = f"{movie_id}.mp4"
    abs_video_out = os.path.join(ABS_UPLOAD_FOLDER, final_video_name)
    
    final_poster_name = f"{movie_id}_poster{os.path.splitext(poster_path)[1]}"
    abs_poster_out = os.path.join(ABS_UPLOAD_FOLDER, final_poster_name)
    
    final_sub_name = f"{movie_id}.vtt"
    abs_sub_out = os.path.join(ABS_UPLOAD_FOLDER, final_sub_name)

    # 1. PROSES VIDEO (SMART SCANNING)
    ext = os.path.splitext(video_path)[1].lower()
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    # KONDISI 1: Jika file MP4, gunakan HARD LINK (Hemat Storage 100%)
    if ext == '.mp4':
        print(f"File MP4 terdeteksi. Membuat Hard Link (Zero Storage)...")
        eel.update_progress_ui(50, "Scanning Video (Zero Storage)...")
        
        try:
            if os.path.exists(abs_video_out): os.remove(abs_video_out)
            try:
                os.link(video_path, abs_video_out)
                print("Hard Link Berhasil!")
            except OSError:
                shutil.copy(video_path, abs_video_out)
        except Exception as e:
            shutil.copy(video_path, abs_video_out)

    # KONDISI 2: Jika MKV/AVI, Harus Convert
    else:
        print(f"File {ext} terdeteksi. Wajib Convert ke MP4.")
        cmd = ['ffmpeg', '-y', '-i', video_path, '-c:v', 'copy', '-c:a', 'aac', abs_video_out]
        
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True, startupinfo=startupinfo)
        total_duration = None
        start_time = time.time() # Mulai hitung waktu awal
        
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None: break
            if line:
                if not total_duration:
                    m = re.search(r"Duration:\s(\d{2}:\d{2}:\d{2}\.\d+)", line)
                    if m: total_duration = parse_time_to_seconds(m.group(1))
                
                m_time = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d+)", line)
                if m_time and total_duration:
                    cur = parse_time_to_seconds(m_time.group(1))
                    pct = (cur / total_duration) * 100
                    
                    # --- LOGIKA PENGHITUNGAN ETA ---
                    elapsed_time = time.time() - start_time
                    if pct > 0:
                        # Rumus: (Waktu berjalan / Progres) * Progres Tersisa
                        remaining_time = (elapsed_time / (pct / 100)) - elapsed_time
                        minutes = int(remaining_time // 60)
                        seconds = int(remaining_time % 60)
                        eta_text = f"Sisa: {minutes}m {seconds}s"
                    else:
                        eta_text = "Menghitung..."
                    
                    # Kirim ke UI dengan Persentase + ETA
                    eel.update_progress_ui(pct, f"Convert: {int(pct)}% ({eta_text})")

        process.wait()

    # 2. PROSES SUBTITLE
    eel.update_progress_ui(95, "Cek Subtitle...")
    has_subtitle = False
    
    if sub_path:
        subprocess.run(['ffmpeg', '-y', '-i', sub_path, abs_sub_out], startupinfo=startupinfo)
        has_subtitle = True
    else:
        # Cari internal subtitle (Indo priority)
        for lang in ['ind', 'id', 'eng']:
            cmd_sub = ['ffmpeg', '-y', '-i', video_path, '-map', f'0:m:language:{lang}?', '-c:s', 'webvtt', abs_sub_out]
            res = subprocess.run(cmd_sub, startupinfo=startupinfo, stderr=subprocess.PIPE)
            if res.returncode == 0 and os.path.exists(abs_sub_out) and os.path.getsize(abs_sub_out) > 50:
                has_subtitle = True
                break

    # 3. PROSES POSTER
    shutil.copy(poster_path, abs_poster_out)

    # 4. SIMPAN DB
    new_movie = {
        "id": movie_id,
        "title": judul,
        "genre": genre,
        "synopsis": sinopsis,
        "video": f"movies/{final_video_name}",
        "poster": f"movies/{final_poster_name}",
        "subtitle": f"movies/{final_sub_name}" if has_subtitle else None
    }
    
    db = load_db()
    db.append(new_movie)
    save_db(db)
    
    eel.update_progress_ui(100, "Selesai!")
    return {"status": "success", "data": new_movie}

# Jalankan Eel
try:
    eel.start('index.html', mode='chrome', size=(1280, 800))
except:
    eel.start('index.html', mode='edge', size=(1280, 800))