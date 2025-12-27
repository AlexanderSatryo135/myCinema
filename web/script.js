let allMovies = [];
let activeMovie = null;

// DAFTAR GENRE
const GENRES = ["Action", "Adventure", "Drama", "Comedy", "Horror", "Sci-Fi", "Anime", "Football"];

// --- LOGIKA SAAT HALAMAN DI-LOAD ---
window.onload = async () => {
    // Muat data film dari Python
    allMovies = await eel.get_all_movies()();
    renderHome();

    // MUAT FOTO PROFIL DARI PENYIMPANAN PERMANEN (LocalStorage)
    const savedProfile = localStorage.getItem('userProfileImage');
    if (savedProfile) {
        const profileIcon = document.querySelector('.profile-icon');
        if (profileIcon) {
            profileIcon.style.backgroundImage = `url('${savedProfile}')`;
        }
    }
};

eel.expose(update_progress_ui);
function update_progress_ui(percent, text) {
    const progressBox = document.getElementById('progressBox');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    
    if (progressBox) progressBox.style.display = 'block';
    if (progressBar) progressBar.style.width = percent + "%";
    if (progressText) progressText.innerText = text || Math.floor(percent) + "%";
}

// --- LOGIKA RENDER UTAMA ---
function renderHome() {
    const mainArea = document.getElementById('mainContentArea');
    if (!mainArea) return; 
    mainArea.innerHTML = ""; 

    GENRES.forEach(genre => {
        const moviesInGenre = allMovies.filter(m => m.genre === genre);

        if (moviesInGenre.length > 0) {
            const section = document.createElement('section');
            section.className = 'row-section';
            
            const header = document.createElement('h2');
            header.className = 'row-header';
            header.innerText = genre;
            section.appendChild(header);

            const slider = document.createElement('div');
            slider.className = 'row-slider';

            moviesInGenre.forEach(movie => {
                slider.appendChild(createMovieCard(movie));
            });

            section.appendChild(slider);
            mainArea.appendChild(section);
        }
    });
}

function filterByGenre(genre) {
    const mainArea = document.getElementById('mainContentArea');
    if (!mainArea) return;
    mainArea.innerHTML = "";

    const movies = allMovies.filter(m => m.genre === genre);
    
    const section = document.createElement('section');
    section.className = 'row-section';
    
    const header = document.createElement('h2');
    header.className = 'row-header';
    header.innerText = genre;
    section.appendChild(header);

    const slider = document.createElement('div');
    slider.className = 'row-slider';

    if(movies.length === 0) {
        slider.innerHTML = "<p style='color:#777; padding:20px;'>Belum ada film di genre ini.</p>";
    } else {
        movies.forEach(movie => slider.appendChild(createMovieCard(movie)));
    }

    section.appendChild(slider);
    mainArea.appendChild(section);
}

function searchMovies(query) {
    query = query.toLowerCase();
    if (!query) {
        renderHome();
        return;
    }

    const mainArea = document.getElementById('mainContentArea');
    if (!mainArea) return;
    mainArea.innerHTML = "";
    
    const matchedMovies = allMovies.filter(m => m.title.toLowerCase().includes(query));

    const section = document.createElement('section');
    section.className = 'row-section';

    const header = document.createElement('h2');
    header.className = 'row-header';
    header.innerText = `Hasil Pencarian: "${query}"`;
    section.appendChild(header);

    const slider = document.createElement('div');
    slider.className = 'row-slider'; 

    if (matchedMovies.length === 0) {
        slider.innerHTML = "<p style='color:#777; padding:20px;'>Tidak ditemukan film.</p>";
    } else {
        matchedMovies.forEach(movie => slider.appendChild(createMovieCard(movie)));
    }

    section.appendChild(slider);
    mainArea.appendChild(section);
}

function createMovieCard(movie) {
    const card = document.createElement('div');
    card.className = 'movie-card';
    card.onclick = () => openPlayer(movie); 
    
    const img = document.createElement('img');
    img.src = movie.poster; 
    
    card.appendChild(img);
    return card;
}

// --- PLAYER & CONTROLS ---
function openPlayer(movie) {
    activeMovie = movie;
    document.getElementById('playerTitle').innerText = movie.title;
    document.getElementById('playerSynopsis').innerText = movie.synopsis;
    document.getElementById('textGenre').innerText = movie.genre || "General";
    
    const v = document.getElementById('mainVideoPlayer');
    const track = document.getElementById('playerSubtitle');
    v.src = movie.video;

    if (movie.subtitle) {
        track.src = movie.subtitle + "?t=" + new Date().getTime();
        track.track.mode = 'showing';
    } else {
        track.src = "";
        track.track.mode = 'hidden';
    }

    document.getElementById('playerOverlay').style.display = 'block';
    v.muted = false; 
    v.play().catch(e => { v.muted = true; v.play(); });
    updateMuteIcon();
}

function closePlayer() {
    const v = document.getElementById('mainVideoPlayer');
    v.pause(); v.src = "";
    document.getElementById('playerOverlay').style.display = 'none';
}

function playFullScreen() {
    const v = document.getElementById('mainVideoPlayer');
    v.muted = false; updateMuteIcon();
    if (v.requestFullscreen) v.requestFullscreen();
    v.play();
}

function togglePlay() {
    const v = document.getElementById('mainVideoPlayer');
    v.muted = false; updateMuteIcon();
    if (v.paused) v.play(); else v.pause();
}

function toggleMute() {
    const v = document.getElementById('mainVideoPlayer');
    v.muted = !v.muted;
    updateMuteIcon();
}

function updateMuteIcon() {
    const v = document.getElementById('mainVideoPlayer');
    const icon = document.querySelector('#btnMute i');
    if (v.muted) icon.className = 'fas fa-volume-mute';
    else icon.className = 'fas fa-volume-up';
}

function toggleSubtitle() {
    const track = document.getElementById('playerSubtitle').track;
    if (track.mode === 'showing') { track.mode = 'hidden'; alert("Subtitle OFF"); }
    else { track.mode = 'showing'; alert("Subtitle ON"); }
}

// --- UPLOAD & EDIT ---
function openEditModal() {
    if (!activeMovie) return;
    document.getElementById('editId').value = activeMovie.id;
    document.getElementById('editTitle').value = activeMovie.title;
    document.getElementById('editGenre').value = activeMovie.genre;
    document.getElementById('editSynopsis').value = activeMovie.synopsis;
    document.getElementById('editModal').style.display = 'flex';
}

function closeEditModal() { document.getElementById('editModal').style.display = 'none'; }

async function saveEdit() {
    const id = document.getElementById('editId').value;
    const title = document.getElementById('editTitle').value;
    const genre = document.getElementById('editGenre').value;
    const synopsis = document.getElementById('editSynopsis').value;
    
    let res = await eel.update_movie_data(id, title, genre, synopsis)();
    if (res.status === 'success') {
        alert("Update Berhasil!");
        activeMovie.title = title; activeMovie.genre = genre; activeMovie.synopsis = synopsis;
        document.getElementById('playerTitle').innerText = title;
        document.getElementById('playerSynopsis').innerText = synopsis;
        document.getElementById('textGenre').innerText = genre;
        closeEditModal();
        renderHome(); 
    }
}

async function deleteMovie() {
    if(!confirm("Hapus film ini?")) return;
    const id = document.getElementById('editId').value;
    let res = await eel.delete_movie(id)();
    if (res.status === 'success') {
        alert("Film Dihapus.");
        allMovies = allMovies.filter(m => m.id !== id);
        renderHome();
        closeEditModal();
        closePlayer();
    }
}

function openModal() { document.getElementById('uploadModal').style.display = 'flex'; }
function closeModal() { document.getElementById('uploadModal').style.display = 'none'; }

async function pickFile(type) {
    let path = await eel.open_file_dialog(type)();
    if(path) {
        if(type === 'video') document.getElementById('pathVideo').value = path;
        if(type === 'image') document.getElementById('pathPoster').value = path;
        if(type === 'sub') document.getElementById('pathSub').value = path;
    }
}

async function doUpload() {
    const title = document.getElementById('inTitle').value;
    const genre = document.getElementById('inGenre').value;
    const synopsis = document.getElementById('inSynopsis').value;
    const vPath = document.getElementById('pathVideo').value;
    const pPath = document.getElementById('pathPoster').value;
    const sPath = document.getElementById('pathSub').value;

    if(!title || !vPath || !pPath) { alert("Data kurang lengkap!"); return; }

    const btn = document.getElementById('btnUpload');
    btn.disabled = true;
    document.getElementById('progressBox').style.display = 'block';

    let result = await eel.process_upload(title, genre, synopsis, vPath, pPath, sPath)();

    if(result.status === 'success') {
        alert("Sukses!");
        allMovies.push(result.data);
        renderHome(); 
        closeModal();
        document.getElementById('uploadForm').reset();
    } else {
        alert("Error: " + result.msg);
    }
    btn.disabled = false;
    document.getElementById('progressBox').style.display = 'none';
}

// --- FUNGSI GANTI FOTO PROFIL (DIPERBARUI DENGAN LOCALSTORAGE) ---
function changeProfileImage(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const imageData = e.target.result;
            const profileIcon = document.querySelector('.profile-icon');
            
            // 1. Tampilkan di UI
            profileIcon.style.backgroundImage = `url('${imageData}')`;
            
            // 2. Simpan Permanen di Browser
            localStorage.setItem('userProfileImage', imageData);
        }
        reader.readAsDataURL(input.files[0]);
    }
}

// --- SEARCH BOX ANIMATION ---
function toggleSearchBox() {
    const box = document.getElementById('searchBox');
    if (!box) return;
    const input = box.querySelector('input');
    
    box.classList.toggle('active');
    
    if (box.classList.contains('active') && input) {
        input.focus();
    }
}