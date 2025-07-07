
let startTime = null;
let timerInterval;
let isTimerRunning = false;
let accessToken = null;

// Make sure DOM is loaded before initializing
document.addEventListener('DOMContentLoaded', function () {
    const audio = document.getElementById('song-snippet');
    audio.load();
    setupGameControls();
    getSpotifyToken();
});

function setupGameControls() {
    const audio = document.getElementById('song-snippet');
    const playPauseBtn = document.getElementById('playPauseBtn');
    const guessForm = document.getElementById('guess-form');
    const giveUpBtn = document.getElementById('giveUpBtn');

    playPauseBtn.addEventListener('click', () => {
        if (audio.paused) {
            audio.currentTime = 0;
            audio.volume = 1.0;
            audio.play().then(() => {
                playPauseBtn.innerHTML = '<i class="fas fa-pause"></i> Pause';
                if (!isTimerRunning) startTimer();
            });
        } else {
            audio.pause();
            playPauseBtn.innerHTML = '<i class="fas fa-play"></i> Play';
        }
    });

    audio.addEventListener('timeupdate', () => {
        const progress = (audio.currentTime / audio.duration) * 100;
        document.querySelector('.progress-fill').style.width = `${progress}%`;
    });

    guessForm.addEventListener('submit', handleGuess);

    giveUpBtn.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to give up? You can still try this archive song later!')) return;

    audio.pause();
    clearInterval(timerInterval);

    try {
        const response = await fetch(`/giveup-archive/?song_id=${songId}`);
        const data = await response.json();

        if (data.error) throw new Error(data.error);

        showResults({
            song_title: data.song_title,
            movie: data.movie,
            artist: data.artist,
            image: data.image,
            points: data.points,
            rank: data.rank,
            time_taken: data.time_taken
        });

    } catch (error) {
        console.error('Give up error:', error);
        alert('Something went wrong while processing give up.');
    }
});


}

function startTimer() {
    startTime = Date.now();
    isTimerRunning = true;
    timerInterval = setInterval(updateTimer, 100);
}

function updateTimer() {
    const elapsedTime = (Date.now() - startTime) / 1000;
    const minutes = Math.floor(elapsedTime / 60);
    const seconds = Math.floor(elapsedTime % 60);
    document.getElementById('timer').textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    updatePointsIndicator(elapsedTime);
}

function updatePointsIndicator(elapsedTime) {
    const pointsValue = document.querySelector('.points-value');
    let points;
    if (elapsedTime <= 10) points = 8;
    else if (elapsedTime <= 20) points = 5;
    else if (elapsedTime <= 30) points = 4;
    else if (elapsedTime <= 45) points = 3;
    else if (elapsedTime <= 60) points = 2;
    else points = 1;

    if (pointsValue.textContent != points) {
        pointsValue.textContent = points;
        pointsValue.classList.remove('points-change');
        void pointsValue.offsetWidth;
        pointsValue.classList.add('points-change');
    }
}

async function handleGuess(e) {
    e.preventDefault();
    const guessInput = document.getElementById('guess-input');
    const timeTaken = (Date.now() - startTime) / 1000;

    if (!guessInput.value.trim()) return alert('Enter a guess!');

    try {
        const response = await fetch('/archive/submit/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                guess: guessInput.value.trim(),
                spotify_id: guessInput.dataset.spotifyId,
                time_taken: timeTaken,
                song_id: songId,
                play_date: playDate
            })
        });

        const data = await response.json();
        if (data.correct) {
            showResults(data);
        } else {
            alert(data.message || 'Wrong guess!');
        }
    } catch (err) {
        console.error(err);
        alert('Something went wrong. Try again.');
    }
}

async function getSpotifyToken() {
    try {
        const res = await fetch('https://accounts.spotify.com/api/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': 'Basic ' + btoa('f7d61e92fbfa47ba825b91d382c21bb8:3c18c9e7addf406a8b20ba92ea13d0e4')
            },
            body: 'grant_type=client_credentials'
        });
        const data = await res.json();
        accessToken = data.access_token;
    } catch (err) {
        console.error('Spotify token error', err);
    }
}

const guessInput = document.getElementById('guess-input');
guessInput.addEventListener('input', function () {
    clearTimeout(this.debounceTimer);
    const q = this.value;
    this.debounceTimer = setTimeout(() => fetchSuggestions(q), 200);
});

async function fetchSuggestions(query) {
    if (!query || query.length < 2) return document.getElementById('suggestions').style.display = 'none';

    try {
        const res = await fetch(`https://api.spotify.com/v1/search?q=${encodeURIComponent(query)}&type=track&limit=10`, {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        const data = await res.json();
        const container = document.getElementById('suggestions');
        container.innerHTML = '';

        data.tracks.items.forEach(track => {
            const div = document.createElement('div');
            div.className = 'suggestion-item';
            div.innerHTML = `
                <img src="${track.album.images[0].url}" />
                <div class="suggestion-info">
                    <div class="suggestion-title">${track.name}</div>
                    <div class="suggestion-artist">${track.artists[0].name}</div>
                </div>`;
            div.onclick = () => {
                guessInput.value = track.name;
                guessInput.dataset.spotifyId = track.id;
                container.style.display = 'none';
            };
            container.appendChild(div);
        });
        container.style.display = 'block';
    } catch (err) {
        console.error('Suggestion error', err);
    }
}

function showResults(result) {
    const resultContainer = document.getElementById('result-container');
    const gameView = document.getElementById('game-view');
    const audio = document.getElementById('song-snippet');

    audio.pause();
    clearInterval(timerInterval);

    // Construct Previous and Next URLs based on current date
    const urlParams = new URLSearchParams(window.location.search);
    const currentDate = urlParams.get('date');

    let prevDate = result.prev_date || null;
    let nextDate = result.next_date || null;

    let arrowsHTML = `
        <div class="d-flex justify-content-between align-items-center mt-4 mb-2">
            ${prevDate ? `<a href="?date=${prevDate}" class="btn btn-sm btn-outline-warning"><i class="fas fa-chevron-left"></i></a>` : `<span></span>`}
            <a href="/archive" class="btn btn-warning fw-bold"><i class="fas fa-archive"></i> Archive</a>
            ${nextDate ? `<a href="?date=${nextDate}" class="btn btn-sm btn-outline-warning"><i class="fas fa-chevron-right"></i></a>` : `<span></span>`}
        </div>
    `;

    resultContainer.innerHTML = `
    <div class="reveal-animation">
        <div class="reveal-header mb-4">
            <h4 class="archive-score-message">
                If you had played on ${playDate}, you would've ranked #${result.rank}
            </h4>
        </div>

        <div class="song-details-container">
            ${result.image ? `<img src="${result.image}" alt="${result.song_title}" class="song-image">` : ''}
            <div class="song-details">
                <div class="song-title">${result.song_title}</div>
                <div class="song-info">${result.movie}</div>
                <div class="song-info">${result.artist}</div>
            </div>
        </div>

        <div class="archive-stats">
            <div class="rank-display">
                <div class="rank-number">#${result.rank}</div>
                <div class="rank-text">Your hypothetical rank</div>
            </div>

            <div class="stats-grid">
                <div class="stat-item">
                    <i class="fas fa-clock"></i>
                    <span>${result.time_taken.toFixed(1)}s</span>
                </div>
                <div class="stat-item">
                    <i class="fas fa-trophy"></i>
                    <span>${result.points} points</span>
                </div>
            </div>
        </div>

        ${arrowsHTML}
    </div>`;

    gameView.style.display = 'none';
    resultContainer.style.display = 'block';

    const revealAudio = document.getElementById('reveal-snippet');
    if (revealAudio) {
        revealAudio.volume = 0.8;
        revealAudio.play().catch(() => {});
    }
}


// Make togglePlay globally available for HTML onclick
window.togglePlay = function () {
    document.getElementById('playPauseBtn').click();
};


document.addEventListener('DOMContentLoaded', function () {
    const archiveDateInput = document.getElementById('archive-date');
    if (!archiveDateInput) return;

    archiveDateInput.addEventListener('change', async function () {
        const selectedDate = this.value;
        if (!selectedDate) return;

        try {
            const response = await fetch(`/load-archive-song?date=${selectedDate}`);
            const data = await response.json();

            if (!data.success) {
                alert(data.message);  // ⛔ Handles: Today’s song & Early dates
                return;
            }

            // ✅ Populate and play the song
            document.getElementById('song-title').textContent = data.title;
            document.getElementById('song-artist').textContent = data.artist;
            document.getElementById('song-movie').textContent = data.movie;
            document.getElementById('song-image').src = data.image;

            const snippet = document.getElementById('song-snippet');
            snippet.src = data.snippet_url;
            snippet.load();

            // Global vars for guess and reveal
            window.songId = data.song_id;
            window.revealSnippet = data.reveal_audio_url;
            window.playDate = selectedDate;
        } catch (err) {
            console.error('Error loading archive song:', err);
            alert('Failed to load song. Try again later.');
        }
    });
});

