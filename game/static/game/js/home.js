let startTime = null;
let timerInterval;
let isTimerRunning = false;
let accessToken = '';
let audioContext, analyser, source;

document.addEventListener('DOMContentLoaded', function () {
    const audioElement = document.getElementById('song-snippet');
    const playPauseBtn = document.getElementById('playPauseBtn');
    const vinylPlayer = document.querySelector('.vinyl-player');
    const giveUpBtn = document.getElementById('giveUpBtn');

    function initAudioContext() {
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioContext.createAnalyser();
        }
    }

    // Play/Pause functionality
    if (playPauseBtn) {
        playPauseBtn.addEventListener('click', () => {
            initAudioContext();

            if (audioElement.paused) {
                if (!source) {
                    source = audioContext.createMediaElementSource(audioElement);
                    source.connect(analyser);
                    analyser.connect(audioContext.destination);
                }

                audioElement.play();
                vinylPlayer?.classList.add('playing');
                vinylPlayer?.classList.remove('paused');
                playPauseBtn.innerHTML = '<i class="fas fa-pause"></i> Pause';
                document.getElementById('vinyl-play-icon').className = 'fas fa-pause';
                startTimer();
            } else {
                audioElement.pause();
                vinylPlayer?.classList.remove('playing');
                vinylPlayer?.classList.add('paused');
                playPauseBtn.innerHTML = '<i class="fas fa-play"></i> Play';
                document.getElementById('vinyl-play-icon').className = 'fas fa-play';
            }
        });
    }

    window.togglePlay = function () {
        playPauseBtn?.click();
    };

    // Give Up
    if (giveUpBtn) {
        giveUpBtn.addEventListener('click', async () => {
            if (confirm('Are you sure you want to give up? You will receive 0 points for today.')) {
                try {
                    const response = await fetch('/give-up/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                        }
                    });

                    if (response.ok) {
                        const data = await response.json();

                        audioElement.pause();
                        document.querySelector('.points-value').textContent = '0';
                        window.isGaveUp = true;
                        showResultView();
                        clearInterval(timerInterval);
                        localStorage.removeItem('songTimer');
                    }
                } catch (error) {
                    console.error('Error:', error);
                }
            }
        });
    }

    // Initialize timer on page load
    const timerWasRunning = initializeTimer();
    if (audioElement && !timerWasRunning) {
        audioElement.addEventListener('play', startTimer, { once: true });
    }

    document.addEventListener('visibilitychange', () => {
        if (!document.hidden && isTimerRunning) {
            clearInterval(timerInterval);
            timerInterval = setInterval(updateTimer, 100);
        }
    });

    // Guess Form Submission
    document.getElementById('guess-form')?.addEventListener('submit', async function (e) {
        e.preventDefault();
        const timeTaken = stopTimer();
        const guessInput = document.getElementById('guess-input');
        const resultMessage = document.getElementById('result-message');

        if (!guessInput.value.trim()) {
            resultMessage.innerHTML = '<div class="alert alert-danger">Please enter a guess!</div>';
            return;
        }

        try {
            const response = await fetch('', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    guess: guessInput.value.trim(),
                    spotify_id: guessInput.dataset.spotifyId,
                    time_taken: timeTaken
                })
            });

            const data = await response.json();

            if (data.correct) {
                resultMessage.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                showResultView();
                document.getElementById('song-snippet').pause();
                clearInterval(timerInterval);
                localStorage.removeItem('songTimer');
            } else {
                resultMessage.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
                isTimerRunning = true;
                timerInterval = setInterval(updateTimer, 100);
            }
        } catch (error) {
            console.error('Error:', error);
            resultMessage.innerHTML = '<div class="alert alert-danger">An error occurred. Please try again.</div>';
        }
    });

    // Spotify Autocomplete
    async function getSpotifyToken() {
        const clientId = 'f7d61e92fbfa47ba825b91d382c21bb8';
        const clientSecret = '3c18c9e7addf406a8b20ba92ea13d0e4';

        try {
            const response = await fetch('https://accounts.spotify.com/api/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': 'Basic ' + btoa(clientId + ':' + clientSecret)
                },
                body: 'grant_type=client_credentials'
            });

            const data = await response.json();
            accessToken = data.access_token;
        } catch (error) {
            console.error('Error getting Spotify token:', error);
        }
    }

    async function searchSpotify(query) {
        if (!query) return [];
        try {
            const response = await fetch(`https://api.spotify.com/v1/search?q=${encodeURIComponent(query)}&type=track&market=IN&limit=20`, {
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });
            const data = await response.json();
            return data.tracks.items || [];
        } catch (error) {
            console.error('Spotify search error:', error);
            return [];
        }
    }

    // Autocomplete Suggestions
    const guessInputField = document.getElementById('guess-input');
    let debounceTimeout;

    if (guessInputField) {
        guessInputField.addEventListener('input', function (e) {
            clearTimeout(debounceTimeout);
            const query = e.target.value;

            debounceTimeout = setTimeout(async () => {
                const suggestionsContainer = document.getElementById('suggestions');
                if (query.length < 2) {
                    suggestionsContainer.style.display = 'none';
                    return;
                }

                const tracks = await searchSpotify(query);
                if (tracks.length > 0) {
                    suggestionsContainer.innerHTML = tracks.map(track => `
                        <div class="suggestion-item" data-song-name="${encodeURIComponent(track.name)}" data-spotify-id="${track.id}">
                            <img src="${track.album.images.at(-1)?.url}" alt="${track.name}">
                            <div class="suggestion-info">
                                <div class="suggestion-title">${track.name}</div>
                                <div class="suggestion-artist">${track.artists[0].name}</div>
                            </div>
                        </div>
                    `).join('');
                    suggestionsContainer.style.display = 'block';
                } else {
                    suggestionsContainer.style.display = 'none';
                }
            }, 150);
        });

        // Select a suggestion
        document.getElementById('suggestions')?.addEventListener('click', function (e) {
            const item = e.target.closest('.suggestion-item');
            if (!item) return;

            const songName = decodeURIComponent(item.dataset.songName);
            const spotifyId = item.dataset.spotifyId;

            guessInputField.value = songName;
            guessInputField.dataset.spotifyId = spotifyId;
            document.getElementById('suggestions').style.display = 'none';
        });
    }

    // Hide suggestions on outside click
    document.addEventListener('click', function (e) {
        if (!e.target.closest('#guess-input') && !e.target.closest('#suggestions')) {
            document.getElementById('suggestions')?.style?.setProperty('display', 'none');
        }
    });

    // 🟣 Leaderboard toggle listener fix
    function toggleLeaderboard(e) {
        const toggle = e.currentTarget;
        const content = toggle.parentElement.querySelector('#leaderboard-content');
        const chevron = toggle.querySelector('i');

        if (!content || !chevron) return;

        if (content.style.display === 'none' || content.style.display === '') {
            content.style.display = 'block';
            void content.offsetHeight;
            chevron.style.transform = 'rotate(180deg)';
            content.style.opacity = '1';
            content.style.maxHeight = content.scrollHeight + 'px';
        } else {
            chevron.style.transform = 'rotate(0deg)';
            content.style.opacity = '0';
            content.style.maxHeight = '0';
            setTimeout(() => {
                content.style.display = 'none';
            }, 300);
        }

        console.log('🟣 Toggle leaderboard clicked');
    }

    // Attach listener AFTER leaderboard injected dynamically
    setTimeout(() => {
        document.querySelectorAll('.leaderboard-toggle').forEach(toggle => {
            toggle.removeEventListener('click', toggleLeaderboard); // clear old
            toggle.addEventListener('click', toggleLeaderboard);    // add fresh
        });
    }, 500);

    // Load Spotify token initially
    getSpotifyToken();
});

    // 📤 SHARE FUNCTIONS
    function getShareText() {
        const score = document.querySelector('.points-value')?.textContent || '';
        const rank = document.querySelector('.leaderboard-header span')?.textContent?.replace('Your Rank: #', '') || '';
        return `🎵 SPOT-ify the Paatu\n🎯 Score: ${score} points\n🏆 Rank: #${rank}\n\nPlay now: https://webzombies.pythonanywhere.com`;
    }

    window.shareToWhatsApp = () => {
        const text = encodeURIComponent(getShareText());
        window.open(`https://wa.me/?text=${text}`, '_blank');
    };

    window.shareToTwitter = () => {
        const text = encodeURIComponent(getShareText());
        window.open(`https://twitter.com/intent/tweet?text=${text}`, '_blank');
    };

    window.shareToInstagram = () => {
        copyShareText();
        alert('Text copied! Open Instagram and paste it in your story or post.');
    };

    window.copyShareText = () => {
        const text = getShareText();
        navigator.clipboard.writeText(text).then(() => {
            showToast('Copied to clipboard!');
        });
    };

    function showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => toast.classList.add('show'), 100);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }

    // 🎵 ANIMATIONS + EFFECTS
    function addRippleEffect(event) {
        const button = event.currentTarget;
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        ripple.className = 'ripple';
        ripple.style.left = `${event.clientX - rect.left}px`;
        ripple.style.top = `${event.clientY - rect.top}px`;
        button.appendChild(ripple);
        setTimeout(() => ripple.remove(), 600);
    }

    function animateVinylPlayer() {
        const vinyl = document.querySelector('.vinyl-player');
        vinyl.classList.add('animate-hover');
        setTimeout(() => vinyl.classList.remove('animate-hover'), 300);
    }

    function scrollToLeaderboard() {
        const leaderboard = document.querySelector('.daily-leaderboard');
        leaderboard?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // 🔁 PULL TO REFRESH
    let touchStart = 0;
    let pullStarted = false;

    document.addEventListener('touchstart', (e) => {
        touchStart = e.touches[0].clientY;
    });

    document.addEventListener('touchmove', (e) => {
        if (window.scrollY === 0) {
            const pull = e.touches[0].clientY - touchStart;
            if (pull > 50 && !pullStarted) {
                pullStarted = true;
                document.body.classList.add('pulling');
                if (navigator.vibrate) navigator.vibrate(10);
            }
        }
    });

    document.addEventListener('touchend', () => {
        if (pullStarted) {
            pullStarted = false;
            document.body.classList.remove('pulling');
            location.reload();
        }
    });

    // ✨ HAPTIC FEEDBACK
    function addHapticFeedback(selectors, duration = 10) {
        selectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(element => {
                element.addEventListener('click', () => {
                    if (navigator.vibrate) navigator.vibrate(duration);
                });
            });
        });
    }

    addHapticFeedback([
        '.btn',
        '.btn-share-icon',
        '.vinyl-center',
        '.leaderboard-toggle'
    ]);

