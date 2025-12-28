let allMovies = [];
let activeMovie = null;

const GENRES = [
  "Action",
  "Adventure",
  "Drama",
  "Comedy",
  "Horror",
  "Sci-Fi",
  "Anime",
  "Football",
];

// --- LOGIKA SAAT HALAMAN DI-LOAD ---
window.onload = async () => {
  allMovies = await eel.get_all_movies()();
  renderHome();
  const savedProfile = localStorage.getItem("userProfileImage");
  if (savedProfile) {
    const profileIcon = document.querySelector(".profile-icon");
    if (profileIcon)
      profileIcon.style.backgroundImage = `url('${savedProfile}')`;
  }
};

eel.expose(update_progress_ui);
function update_progress_ui(percent, text) {
  const progressBox = document.getElementById("progressBox");
  const progressBar = document.getElementById("progressBar");
  const progressText = document.getElementById("progressText");
  if (progressBox) progressBox.style.display = "block";
  if (progressBar) progressBar.style.width = percent + "%";
  if (progressText) progressText.innerText = text || Math.floor(percent) + "%";
}

// --- LOGIKA RENDER UTAMA ---
function renderHome() {
  const mainArea = document.getElementById("mainContentArea");
  if (!mainArea) return;
  mainArea.innerHTML = "";
  GENRES.forEach((genre) => {
    const moviesInGenre = allMovies.filter((m) => m.genre === genre);
    if (moviesInGenre.length > 0) {
      const section = document.createElement("section");
      section.className = "row-section";
      const header = document.createElement("h2");
      header.className = "row-header";
      header.innerText = genre;
      section.appendChild(header);
      const slider = document.createElement("div");
      slider.className = "row-slider";
      moviesInGenre.forEach((movie) =>
        slider.appendChild(createMovieCard(movie))
      );
      section.appendChild(slider);
      mainArea.appendChild(section);
    }
  });
}

function createMovieCard(movie) {
  const card = document.createElement("div");
  card.className = "movie-card";
  card.onclick = () => openPlayer(movie);
  const img = document.createElement("img");
  img.src = movie.poster;
  card.appendChild(img);
  return card;
}

// --- PERBAIKAN PLAYER (JUDUL, SINOPSIS, & PLAYBACK) ---
function openPlayer(movie) {
  activeMovie = movie;

  // 1. Update Data Teks ke Modal agar tidak kosong
  document.getElementById("playerTitle").innerText =
    movie.title || "Judul Tidak Tersedia";
  document.getElementById("playerSynopsis").innerText =
    movie.synopsis || "Sinopsis tidak ditemukan.";
  document.getElementById("textGenre").innerText = movie.genre || "General";

  const v = document.getElementById("mainVideoPlayer");
  const track = document.getElementById("playerSubtitle");

  // 2. Set Sumber Video dan Paksa Load agar bisa diputar
  v.src = movie.video;
  v.load();

  // 3. Reset dan muat subtitle dengan timestamp anti-cache
  if (movie.subtitle) {
    track.src = movie.subtitle + "?t=" + new Date().getTime();
    track.track.mode = "showing";
  } else {
    track.src = "";
    track.track.mode = "hidden";
  }

  // 4. Tampilkan Overlay Modal
  document.getElementById("playerOverlay").style.display = "block";

  // 5. Jalankan Video (Handle kebijakan Autoplay browser)
  v.play().catch(() => {
    console.log("Autoplay dicegah, mencoba mode muted...");
    v.muted = true;
    v.play();
  });
}

function closePlayer() {
  const v = document.getElementById("mainVideoPlayer");
  v.pause();
  v.src = "";
  document.getElementById("playerOverlay").style.display = "none";
}

// --- FUNGSI SCAN ULANG SUBTITLE ---
async function rescanSpecificSub() {
  if (!activeMovie || !activeMovie.id) return;
  const btn = document.getElementById("btnRescanSub");
  const originalText = btn.innerText;
  btn.innerText = "Scanning... ⏳";
  btn.disabled = true;
  try {
    const result = await eel.rescan_single_movie_subtitle(activeMovie.id)();
    alert(result);
    allMovies = await eel.get_all_movies()();
    renderHome();
    const track = document.getElementById("playerSubtitle");
    const updated = allMovies.find((m) => m.id === activeMovie.id);
    if (updated && updated.subtitle) {
      track.src = updated.subtitle + "?t=" + new Date().getTime();
      track.track.mode = "showing";
      activeMovie.subtitle = updated.subtitle;
    }
  } catch (e) {
    alert("Gagal koneksi Python.");
  } finally {
    btn.innerText = originalText;
    btn.disabled = false;
  }
}

// --- SEARCH BOX ---
function toggleSearchBox() {
  const box = document.getElementById("searchBox");
  const input = box.querySelector("input");
  box.classList.toggle("active");
  if (box.classList.contains("active") && input) input.focus();
}

function searchMovies(q) {
  q = q.toLowerCase();
  if (!q) {
    renderHome();
    return;
  }
  const mainArea = document.getElementById("mainContentArea");
  mainArea.innerHTML = `<section class="row-section"><h2 class="row-header">Hasil: "${q}"</h2><div class="row-slider" id="searchResult"></div></section>`;
  const container = document.getElementById("searchResult");
  const matches = allMovies.filter((m) => m.title.toLowerCase().includes(q));
  if (matches.length === 0)
    container.innerHTML = "<p style='color:#777;'>Tidak ada hasil.</p>";
  else matches.forEach((m) => container.appendChild(createMovieCard(m)));
}

// --- EDIT & DELETE ---
function openEditModal() {
  if (!activeMovie) return;
  document.getElementById("editId").value = activeMovie.id;
  document.getElementById("editTitle").value = activeMovie.title;
  document.getElementById("editGenre").value = activeMovie.genre;
  document.getElementById("editSynopsis").value = activeMovie.synopsis;
  document.getElementById("editModal").style.display = "flex";
}

function closeEditModal() {
  document.getElementById("editModal").style.display = "none";
}

async function saveEdit() {
  const id = document.getElementById("editId").value;
  const title = document.getElementById("editTitle").value;
  const genre = document.getElementById("editGenre").value;
  const synopsis = document.getElementById("editSynopsis").value;
  let res = await eel.update_movie_data(id, title, genre, synopsis)();
  if (res.status === "success") {
    alert("Berhasil!");
    allMovies = await eel.get_all_movies()();
    renderHome();
    closeEditModal();
  }
}

async function deleteMovie() {
  if (!confirm("Hapus?")) return;
  let res = await eel.delete_movie(activeMovie.id)();
  if (res.status === "success") {
    allMovies = allMovies.filter((m) => m.id !== activeMovie.id);
    renderHome();
    closeEditModal();
    closePlayer();
  }
}

// --- UPLOAD ---
function openModal() {
  document.getElementById("uploadModal").style.display = "flex";
}
function closeModal() {
  document.getElementById("uploadModal").style.display = "none";
}

async function pickFile(type) {
  let p = await eel.open_file_dialog(type)();
  if (p) {
    if (type === "video") document.getElementById("pathVideo").value = p;
    if (type === "image") document.getElementById("pathPoster").value = p;
    if (type === "sub") document.getElementById("pathSub").value = p;
  }
}

async function doUpload() {
  const t = document.getElementById("inTitle").value;
  const g = document.getElementById("inGenre").value;
  const s = document.getElementById("inSynopsis").value;
  const v = document.getElementById("pathVideo").value;
  const p = document.getElementById("pathPoster").value;
  const sb = document.getElementById("pathSub").value;
  if (!t || !v || !p) {
    alert("Data tidak lengkap!");
    return;
  }
  document.getElementById("btnUpload").disabled = true;
  let res = await eel.process_upload(t, g, s, v, p, sb)();
  if (res.status === "success") {
    allMovies.push(res.data);
    renderHome();
    closeModal();
  }
  document.getElementById("btnUpload").disabled = false;
}
