
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
        const response = await fetch(`/${window.currentLanguage || 'tamil'}/giveup-archive/?song_id=${window.songId || songId}`);
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
    console.log('Starting timer...');
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
        const submissionData = {
            guess: guessInput.value.trim(),
            spotify_id: guessInput.dataset.spotifyId,
            time_taken: timeTaken,
            song_id: window.songId || songId,
            play_date: window.playDate || playDate
        };

        console.log('Submitting guess with data:', submissionData);

        const response = await fetch(`/${window.currentLanguage || 'tamil'}/archive/submit/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify(submissionData)
        });

        const data = await response.json();
        console.log('Guess response:', data);

        if (data.correct) {
            showResults(data);
        } else {
            console.log('Wrong guess. Expected song details:', data);
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
            <a href="/${window.currentLanguage || 'tamil'}/archive" class="btn btn-warning fw-bold"><i class="fas fa-archive"></i> Archive</a>
            ${nextDate ? `<a href="?date=${nextDate}" class="btn btn-sm btn-outline-warning"><i class="fas fa-chevron-right"></i></a>` : `<span></span>`}
        </div>
    `;

    resultContainer.innerHTML = `
    <div class="reveal-animation">
        <div class="reveal-header mb-4">
            <h4 class="archive-score-message">
                If you had played on ${window.playDate || playDate}, you would've ranked #${result.rank}
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

        <div class="leaderboard-section">
            <button id="toggle-leaderboard" class="toggle-leaderboard-btn">
                <i class="fas fa-trophy"></i>
                <span>Show Leaderboard</span>
            </button>
            <div id="archive-leaderboard" class="archive-leaderboard" style="display: none;">
                <div class="leaderboard-loading">
                    <i class="fas fa-spinner fa-spin"></i> Loading leaderboard...
                </div>
            </div>
        </div>

        <div class="archive-navigation">
            <button id="prev-date-btn" class="nav-date-btn">
                <i class="fas fa-chevron-left"></i>
                <span>Previous Day</span>
            </button>
            <button id="next-date-btn" class="nav-date-btn">
                <i class="fas fa-chevron-right"></i>
                <span>Next Day</span>
            </button>
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

    // Add leaderboard toggle functionality
    setupLeaderboardToggle(result);

    // Add navigation functionality
    console.log('Setting up archive navigation...');
    setupArchiveNavigation();
}

function setupLeaderboardToggle(result) {
    const toggleBtn = document.getElementById('toggle-leaderboard');
    const leaderboardDiv = document.getElementById('archive-leaderboard');
    let isLeaderboardLoaded = false;

    toggleBtn.addEventListener('click', async () => {
        const isVisible = leaderboardDiv.style.display !== 'none';

        if (isVisible) {
            // Hide leaderboard
            leaderboardDiv.style.display = 'none';
            toggleBtn.innerHTML = '<i class="fas fa-trophy"></i><span>Show Leaderboard</span>';
        } else {
            // Show leaderboard
            leaderboardDiv.style.display = 'block';
            toggleBtn.innerHTML = '<i class="fas fa-trophy"></i><span>Hide Leaderboard</span>';

            // Load leaderboard if not already loaded
            if (!isLeaderboardLoaded) {
                await loadArchiveLeaderboard(result);
                isLeaderboardLoaded = true;
            }
        }
    });
}

async function loadArchiveLeaderboard(result) {
    const leaderboardDiv = document.getElementById('archive-leaderboard');

    try {
        // Ensure date is in YYYY-MM-DD format
        const currentPlayDate = window.playDate || playDate;
        let formattedDate = currentPlayDate;
        if (currentPlayDate && !currentPlayDate.match(/^\d{4}-\d{2}-\d{2}$/)) {
            // If playDate is not in YYYY-MM-DD format, try to convert it
            const date = new Date(currentPlayDate);
            if (!isNaN(date.getTime())) {
                formattedDate = date.toISOString().split('T')[0];
            }
        }

        const url = `/${window.currentLanguage || 'tamil'}/archive-leaderboard/?` +
            `date=${formattedDate}&user_rank=${result.rank}&user_points=${result.points}&user_time=${result.time_taken}`;

        console.log('Loading leaderboard from:', url);
        console.log('Original playDate:', playDate);
        console.log('Formatted date:', formattedDate);
        console.log('Parameters:', { formattedDate, rank: result.rank, points: result.points, time: result.time_taken });

        const response = await fetch(url);
        const data = await response.json();

        console.log('Leaderboard response:', data);

        if (data.success) {
            displayLeaderboard(data.leaderboard, data.date);
        } else {
            console.error('Leaderboard error:', data.error);
            leaderboardDiv.innerHTML = `<div class="leaderboard-error">Failed to load leaderboard: ${data.error || 'Unknown error'}</div>`;
        }
    } catch (error) {
        console.error('Error loading leaderboard:', error);
        leaderboardDiv.innerHTML = '<div class="leaderboard-error">Error loading leaderboard</div>';
    }
}

function displayLeaderboard(leaderboard, date) {
    const leaderboardDiv = document.getElementById('archive-leaderboard');

    let html = `
        <div class="leaderboard-header">
            <h5><i class="fas fa-calendar-alt"></i> ${new Date(date).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            })}</h5>
        </div>
        <div class="leaderboard-list">
    `;

    leaderboard.forEach(entry => {
        const isHypothetical = entry.is_hypothetical;
        const rowClass = isHypothetical ? 'leaderboard-row hypothetical-entry' : 'leaderboard-row';

        html += `
            <div class="${rowClass}">
                <div class="rank-col">#${entry.rank}</div>
                <div class="username-col">${entry.username}</div>
                <div class="score-col">${entry.score}pts</div>
                <div class="time-col">${entry.time.toFixed(1)}s</div>
            </div>
        `;
    });

    html += '</div>';
    leaderboardDiv.innerHTML = html;
}

async function setupArchiveNavigation() {
    console.log('setupArchiveNavigation called');
    const prevBtn = document.getElementById('prev-date-btn');
    const nextBtn = document.getElementById('next-date-btn');

    console.log('Navigation buttons found:', { prevBtn, nextBtn });
    if (!prevBtn || !nextBtn) {
        console.log('Navigation buttons not found, exiting');
        return;
    }

    try {
        // Get proper previous and next dates from backend
        const response = await fetch(`/${window.currentLanguage || 'tamil'}/archive-navigation/?date=${window.playDate || playDate}`);
        const data = await response.json();

        console.log('Navigation data:', data);

        if (data.success) {
            // Update button text and functionality
            if (data.prev_date) {
                prevBtn.innerHTML = `<i class="fas fa-chevron-left"></i><span>${data.prev_display}</span>`;
                prevBtn.disabled = false;
                prevBtn.classList.remove('disabled');
                prevBtn.onclick = () => loadArchiveDate(data.prev_date);
            } else {
                prevBtn.innerHTML = `<i class="fas fa-chevron-left"></i><span>No Earlier</span>`;
                prevBtn.disabled = true;
                prevBtn.classList.add('disabled');
            }

            if (data.next_date) {
                nextBtn.innerHTML = `<i class="fas fa-chevron-right"></i><span>${data.next_display}</span>`;
                nextBtn.disabled = false;
                nextBtn.classList.remove('disabled');
                nextBtn.onclick = () => loadArchiveDate(data.next_date);
            } else {
                nextBtn.innerHTML = `<i class="fas fa-chevron-right"></i><span>No Later</span>`;
                nextBtn.disabled = true;
                nextBtn.classList.add('disabled');
            }
        } else {
            console.error('Failed to get navigation data:', data.error);
            // Disable both buttons on error
            prevBtn.disabled = true;
            nextBtn.disabled = true;
            prevBtn.classList.add('disabled');
            nextBtn.classList.add('disabled');
        }
    } catch (error) {
        console.error('Error setting up navigation:', error);
        // Disable both buttons on error
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        prevBtn.classList.add('disabled');
        nextBtn.classList.add('disabled');
    }
}

async function loadArchiveDate(dateStr) {
    try {
        console.log('Loading archive date:', dateStr);

        // STOP ALL AUDIO IMMEDIATELY
        const snippet = document.getElementById('song-snippet');
        const revealAudio = document.getElementById('reveal-snippet');

        if (snippet) {
            snippet.pause();
            snippet.currentTime = 0;
        }
        if (revealAudio) {
            revealAudio.pause();
            revealAudio.currentTime = 0;
        }

        // Stop any playing audio globally
        document.querySelectorAll('audio').forEach(audio => {
            audio.pause();
            audio.currentTime = 0;
        });

        // Clear any timers - use global variables
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
        startTime = null;
        isTimerRunning = false;

        // Show loading state
        const gameView = document.getElementById('game-view');
        const resultContainer = document.getElementById('result-container');

        gameView.style.display = 'block';
        resultContainer.style.display = 'none';

        // Reset ALL game state with null checks
        const guessInput = document.getElementById('guess-input');
        const timer = document.getElementById('timer');

        if (guessInput) guessInput.value = '';
        if (timer) timer.textContent = '00:00';

        // Reset timer state completely
        startTime = null;
        isTimerRunning = false;

        // Reset play button
        const playBtn = document.getElementById('playPauseBtn');
        if (playBtn) {
            playBtn.innerHTML = '<i class="fas fa-play"></i> Play';
            playBtn.classList.remove('playing');
        }

        // Load new song
        const response = await fetch(`/${window.currentLanguage || 'tamil'}/load-archive-song?date=${dateStr}`);
        const data = await response.json();

        console.log('Load response:', data);

        if (!data.success) {
            alert(data.message);
            return;
        }

        // Update song details with null checks
        const titleEl = document.getElementById('song-title');
        const artistEl = document.getElementById('song-artist');
        const movieEl = document.getElementById('song-movie');
        const imageEl = document.getElementById('song-image');

        if (titleEl) titleEl.textContent = data.title;
        if (artistEl) artistEl.textContent = data.artist;
        if (movieEl) movieEl.textContent = data.movie;
        if (imageEl) imageEl.src = data.image;

        // Update audio sources and reset
        snippet.src = data.snippet_url;
        snippet.load();
        snippet.pause(); // Ensure it's paused

        if (revealAudio) {
            revealAudio.src = data.reveal_audio_url;
            revealAudio.load();
            revealAudio.pause(); // Ensure it's paused
        }

        // Update global variables
        window.songId = data.db_song_id;  // Use database ID for submissions
        window.spotifyId = data.song_id;  // Keep Spotify ID for other uses
        window.revealSnippet = data.reveal_audio_url;
        window.playDate = dateStr;

        console.log('Updated song data:');
        console.log('- Database ID (songId):', window.songId);
        console.log('- Spotify ID:', window.spotifyId);
        console.log('- Play Date:', window.playDate);
        console.log('- Song Title:', data.title);
        console.log('- Song Artist:', data.artist);

        // Update URL without page reload
        const newUrl = `/${window.currentLanguage || 'tamil'}/archive/?date=${dateStr}`;
        window.history.pushState({date: dateStr}, '', newUrl);

        // Update date display in header
        const dateDisplay = document.querySelector('.archive-date-badge');
        if (dateDisplay) {
            const displayDate = new Date(dateStr).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            dateDisplay.innerHTML = `<i class="fas fa-calendar-alt"></i> ${displayDate}`;
        }

        // Update date input if it exists
        const dateInput = document.getElementById('archive-date');
        if (dateInput) {
            dateInput.value = dateStr;
        }

        console.log('Successfully loaded new date:', dateStr);

    } catch (error) {
        console.error('Error loading archive date:', error);
        alert('Failed to load song for this date. Please try again.');
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
            const response = await fetch(`/${window.currentLanguage || 'tamil'}/load-archive-song?date=${selectedDate}`);
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
            window.songId = data.db_song_id;  // Use database ID for submissions
            window.spotifyId = data.song_id;  // Keep Spotify ID for other uses
            window.revealSnippet = data.reveal_audio_url;
            window.playDate = selectedDate;
        } catch (err) {
            console.error('Error loading archive song:', err);
            alert('Failed to load song. Try again later.');
        }
    });
});

