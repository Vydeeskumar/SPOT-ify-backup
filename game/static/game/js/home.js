function toggleLeaderboard(e) {
    const toggle = e.currentTarget;
    const content = toggle.parentElement.querySelector('#leaderboard-content');
    const chevron = toggle.querySelector('i');

    if (!content || !chevron) return;

    const isHidden = content.style.display === 'none' || content.style.display === '';

    if (isHidden) {
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

    console.log("🟣 Toggle leaderboard clicked");
}

window.toggleLeaderboard = toggleLeaderboard;

function attachLeaderboardToggleListeners() {
        const toggles = document.querySelectorAll('.leaderboard-toggle');
        console.log(`🟣 Found ${toggles.length} leaderboard toggles`);
        toggles.forEach(toggle => {
            toggle.removeEventListener('click', toggleLeaderboard);
            toggle.addEventListener('click', toggleLeaderboard);
        });
    }




document.addEventListener('DOMContentLoaded', function () {
    console.log("✅ home.js loaded");
    const mainGame = document.getElementById('game-main');  // Add this container to home.html
    if (!mainGame) return;

        // Initialize variables
    let startTime = null;
    let timerInterval;
    let isTimerRunning = false;
    let audioContext = null;
    let analyser = null;
    let dataArray = null;
    let source = null;

    // Initialize audio context
    function initAudioContext() {
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioContext.createAnalyser();
            analyser.fftSize = 32;
            dataArray = new Uint8Array(analyser.frequencyBinCount);
        }
    }

    // Timer functions with persistence
    function initializeTimer() {
        const storedData = localStorage.getItem('songTimer');
        if (storedData) {
            try {
                const { date, initialStartTime } = JSON.parse(storedData);
                if (date === new Date().toDateString()) {
                    startTime = parseInt(initialStartTime);
                    isTimerRunning = true;
                    timerInterval = setInterval(updateTimer, 100);
                    return true;
                }
            } catch (error) {
                console.error('Timer initialization error:', error);
                localStorage.removeItem('songTimer');
            }
        }
        return false;
    }

    function startTimer() {
        if (!isTimerRunning && startTime === null) {
            startTime = Date.now();
            isTimerRunning = true;
            timerInterval = setInterval(updateTimer, 100);

            localStorage.setItem('songTimer', JSON.stringify({
                date: new Date().toDateString(),
                initialStartTime: startTime
            }));
        }
    }

    function updateTimer() {
        if (startTime === null) return;

        const elapsedTime = (Date.now() - startTime) / 1000;
        if (elapsedTime < 0) {
            startTime = Date.now();
            return;
        }

        const minutes = Math.floor(elapsedTime / 60);
        const seconds = Math.floor(elapsedTime % 60);

        const timerElement = document.getElementById('timer');
        if (timerElement) {
            timerElement.textContent =
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }

        const pointsIndicator = document.getElementById('points-indicator');
        if (!pointsIndicator) return;

        const pointsValue = pointsIndicator.querySelector('.points-value');
        if (!pointsValue) return;

        let currentPoints;
        if (elapsedTime <= 10) {
            currentPoints = 8;
        } else if (elapsedTime <= 20) {
            currentPoints = 5;
        } else if (elapsedTime <= 30) {
            currentPoints = 4;
        } else if (elapsedTime <= 45) {
            currentPoints = 3;
        } else if (elapsedTime <= 60) {
            currentPoints = 2;
        } else {
            currentPoints = 1;
        }

        if (pointsValue.textContent != currentPoints) {
            pointsValue.textContent = currentPoints;
            pointsValue.classList.remove('points-change');
            void pointsValue.offsetWidth;
            pointsValue.classList.add('points-change');

            // Update colors
            if (currentPoints >= 8) {
                pointsValue.style.color = '#B026FF';
            } else if (currentPoints >= 5) {
                pointsValue.style.color = '#0096FF';
            } else if (currentPoints >= 3) {
                pointsValue.style.color = '#FFD700';
            } else {
                pointsValue.style.color = '#FF69B4';
            }
        }
    }


    function stopTimer() {
        if (startTime === null) return 0;
        clearInterval(timerInterval);
        isTimerRunning = false;
        const timeTaken = (Date.now() - startTime) / 1000;
        return Math.max(0, Math.min(timeTaken, 3600));
    }

    function updateCountdown() {
        try {
            const now = new Date();

            // Get UTC midnight of the next day
            const utcNow = new Date(now.toUTCString());
            const nextUTCMidnight = new Date(Date.UTC(
                utcNow.getUTCFullYear(),
                utcNow.getUTCMonth(),
                utcNow.getUTCDate() + 1, // tomorrow
                0, 0, 0, 0
            ));

            // Calculate time left until UTC midnight
            const timeLeft = nextUTCMidnight - now;

            const hours = Math.floor(timeLeft / (1000 * 60 * 60));
            const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);

            // Update DOM
            const hoursElement = document.getElementById('countdown-hours');
            const minutesElement = document.getElementById('countdown-minutes');
            const secondsElement = document.getElementById('countdown-seconds');

            if (hoursElement && minutesElement && secondsElement) {
                hoursElement.textContent = hours.toString().padStart(2, '0');
                minutesElement.textContent = minutes.toString().padStart(2, '0');
                secondsElement.textContent = seconds.toString().padStart(2, '0');
            }
        } catch (error) {
            console.error('Countdown update error:', error);
        }
    }



    // ADD this new function
    function initializeCountdown() {
        console.log('Initializing countdown...'); // This helps us debug

        // Clear any existing intervals
        if (window.countdownInterval) {
            clearInterval(window.countdownInterval);
        }

        // Start new countdown
        updateCountdown();
        window.countdownInterval = setInterval(updateCountdown, 1000);
    }







    // Check if we need to show countdown
    const needsCountdown = document.querySelector('.countdown-section') ||
                        document.querySelector('.result-container');

    if (needsCountdown) {
        console.log('Countdown needed, initializing...'); // This helps us debug
        initializeCountdown();
    }


    // ADD this new event listener
    window.addEventListener('beforeunload', function() {
        if (window.countdownInterval) {
            clearInterval(window.countdownInterval);
        }
    });




    function showResultView() {
        try {

            const gameContainer = document.getElementById('game-container');
            const resultContainer = document.getElementById('result-container');

            if (gameContainer) gameContainer.style.display = 'none';
            if (resultContainer) {
                resultContainer.style.display = 'block';
                resultContainer.style.opacity = '1';
                resultContainer.style.visibility = 'visible';
            }


            // Get current points and update score message
            const points = document.querySelector('.points-value')?.textContent || '0';
            const scoreMessage = document.getElementById('score-message');

            if (scoreMessage) {
                let messageHTML;

                // Check if user gave up using the window flag
                if (window.isGaveUp) {
                    messageHTML = `😅 Better Luck Next Time! <span class="highlight-points">0 Points</span> • Even ARR had tough days!`;
                } else {
                    const pointsNum = parseInt(points);
                    if (pointsNum >= 8) {
                        messageHTML = `🎯 Mass Performance! <span class="highlight-points">${points} Points</span> • Are you Anirudh in disguise?`;
                    } else if (pointsNum >= 5) {
                        messageHTML = `🎶 Semma Speed! <span class="highlight-points">${points} Points</span> • You're on fire mamey!`;
                    } else if (pointsNum >= 3) {
                        messageHTML = `🎧 Took Your Sweet Time! <span class="highlight-points">${points} Points</span> • Style-ah Solve Pannita!`;
                    } else {
                        messageHTML = `✨ Finally! <span class="highlight-points">${points} Points</span> • Even Ilayaraja started somewhere!`;
                    }
                }
                scoreMessage.innerHTML = messageHTML;
            }


            // Stop the main audio if it's playing
            const mainAudio = document.getElementById('song-snippet');
            if (mainAudio) {
                mainAudio.pause();
            }

            // Play the reveal snippet automatically
            const revealAudio = document.getElementById('reveal-snippet');
            if (revealAudio) {
                revealAudio.volume = 0.7;
                revealAudio.play()
                    .catch(error => console.log('Audio playback failed:', error));
            }



            // Remove any existing leaderboard
            const existingLeaderboard = document.querySelector('.daily-leaderboard');
            if (existingLeaderboard) {
                existingLeaderboard.remove();
            }

            // Fetch and display daily leaderboard immediately
            fetch(`/${window.currentLanguage || 'tamil'}/get-daily-rankings/`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    const songDetails = document.querySelector('.song-details');
                    if (!songDetails) {
                        throw new Error('Song details element not found');
                    }

                    const leaderboardHTML = `
                        <div class="daily-leaderboard mt-4" style="background: rgba(176, 38, 255, 0.05); padding: 20px; border-radius: 15px; opacity: 0; animation: fadeIn 0.5s ease forwards 0.9s;">

                            <div class="leaderboard-toggle" style="background: rgba(176, 38, 255, 0.1); padding: 15px; border-radius: 10px; cursor: pointer; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                                <span style="color: white;">View Leaderboard</span>
                                <i class="fas fa-chevron-down" style="color: var(--neon-purple); transition: transform 0.3s ease;"></i>
                            </div>

                            <div id="leaderboard-content" style="display: none; transition: all 0.3s ease;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                    <h5 style="color: var(--neon-blue); margin: 0;">
                                        <i class="fas fa-trophy"></i> Today's Rankings
                                    </h5>
                                    <span style="color: var(--neon-purple);">
                                        Your Rank: #${data.userRank}
                                    </span>
                                </div>


                                <div class="leaderboard-list" style="max-height: 300px; overflow-y: auto; margin-top: 10px;">
                                    ${data.scores.map((score, index) => `
                                        <div class="leaderboard-item" style="display: grid; grid-template-columns: auto 1fr auto auto; gap: 15px; padding: 10px; margin: 5px 0; background: rgba(176, 38, 255, 0.1); border-radius: 8px; ${score.isCurrentUser ? 'border: 1px solid var(--neon-purple);' : ''}">
                                            <div style="color: var(--neon-purple); font-weight: bold;">
                                                ${index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${index + 1}`}
                                            </div>
                                            <div style="color: white;">
                                                <a href="/${window.currentLanguage || 'tamil'}/profile/${score.username}" style="color: white; text-decoration: none; font-weight: bold;">
                                                    ${score.username}
                                                </a>
                                            </div>
                                            <div style="color: var(--neon-blue);">${score.score} pts</div>
                                            <div style="color: var(--neon-pink);">${score.guessTime}s</div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                    `;

                    console.log("✅ songDetails found:", songDetails);
                    if (!songDetails) {
                        console.error("❌ songDetails element not found. Leaderboard won't be injected.");
                        return; // 🛑 Don't proceed if songDetails is missing
                    }

                    // ✅ Inject into page
                    songDetails.insertAdjacentHTML('afterend', leaderboardHTML);
                    console.log("✅ Leaderboard HTML injected after .song-details");

                    setTimeout(() => {
                        attachLeaderboardToggleListeners();
                    }, 100);  // ⬅️ This is key




                })
                .catch(error => {
                    console.error('Error fetching rankings:', error);
                });


            initializeCountdown();

            // Hide any success/error messages
            const resultMessage = document.getElementById('result-message');
            if (resultMessage) {
                resultMessage.style.display = 'none';
            }
        } catch (error) {
            console.error('Error in showResultView:', error);
        }
    }




    // Reattach all dynamic listeners here

    document.getElementById('upi-copy-btn')?.addEventListener('click', copyUpiId);  // Adjust ID if needed
    document.querySelector('.btn-share-whatsapp')?.addEventListener('click', shareToWhatsApp);
    document.querySelector('.btn-share-twitter')?.addEventListener('click', shareToTwitter);
    document.querySelector('.btn-share-copy')?.addEventListener('click', copyShareText);





    // Initialize elements
    const audioElement = document.getElementById('song-snippet');
    const vinylPlayer = document.getElementById('vinyl-player');
    const playPauseBtn = document.getElementById('playPauseBtn');
    const giveUpBtn = document.getElementById('giveUpBtn');
    const progressFill = document.querySelector('.progress-fill');
    const currentTimeDisplay = document.getElementById('current-time');
    const totalTimeDisplay = document.getElementById('total-time');

    if (audioElement) {
        audioElement.addEventListener('timeupdate', updateProgress);

        audioElement.addEventListener('loadedmetadata', () => {
            const minutes = Math.floor(audioElement.duration / 60);
            const seconds = Math.floor(audioElement.duration % 60);
            if (totalTimeDisplay) {
                totalTimeDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            }
        });

        audioElement.addEventListener('ended', () => {
            if (vinylPlayer) {
                vinylPlayer.classList.remove('playing');
                vinylPlayer.classList.add('paused');
            }
            if (playPauseBtn) {
                playPauseBtn.innerHTML = '<i class="fas fa-play"></i> Play';
            }
            const vinylIcon = document.getElementById('vinyl-play-icon');
            if (vinylIcon) {
                vinylIcon.className = 'fas fa-play';
            }
        });
    }



    function updateProgress() {
        if (audioElement.duration) {
            const progress = (audioElement.currentTime / audioElement.duration) * 100;
            progressFill.style.width = `${progress}%`;

            // Update time displays
            const currentMinutes = Math.floor(audioElement.currentTime / 60);
            const currentSeconds = Math.floor(audioElement.currentTime % 60);
            const totalMinutes = Math.floor(audioElement.duration / 60);
            const totalSeconds = Math.floor(audioElement.duration % 60);

            if (currentTimeDisplay && totalTimeDisplay) {
                currentTimeDisplay.textContent = `${currentMinutes}:${currentSeconds.toString().padStart(2, '0')}`;
                totalTimeDisplay.textContent = `${totalMinutes}:${totalSeconds.toString().padStart(2, '0')}`;
            }

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
                vinylPlayer.classList.add('playing');
                vinylPlayer.classList.remove('paused');
                playPauseBtn.innerHTML = '<i class="fas fa-pause"></i> Pause';
                // Update vinyl center icon
                document.getElementById('vinyl-play-icon').className = 'fas fa-pause';
                startTimer();
            } else {
                audioElement.pause();
                vinylPlayer.classList.remove('playing');
                vinylPlayer.classList.add('paused');
                playPauseBtn.innerHTML = '<i class="fas fa-play"></i> Play';
                // Update vinyl center icon
                document.getElementById('vinyl-play-icon').className = 'fas fa-play';
            }
        });
    }

    // Add this new function right after the above code
    window.togglePlay = function() {
        playPauseBtn.click();
    };




    // Give Up functionality
    if (giveUpBtn) {
        giveUpBtn.addEventListener('click', async () => {
            if (confirm('Are you sure you want to give up? You will receive 0 points for today.')) {
                try {
                    const response = await fetch(`/${window.currentLanguage || 'tamil'}/give-up/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                        }
                    });

                    if (response.ok) {
                        const data = await response.json();

                        // Stop audio and animations
                        audioElement.pause();

                        // Set points to 0 for give up
                        const pointsValue = document.querySelector('.points-value');
                        if (pointsValue) {
                            pointsValue.textContent = '0';
                        }

                        // Set a flag to indicate give-up
                        window.isGaveUp = true;

                        // Show result view (this should now show the give-up message)
                        showResultView();

                        // Clear timer
                        clearInterval(timerInterval);
                        localStorage.removeItem('songTimer');
                    }
                } catch (error) {
                    console.error('Error:', error);
                }
            }
        });
    }


    // Form submission
    document.getElementById('guess-form')?.addEventListener('submit', async function(e) {
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
                    spotify_id: guessInput.dataset.spotifyId,  // Add this line
                    time_taken: timeTaken
                })
            });
            // ... rest of your code

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();

            if (data.correct) {
                // Show success message
                resultMessage.innerHTML = `<div class="alert alert-success">
                    ${data.message}
                </div>`;

                // Show result view
                showResultView();

                // Stop audio and clear timer
                audioElement.pause();
                clearInterval(timerInterval);
                localStorage.removeItem('songTimer');

                // 🔥 Trigger streak celebration modal after 3 seconds
                if (data.streak && data.streak > 0) {
                    window.showStreakCelebration(data.streak, 3000);
                }
            } else {
                resultMessage.innerHTML = `<div class="alert alert-danger">
                    ${data.message}
                </div>`;
                isTimerRunning = true;
                timerInterval = setInterval(updateTimer, 100);
            }
        } catch (error) {
            console.error('Error:', error);
            resultMessage.innerHTML = '<div class="alert alert-danger">An error occurred. Please try again.</div>';
        }
    });

    // Initialize timer on page load
    const timerWasRunning = initializeTimer();

    // Start timer on first play only if it wasn't already running
    if (audioElement && !timerWasRunning) {
        audioElement.addEventListener('play', startTimer, { once: true });
    }

    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden && isTimerRunning) {
            clearInterval(timerInterval);
            timerInterval = setInterval(updateTimer, 100);
        }
    });





    function copyUpiId() {
        const upiId = document.getElementById('upiId');
        upiId.select();
        document.execCommand('copy');

        // Show feedback
        const button = event.target.closest('button');
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i> Copied!';
        setTimeout(() => {
            button.innerHTML = originalText;
        }, 2000);
    }

    window.copyUpiId = copyUpiId;




    let accessToken = '';

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
        if (!query) return;

        try {
            // Add more search parameters and operators
            const searchQuery = `${query} OR lyrics:${query} OR track:${query}`;
            const response = await fetch(`https://api.spotify.com/v1/search?q=${encodeURIComponent(query)}&type=track&market=IN&limit=20&include_external=audio`, {
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });

            const data = await response.json();
            return data.tracks.items;
        } catch (error) {
            console.error('Error searching Spotify:', error);
            return [];
        }
    }

    let debounceTimeout;

    const guessInputField = document.getElementById('guess-input');
    if (guessInputField) {
        guessInputField.addEventListener('input', async function (e) {
            clearTimeout(debounceTimeout);
            const query = e.target.value;

            debounceTimeout = setTimeout(async () => {
                if (query.length < 2) {
                    document.getElementById('suggestions').style.display = 'none';
                    return;
                }

                const tracks = await searchSpotify(query);
                const suggestionsContainer = document.getElementById('suggestions');

                if (tracks && tracks.length > 0) {
                    suggestionsContainer.innerHTML = tracks.map(track => `
                        <div class="suggestion-item"
                            data-song-name="${encodeURIComponent(track.name)}"
                            data-spotify-id="${track.id}">
                            <img src="${track.album.images[track.album.images.length - 1].url}" alt="${track.name}">
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
            }, 100);
        });
    }

    // Select suggestion and apply it to the guess input
    function selectSuggestion(songName, spotifyId) {
        const guessInput = document.getElementById('guess-input');
        const suggestions = document.getElementById('suggestions');

        if (guessInput && suggestions) {
            guessInput.value = songName;
            guessInput.dataset.spotifyId = spotifyId;  // Store the ID
            suggestions.style.display = 'none';
        }
    }

    // Close suggestions when clicking outside
    document.addEventListener('click', function (e) {
        const guessInput = document.getElementById('guess-input');
        const suggestions = document.getElementById('suggestions');

        if (suggestions && !e.target.closest('#guess-input') && !e.target.closest('#suggestions')) {
            suggestions.style.display = 'none';
        }
    });

    // Get token when page loads (✅ leave this untouched)
    getSpotifyToken();




    // Share functions
    function getShareText() {
        const score = document.querySelector('.points-value')?.textContent || '';
        const rank = document.querySelector('.leaderboard-header span')?.textContent.replace('Your Rank: #', '') || '';

        return `🎵 SPOT-ify the Paatu\n` +
            `🎯 Score: ${score} points\n` +
            `🏆 Rank: #${rank}\n\n` +
            `Play now: https://webzombies.pythonanywhere.com/${window.currentLanguage || 'tamil'}/`;  // Your actual URL
    }

    function getCurrentDay() {
        // Calculate days since game launch
        const launchDate = new Date('2024-01-01'); // Replace with your launch date
        const today = new Date();
        const diffTime = Math.abs(today - launchDate);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays;
    }

    window.shareToWhatsApp = function () {
        const text = encodeURIComponent(getShareText());
        window.open(`https://wa.me/?text=${text}`, '_blank');
    };

    window.shareToTwitter = function () {
        const text = encodeURIComponent(getShareText());
        window.open(`https://twitter.com/intent/tweet?text=${text}`, '_blank');
    };

    window.shareToInstagram = function () {
        copyShareText();
        alert('Text copied! Open Instagram and paste in your story or post.');
    };

    window.copyShareText = function () {
        const text = getShareText();
        navigator.clipboard.writeText(text).then(() => {
            const copySuccess = document.getElementById('copySuccess');
            if (!copySuccess) return;
            copySuccess.style.display = 'block';
            copySuccess.classList.add('show');
            setTimeout(() => {
                copySuccess.classList.remove('show');
                setTimeout(() => {
                    copySuccess.style.display = 'none';
                }, 300);
            }, 2000);
        });
    };

    // Add these new interaction functions

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

    // Add smooth scroll to leaderboard
    function scrollToLeaderboard() {
    const leaderboard = document.querySelector('.daily-leaderboard');
    leaderboard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Pull to Refresh
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
                // Trigger haptic feedback
                if (navigator.vibrate) {
                    navigator.vibrate(10);
                }
            }
        }
    });

    document.addEventListener('touchend', () => {
        if (pullStarted) {
            pullStarted = false;
            document.body.classList.remove('pulling');
            // Reload the page
            location.reload();
        }
    });

    // Haptic Feedback for Interactions
    function addHapticFeedback(elements, duration = 10) {
        elements.forEach(selector => {
            document.querySelectorAll(selector).forEach(element => {
                element.addEventListener('click', () => {
                    if (navigator.vibrate) {
                        navigator.vibrate(duration);
                    }
                });
            });
        });
    }

    // Add haptic feedback to interactive elements
    addHapticFeedback([
        '.btn',
        '.btn-share-icon',
        '.vinyl-center',
        '.leaderboard-toggle'
    ]);

    // Smooth State Transitions
    function addTransitionClass(element, className, duration = 300) {
        element.classList.add(className);
        setTimeout(() => element.classList.remove(className), duration);
    }

    // Enhanced Share Functionality
    function shareContent(platform) {
        const shareText = getShareText();

        switch(platform) {
            case 'whatsapp':
                window.open(`whatsapp://send?text=${encodeURIComponent(shareText)}`);
                break;
            case 'twitter':
                window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}`);
                break;
            case 'copy':
                navigator.clipboard.writeText(shareText).then(() => {
                    showToast('Copied to clipboard!');
                    if (navigator.vibrate) navigator.vibrate([10, 30, 10]);
                });
                break;
        }
    }

    // Toast Notification
    function showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('show');
            if (navigator.vibrate) navigator.vibrate(10);
        }, 100);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }

    const suggestionsContainer = document.getElementById('suggestions');
    if (suggestionsContainer) {
        suggestionsContainer.addEventListener('click', function(e) {
            const suggestion = e.target.closest('.suggestion-item');
            if (!suggestion) return;

            const songName = decodeURIComponent(suggestion.dataset.songName);
            const spotifyId = suggestion.dataset.spotifyId;
            selectSuggestion(songName, spotifyId);
        });
    }





});




document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        attachLeaderboardToggleListeners();  // ✅ Ensures DOM is fully ready
        console.log("🟣 Attached toggle listeners to static leaderboard");
    }, 100);
});





















// 🔥 STREAK CELEBRATION MODAL FUNCTIONALITY

const streakMessages = {
    regular: [
        "Keep it going!",
        "You're on fire!",
        "Streak master!",
        "Unstoppable!",
        "Amazing consistency!",
        "Daily dedication!",
        "Music genius!",
        "Perfect rhythm!",
        "Song detective!",
        "Melody master!",
        "Tune hunter!",
        "Beat keeper!"
    ],
    milestone: [
        "INCREDIBLE MILESTONE!",
        "LEGENDARY STREAK!",
        "ABSOLUTELY AMAZING!",
        "STREAK CHAMPION!",
        "MUSIC MASTER!",
        "PHENOMENAL DEDICATION!",
        "STREAK SUPERSTAR!",
        "UNBELIEVABLE CONSISTENCY!"
    ]
};

function shouldShowStreakModal(streak) {
    if (!streak || streak === 0) return false;

    // Show for days 1-10
    if (streak <= 10) return true;

    // Show for multiples of 5 after 10
    if (streak > 10 && streak % 5 === 0) return true;

    return false;
}

function isSpecialMilestone(streak) {
    const milestones = [10, 25, 50, 75, 100, 150, 200, 250, 300, 365, 500, 750, 1000];
    return milestones.includes(streak);
}

function getRandomMessage(isSpecial = false) {
    const messages = isSpecial ? streakMessages.milestone : streakMessages.regular;
    return messages[Math.floor(Math.random() * messages.length)];
}

function showStreakModal(streak) {
    if (!shouldShowStreakModal(streak)) return;

    const modal = document.getElementById('streak-modal');
    const modalContent = modal.querySelector('.streak-modal-content');
    const title = modal.querySelector('.streak-title');
    const count = modal.querySelector('.streak-count');
    const message = modal.querySelector('.streak-message');
    const closeBtn = modal.querySelector('.streak-close-btn');

    if (!modal || !modalContent) return;

    const isSpecial = isSpecialMilestone(streak);

    // Set content
    title.textContent = isSpecial ? 'MILESTONE ACHIEVED!' : 'STREAK FIRE!';
    count.textContent = `${streak} Day Streak!`;
    message.textContent = getRandomMessage(isSpecial);

    // Apply special styling for milestones
    if (isSpecial) {
        modalContent.classList.add('milestone');
    } else {
        modalContent.classList.remove('milestone');
    }

    // Show modal with animation
    modal.style.display = 'block';

    // Auto-close after 4 seconds
    const autoCloseTimer = setTimeout(() => {
        hideStreakModal();
    }, 4000);

    // Close button functionality
    closeBtn.onclick = () => {
        clearTimeout(autoCloseTimer);
        hideStreakModal();
    };

    // Close on background click
    modal.onclick = (e) => {
        if (e.target === modal) {
            clearTimeout(autoCloseTimer);
            hideStreakModal();
        }
    };

    console.log(`🔥 Showing streak modal for ${streak} days (${isSpecial ? 'MILESTONE' : 'regular'})`);
}

function hideStreakModal() {
    const modal = document.getElementById('streak-modal');
    if (modal) {
        modal.style.display = 'none';
        console.log('🔥 Streak modal hidden');
    }
}

// Global function to trigger streak modal (called from game logic)
window.showStreakCelebration = function(streak, delay = 3000) {
    console.log(`🔥 Streak celebration scheduled for ${streak} days in ${delay}ms`);
    setTimeout(() => {
        showStreakModal(streak);
    }, delay);
};

// Export for use in other files
window.streakModal = {
    show: showStreakModal,
    hide: hideStreakModal,
    shouldShow: shouldShowStreakModal,
    isSpecial: isSpecialMilestone
};

console.log('🔥 Streak modal system loaded');














console.log('🔥 Streak modal system loaded');

// 🎤 ADVANCED VOICE RECOGNITION SYSTEM - ALL LANGUAGES SUPPORT

class VoiceRecognitionSystem {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.currentLanguage = window.currentLanguage || 'tamil';
        this.voiceBtn = document.getElementById('voiceBtn');
        this.voiceFeedback = document.getElementById('voiceFeedback');
        this.voiceStatusText = document.getElementById('voiceStatusText');
        this.voiceTranscript = document.getElementById('voiceTranscript');
        this.voiceInstructions = document.getElementById('voiceInstructions');
        this.guessInput = document.getElementById('guess-input');

        // CORRECTED: Both Tamil AND Hindi songs are in English letters (Romanized)!
        this.languageMap = {
            'tamil': 'en-US',    // Tamil songs written in English letters!
            'english': 'en-US',  // English songs
            'hindi': 'en-US'     // Hindi songs ALSO written in English letters!
        };

        this.fallbackLanguages = {
            'tamil': ['en-US', 'en-IN'],     // English recognition for Romanized Tamil
            'english': ['en-US', 'en-IN'],   // English variants
            'hindi': ['en-US', 'en-IN']      // English recognition for Romanized Hindi
        };

        this.initializeVoiceRecognition();
        this.bindEvents();
    }

    initializeVoiceRecognition() {
        // Check for Web Speech API support
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.warn('🎤 Web Speech API not supported');
            this.voiceBtn.style.display = 'none';
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();

        // Configure recognition
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 3;

        this.setupRecognitionEvents();
        console.log('🎤 Voice recognition system initialized');
    }

    setupRecognitionEvents() {
        if (!this.recognition) return;

        this.recognition.onstart = () => {
            console.log('🎤 Voice recognition started');
            this.isListening = true;
            this.updateUI('listening');
        };

        this.recognition.onresult = (event) => {
            let transcript = '';
            let confidence = 0;

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const result = event.results[i];
                if (result.isFinal) {
                    transcript = result[0].transcript.trim();
                    confidence = result[0].confidence;
                    console.log(`🎤 Final result: "${transcript}" (confidence: ${confidence})`);
                } else {
                    // Show interim results
                    const interimTranscript = result[0].transcript;
                    this.voiceTranscript.textContent = `"${interimTranscript}"`;
                }
            }

            if (transcript) {
                this.processVoiceResult(transcript, confidence);
            }
        };

        this.recognition.onerror = (event) => {
            console.error('🎤 Voice recognition error:', event.error);
            this.handleVoiceError(event.error);
        };

        this.recognition.onend = () => {
            console.log('🎤 Voice recognition ended');
            this.isListening = false;
            if (!this.voiceFeedback.classList.contains('processing')) {
                this.hideVoiceFeedback();
            }
        };
    }

    bindEvents() {
        if (!this.voiceBtn) return;

        this.voiceBtn.addEventListener('click', () => {
            if (this.isListening) {
                this.stopListening();
            } else {
                this.startListening();
            }
        });

        // Close feedback on click outside
        this.voiceFeedback.addEventListener('click', (e) => {
            if (e.target === this.voiceFeedback) {
                this.stopListening();
            }
        });

        // Keyboard shortcut (Ctrl/Cmd + M)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'm') {
                e.preventDefault();
                if (!this.isListening) {
                    this.startListening();
                }
            }
        });
    }

    startListening() {
        if (!this.recognition || this.isListening) return;

        // Set language based on current game language
        const langCode = this.languageMap[this.currentLanguage] || 'en-US';
        this.recognition.lang = langCode;

        console.log(`🎤 Starting voice recognition for ${this.currentLanguage} (${langCode})`);

        try {
            this.recognition.start();
            this.showVoiceFeedback();
        } catch (error) {
            console.error('🎤 Failed to start recognition:', error);
            this.handleVoiceError('start-failed');
        }
    }

    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
        this.hideVoiceFeedback();
    }

    processVoiceResult(transcript, confidence) {
        console.log(`🎤 Processing: "${transcript}" (confidence: ${confidence})`);

        this.updateUI('processing');
        this.voiceTranscript.textContent = `"${transcript}"`;

        // If confidence is high, use result directly
        if (confidence > 0.7) {
            this.submitVoiceGuess(transcript);
        } else {
            // Try Whisper fallback for better accuracy
            console.log('🎤 Low confidence, trying Whisper fallback...');
            this.tryWhisperFallback(transcript);
        }
    }

    submitVoiceGuess(transcript) {
        // Clean up the transcript
        const cleanTranscript = this.cleanTranscript(transcript);

        // Fill the input field
        if (this.guessInput) {
            this.guessInput.value = cleanTranscript;
            this.guessInput.dispatchEvent(new Event('input', { bubbles: true }));
        }

        // Auto-submit or let user confirm
        setTimeout(() => {
            this.hideVoiceFeedback();
            // Optionally auto-submit: document.querySelector('form').submit();
        }, 1000);

        console.log(`🎤 Voice guess submitted: "${cleanTranscript}"`);
    }

    cleanTranscript(transcript) {
        let cleaned = transcript
            .replace(/\b(the|a|an)\b/gi, '') // Remove articles
            .replace(/[.,!?;]/g, '') // Remove punctuation
            .replace(/\s+/g, ' ') // Normalize spaces
            .trim();

        // Apply phonetic corrections for common misrecognitions
        if (this.currentLanguage === 'tamil') {
            cleaned = this.applyTamilPhoneticCorrections(cleaned);
        } else if (this.currentLanguage === 'hindi') {
            cleaned = this.applyHindiPhoneticCorrections(cleaned);
        }

        return cleaned;
    }

    applyTamilPhoneticCorrections(text) {
        // Common Tamil phonetic corrections for English speech recognition
        const corrections = {
            // Common Tamil sounds that get misrecognized
            'andra': 'ondra',
            'endra': 'ondra',
            'renda': 'renda',
            'vaathi': 'vaathi',
            'rowdy': 'rowdy',
            'baby': 'baby',
            'coming': 'coming',
            'kadhal': 'kadhal',
            'anbe': 'anbe',
            'sivam': 'sivam',
            'theri': 'theri',
            'mersal': 'mersal',
            'bigil': 'bigil',
            'master': 'master',
            'beast': 'beast',
            'vikram': 'vikram',
            'leo': 'leo',
            // Add more common Tamil song name corrections
            'naan': 'naan',
            'unna': 'unna',
            'enna': 'enna',
            'illa': 'illa',
            'dhan': 'than',
            'than': 'than'
        };

        let corrected = text.toLowerCase();

        // Apply corrections
        for (const [wrong, right] of Object.entries(corrections)) {
            const regex = new RegExp(`\\b${wrong}\\b`, 'gi');
            corrected = corrected.replace(regex, right);
        }

        return corrected;
    }

    applyHindiPhoneticCorrections(text) {
        // Common Hindi phonetic corrections for English speech recognition
        const corrections = {
            // Common Hindi sounds that get misrecognized
            'tum': 'tum',
            'hai': 'hai',
            'hum': 'hum',
            'main': 'main',
            'kya': 'kya',
            'kal': 'kal',
            'ho': 'ho',
            'naa': 'naa',
            'kabhi': 'kabhi',
            'khushi': 'khushi',
            'gham': 'gham',
            'dilwale': 'dilwale',
            'dulhania': 'dulhania',
            'jayenge': 'jayenge',
            'shah': 'shah',
            'rukh': 'rukh',
            'khan': 'khan',
            'bollywood': 'bollywood',
            'hindi': 'hindi',
            'gaana': 'gaana',
            'film': 'film',
            'movie': 'movie',
            'song': 'song',
            // Add more common Hindi song name corrections
            'pyaar': 'pyaar',
            'ishq': 'ishq',
            'dil': 'dil',
            'mohabbat': 'mohabbat',
            'zindagi': 'zindagi',
            'sapna': 'sapna',
            'rang': 'rang',
            'baarish': 'baarish'
        };

        let corrected = text.toLowerCase();

        // Apply corrections
        for (const [wrong, right] of Object.entries(corrections)) {
            const regex = new RegExp(`\\b${wrong}\\b`, 'gi');
            corrected = corrected.replace(regex, right);
        }

        return corrected;
    }

    async tryWhisperFallback(transcript) {
        console.log('🎤 Attempting Whisper fallback for better accuracy...');

        try {
            // For now, we'll use the Web Speech result since we need audio recording
            // In a full implementation, you would:
            // 1. Record audio during speech recognition
            // 2. Send audio blob to backend
            // 3. Process with Whisper

            // Simulate Whisper processing delay
            await new Promise(resolve => setTimeout(resolve, 1000));

            // Use the Web Speech result for now
            this.submitVoiceGuess(transcript);

            console.log('🎤 Whisper fallback completed (simulated)');

        } catch (error) {
            console.error('🎤 Whisper fallback failed:', error);
            // Fall back to original transcript
            this.submitVoiceGuess(transcript);
        }
    }

    handleVoiceError(error) {
        console.error('🎤 Voice error:', error);

        let errorMessage = 'Voice recognition failed';

        switch (error) {
            case 'no-speech':
                errorMessage = 'No speech detected. Please try again.';
                break;
            case 'audio-capture':
                errorMessage = 'Microphone not accessible. Please check permissions.';
                break;
            case 'not-allowed':
                errorMessage = 'Microphone permission denied. Please allow microphone access.';
                break;
            case 'network':
                errorMessage = 'Network error. Please check your connection.';
                break;
            case 'start-failed':
                errorMessage = 'Failed to start voice recognition.';
                break;
        }

        this.updateUI('error');
        this.voiceStatusText.textContent = `❌ ${errorMessage}`;
        this.voiceInstructions.textContent = 'Click to try again';

        setTimeout(() => {
            this.hideVoiceFeedback();
        }, 3000);
    }

    updateUI(state) {
        if (!this.voiceBtn) return;

        // Reset button classes
        this.voiceBtn.classList.remove('listening', 'processing');

        switch (state) {
            case 'listening':
                this.voiceBtn.classList.add('listening');
                this.voiceStatusText.textContent = '🎤 Listening...';

                // Updated instructions for Romanized Tamil & Hindi
                if (this.currentLanguage === 'tamil') {
                    this.voiceInstructions.textContent = 'Speak Tamil song name (will be recognized in English letters)';
                } else if (this.currentLanguage === 'hindi') {
                    this.voiceInstructions.textContent = 'Speak Hindi song name (will be recognized in English letters)';
                } else {
                    this.voiceInstructions.textContent = 'Speak the English song name clearly';
                }

                this.voiceTranscript.textContent = '';
                break;

            case 'processing':
                this.voiceBtn.classList.add('processing');
                this.voiceStatusText.textContent = '🔄 Processing...';
                this.voiceInstructions.textContent = 'Analyzing your voice input';
                break;

            case 'error':
                // Error styling handled in handleVoiceError
                break;

            default:
                this.voiceStatusText.textContent = '🎤 Ready';
                this.voiceInstructions.textContent = 'Click microphone to start';
        }
    }

    showVoiceFeedback() {
        if (this.voiceFeedback) {
            this.voiceFeedback.classList.add('show');
        }
    }

    hideVoiceFeedback() {
        if (this.voiceFeedback) {
            this.voiceFeedback.classList.remove('show');
            this.voiceFeedback.style.display = 'none'; // Ensure it's completely hidden
        }
        if (this.voiceBtn) {
            this.voiceBtn.classList.remove('listening', 'processing');
        }
    }

    // Method to hide only voice feedback overlay (keep button visible)
    hideVoiceSystem() {
        this.hideVoiceFeedback();
        // Don't hide the voice button - users should always be able to use voice input
        // Just hide the feedback overlay
    }

    // Method to show voice system when game is active
    showVoiceSystem() {
        // Voice button should always be visible if recognition is supported
        if (this.voiceBtn && this.recognition) {
            this.voiceBtn.style.display = 'block';
        }
    }

    // Update current language when user switches
    updateLanguage(newLanguage) {
        this.currentLanguage = newLanguage;
        console.log(`🎤 Voice recognition language updated to: ${newLanguage}`);
    }
}

// Initialize voice recognition system
let voiceRecognition;

document.addEventListener('DOMContentLoaded', () => {
    voiceRecognition = new VoiceRecognitionSystem();
    console.log('🎤 Voice recognition system loaded');

    // Check if voice system should be hidden based on game state
    checkVoiceSystemVisibility();
});

function checkVoiceSystemVisibility() {
    // Only hide voice feedback overlay in certain situations, but keep voice button functional
    const tourModal = document.querySelector('.tour-modal');
    const rulesModal = document.querySelector('#rulesModal.show');
    const answerSection = document.querySelector('.answer-section');
    const resultContainer = document.querySelector('.result-container');

    if (tourModal || rulesModal || answerSection || resultContainer) {
        if (voiceRecognition) {
            // Only hide the feedback overlay, not the voice functionality
            voiceRecognition.hideVoiceFeedback();
        }
    }
    // Voice button should always remain visible and functional
}

// Run visibility check more frequently
setInterval(checkVoiceSystemVisibility, 500);

// Enhanced visibility check that runs more frequently
function enhancedVoiceVisibilityCheck() {
    checkVoiceSystemVisibility();

    // Also check for specific game states
    const gameContainer = document.querySelector('.game-container');
    const answerSection = document.querySelector('.answer-section');
    const resultContainer = document.querySelector('.result-container');

    if (gameContainer && (answerSection || resultContainer)) {
        if (voiceRecognition) {
            voiceRecognition.hideVoiceSystem();
        }
    }
}

// Global function to update voice language when user switches
window.updateVoiceLanguage = function(language) {
    if (voiceRecognition) {
        voiceRecognition.updateLanguage(language);
    }
};

console.log('🎤 Voice recognition module loaded');

// 🏆 CELEBRATION MODALS SYSTEM

class CelebrationModals {
    constructor() {
        this.winnersModal = document.getElementById('winnersModal');
        this.achievementModal = document.getElementById('achievementModal');
        this.currentLanguage = window.currentLanguage || 'tamil';

        this.bindEvents();
        this.checkForCelebrations();
    }

    bindEvents() {
        // Winners modal events
        const winnersClose = document.getElementById('winnersClose');
        const winnersContinue = document.getElementById('winnersContinue');

        if (winnersClose) {
            winnersClose.addEventListener('click', () => this.hideWinnersModal());
        }

        if (winnersContinue) {
            winnersContinue.addEventListener('click', () => this.hideWinnersModal());
        }

        // Achievement modal events
        const achievementClose = document.getElementById('achievementClose');
        const achievementContinue = document.getElementById('achievementContinue');

        if (achievementClose) {
            achievementClose.addEventListener('click', () => this.hideAchievementModal());
        }

        if (achievementContinue) {
            achievementContinue.addEventListener('click', () => this.hideAchievementModal());
        }

        // Close on background click
        if (this.winnersModal) {
            this.winnersModal.addEventListener('click', (e) => {
                if (e.target === this.winnersModal) {
                    this.hideWinnersModal();
                }
            });
        }

        if (this.achievementModal) {
            this.achievementModal.addEventListener('click', (e) => {
                if (e.target === this.achievementModal) {
                    this.hideAchievementModal();
                }
            });
        }
    }

    async checkForCelebrations() {
        try {
            const response = await fetch(`/${this.currentLanguage}/check-celebrations/`);
            const data = await response.json();

            if (data.success) {
                // Show weekly winners first (if applicable)
                if (data.weekly_winners) {
                    setTimeout(() => {
                        this.showWeeklyWinners(data.weekly_winners);
                    }, 1000);
                }

                // Show monthly winners first (if applicable)
                if (data.monthly_winners) {
                    setTimeout(() => {
                        this.showMonthlyWinners(data.monthly_winners);
                    }, 1000);
                }

                // Show daily achievement after winners modal
                if (data.daily_achievement) {
                    const delay = (data.weekly_winners || data.monthly_winners) ? 6000 : 1500;
                    setTimeout(() => {
                        this.showDailyAchievement(data.daily_achievement);
                    }, delay);
                }
            }
        } catch (error) {
            console.error('🏆 Failed to check celebrations:', error);
        }
    }

    showWeeklyWinners(winners) {
        this.showWinnersModal(winners, 'weekly');
    }

    showMonthlyWinners(winners) {
        this.showWinnersModal(winners, 'monthly');
    }

    showWinnersModal(winners, type) {
        if (!this.winnersModal || !winners || winners.length === 0) return;

        const title = document.getElementById('winnersTitle');
        const message = document.getElementById('winnersMessage');

        // Update title and message
        if (type === 'weekly') {
            title.textContent = '🏆 WEEKLY CHAMPIONS 🏆';
            message.textContent = 'Congratulations to this week\'s amazing champions!';
        } else {
            title.textContent = '🏆 MONTHLY CHAMPIONS 🏆';
            message.textContent = 'Celebrating this month\'s incredible champions!';
        }

        // Update podium places
        this.updatePodiumPlace('firstPlace', 'firstScore', winners[0]);
        this.updatePodiumPlace('secondPlace', 'secondScore', winners[1]);
        this.updatePodiumPlace('thirdPlace', 'thirdScore', winners[2]);

        // Show modal
        this.winnersModal.style.display = 'block';

        console.log(`🏆 Showing ${type} winners modal`);
    }

    updatePodiumPlace(nameId, scoreId, winner) {
        const nameElement = document.getElementById(nameId);
        const scoreElement = document.getElementById(scoreId);

        if (winner && nameElement && scoreElement) {
            nameElement.textContent = winner.username;
            scoreElement.textContent = `${winner.total_score} pts`;
        } else if (nameElement && scoreElement) {
            nameElement.textContent = 'No Player';
            scoreElement.textContent = '0 pts';
        }
    }

    showDailyAchievement(achievement) {
        if (!this.achievementModal || !achievement) return;

        const rank = document.getElementById('achievementRank');
        const text = document.getElementById('achievementText');
        const subtext = document.getElementById('achievementSubtext');

        // Update content
        if (rank) rank.textContent = `#${achievement.rank}`;
        if (text) text.textContent = `You ranked #${achievement.rank} yesterday!`;

        // Custom messages based on rank
        let message = 'Great performance! Keep up the amazing work!';
        if (achievement.rank === 1) {
            message = '🎉 INCREDIBLE! You were #1 yesterday! You\'re a true champion!';
        } else if (achievement.rank <= 3) {
            message = '🥇 Amazing! You made it to the top 3! Fantastic job!';
        } else if (achievement.rank <= 5) {
            message = '⭐ Excellent! Top 5 performance! You\'re doing great!';
        } else if (achievement.rank <= 10) {
            message = '🌟 Well done! Top 10 achievement! Keep climbing!';
        }

        if (subtext) subtext.textContent = message;

        // Show modal
        this.achievementModal.style.display = 'block';

        console.log(`⭐ Showing daily achievement modal for rank #${achievement.rank}`);
    }

    hideWinnersModal() {
        if (this.winnersModal) {
            this.winnersModal.style.display = 'none';
        }
    }

    hideAchievementModal() {
        if (this.achievementModal) {
            this.achievementModal.style.display = 'none';
        }
    }
}

// 🧪 ADMIN TESTING FUNCTIONS
window.testWeeklyWinners = function() {
    const mockWinners = [
        { username: 'TestUser1', total_score: 200 },
        { username: 'TestUser2', total_score: 150 },
        { username: 'TestUser3', total_score: 120 }
    ];
    celebrationModals.showWeeklyWinners(mockWinners);
};

window.testMonthlyWinners = function() {
    const mockWinners = [
        { username: 'MonthlyChamp', total_score: 500 },
        { username: 'SecondPlace', total_score: 450 },
        { username: 'ThirdPlace', total_score: 400 }
    ];
    celebrationModals.showMonthlyWinners(mockWinners);
};

window.testDailyAchievement = function(rank) {
    const mockAchievement = { rank: rank };
    celebrationModals.showDailyAchievement(mockAchievement);
};

// Initialize celebration modals system
let celebrationModals;

document.addEventListener('DOMContentLoaded', () => {
    celebrationModals = new CelebrationModals();
    console.log('🏆 Celebration modals system loaded');
});

console.log('🏆 Celebration modals module loaded');

// 🎮 INTERACTIVE ONBOARDING TOUR SYSTEM

class OnboardingTour {
    constructor() {
        this.currentStep = 0;
        this.totalSteps = 8;
        this.tourModal = null;
        this.isActive = false;
        this.currentLanguage = window.currentLanguage || 'tamil';

        this.steps = [
            {
                title: "🎵 Welcome to SPOT-ify!",
                content: "The ultimate daily music guessing game! Listen to song snippets and test your music knowledge.",
                highlight: null,
                buttonText: "Let's Start!"
            },
            {
                title: "🎧 Listen to Song Snippets",
                content: "Each day features a new song. Click the play button to hear a snippet and guess the song name!",
                highlight: ".audio-controls",
                buttonText: "Got it!"
            },
            {
                title: "🎤 Make Your Guess",
                content: "Type the song name in the input box. You can also use the microphone button for voice recognition!",
                highlight: ".guess-section",
                buttonText: "Cool!"
            },
            {
                title: "🌍 Language Orb - Switch Languages!",
                content: "Click the floating orb to switch between Tamil (Paatu), English (Song), and Hindi (Gaana) versions. Each language has different songs and separate leaderboards!",
                highlight: ".language-orb",
                buttonText: "Amazing!"
            },
            {
                title: "⏱️ Scoring System",
                content: "Speed matters! Guess within 10 seconds for 8 points, 20 seconds for 5 points, and so on.",
                highlight: ".timer-section",
                buttonText: "Understood!"
            },
            {
                title: "📊 Language-Specific Stats",
                content: "Important: Each language (Tamil/English/Hindi) has its own leaderboards, streaks, and statistics. Your progress is tracked separately for each language!",
                highlight: ".leaderboard-link",
                buttonText: "Got it!"
            },
            {
                title: "📚 Archive Feature",
                content: "Missed a day? No problem! Use the Archive to play previous songs and catch up on your favorites.",
                highlight: ".archive-link",
                buttonText: "Awesome!"
            },
            {
                title: "🎮 Ready to Play!",
                content: "You're all set! Compete with friends, build streaks, and become the ultimate music champion!",
                highlight: null,
                buttonText: "Start Playing! 🚀"
            }
        ];

        this.createTourModal();
        this.bindEvents();
        this.checkShouldShowTour();
    }

    createTourModal() {
        // Create tour modal HTML
        const modalHTML = `
            <div id="onboardingTour" class="onboarding-tour">
                <div class="tour-overlay"></div>
                <div class="tour-modal">
                    <div class="tour-header">
                        <div class="tour-progress">
                            <span id="tourStepIndicator">Step 1 of ${this.totalSteps}</span>
                        </div>
                        <button class="tour-skip" id="tourSkip">Skip Tour</button>
                    </div>
                    <div class="tour-content">
                        <h3 id="tourTitle">Welcome!</h3>
                        <p id="tourDescription">Let's get you started...</p>
                    </div>
                    <div class="tour-navigation">
                        <button class="tour-btn tour-back" id="tourBack" style="display: none;">
                            ← Back
                        </button>
                        <button class="tour-btn tour-next" id="tourNext">
                            Next →
                        </button>
                    </div>
                </div>
                <div class="tour-spotlight" id="tourSpotlight"></div>
            </div>
        `;

        // Add to page
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.tourModal = document.getElementById('onboardingTour');
    }

    bindEvents() {
        const nextBtn = document.getElementById('tourNext');
        const backBtn = document.getElementById('tourBack');
        const skipBtn = document.getElementById('tourSkip');

        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.nextStep());
        }

        if (backBtn) {
            backBtn.addEventListener('click', () => this.previousStep());
        }

        if (skipBtn) {
            skipBtn.addEventListener('click', () => this.skipTour());
        }

        // Prevent closing on overlay click during tour
        if (this.tourModal) {
            this.tourModal.addEventListener('click', (e) => {
                if (e.target.classList.contains('tour-overlay')) {
                    // Don't close - force users to complete or skip
                }
            });
        }
    }

    checkShouldShowTour() {
        // Check if user has seen the new onboarding tour
        const hasSeenNewTour = localStorage.getItem('spotifyOnboardingV2Seen');

        if (!hasSeenNewTour) {
            // Show tour after a short delay to let page load
            setTimeout(() => {
                this.startTour();
            }, 1500);
        }
    }

    startTour() {
        if (this.isActive) return;

        this.isActive = true;
        this.currentStep = 0;

        // Show modal
        if (this.tourModal) {
            this.tourModal.style.display = 'block';
            document.body.style.overflow = 'hidden'; // Prevent scrolling
        }

        this.showStep(0);
        console.log('🎮 Onboarding tour started');
    }

    showStep(stepIndex) {
        if (stepIndex < 0 || stepIndex >= this.totalSteps) return;

        this.currentStep = stepIndex;
        const step = this.steps[stepIndex];

        // Update content
        const titleEl = document.getElementById('tourTitle');
        const descEl = document.getElementById('tourDescription');
        const indicatorEl = document.getElementById('tourStepIndicator');
        const nextBtn = document.getElementById('tourNext');
        const backBtn = document.getElementById('tourBack');

        if (titleEl) titleEl.textContent = step.title;
        if (descEl) descEl.textContent = step.content;
        if (indicatorEl) indicatorEl.textContent = `Step ${stepIndex + 1} of ${this.totalSteps}`;
        if (nextBtn) nextBtn.textContent = step.buttonText;

        // Show/hide back button
        if (backBtn) {
            backBtn.style.display = stepIndex > 0 ? 'block' : 'none';
        }

        // Highlight element if specified
        this.highlightElement(step.highlight);

        // Add step-specific animations
        this.animateStep(stepIndex);
    }

    highlightElement(selector) {
        // Remove previous highlights
        document.querySelectorAll('.tour-highlighted').forEach(el => {
            el.classList.remove('tour-highlighted');
        });

        const spotlight = document.getElementById('tourSpotlight');

        if (selector && spotlight) {
            const element = document.querySelector(selector);
            if (element) {
                element.classList.add('tour-highlighted');

                // Position spotlight
                const rect = element.getBoundingClientRect();
                spotlight.style.display = 'block';
                spotlight.style.top = (rect.top - 10) + 'px';
                spotlight.style.left = (rect.left - 10) + 'px';
                spotlight.style.width = (rect.width + 20) + 'px';
                spotlight.style.height = (rect.height + 20) + 'px';
            }
        } else if (spotlight) {
            spotlight.style.display = 'none';
        }
    }

    animateStep(stepIndex) {
        const modal = document.querySelector('.tour-modal');
        if (!modal) return;

        // Add entrance animation
        modal.style.transform = 'scale(0.8) translateY(20px)';
        modal.style.opacity = '0';

        setTimeout(() => {
            modal.style.transform = 'scale(1) translateY(0)';
            modal.style.opacity = '1';
        }, 100);
    }

    nextStep() {
        if (this.currentStep < this.totalSteps - 1) {
            this.showStep(this.currentStep + 1);
        } else {
            this.completeTour();
        }
    }

    previousStep() {
        if (this.currentStep > 0) {
            this.showStep(this.currentStep - 1);
        }
    }

    skipTour() {
        this.completeTour();
    }

    completeTour() {
        // Mark tour as seen
        localStorage.setItem('spotifyOnboardingV2Seen', 'true');

        // Hide modal
        if (this.tourModal) {
            this.tourModal.style.display = 'none';
            document.body.style.overflow = ''; // Restore scrolling
        }

        // Remove highlights
        document.querySelectorAll('.tour-highlighted').forEach(el => {
            el.classList.remove('tour-highlighted');
        });

        this.isActive = false;
        console.log('🎮 Onboarding tour completed');
    }

    // Public method to restart tour (for help/settings)
    restartTour() {
        this.startTour();
    }
}

// Initialize onboarding tour
let onboardingTour;

document.addEventListener('DOMContentLoaded', () => {
    // Wait for other systems to load first
    setTimeout(() => {
        onboardingTour = new OnboardingTour();
        console.log('🎮 Onboarding tour system loaded');
    }, 1000);
});

// Global function to restart tour
window.restartOnboardingTour = function() {
    if (onboardingTour) {
        onboardingTour.restartTour();
    }
};

console.log('🎮 Onboarding tour module loaded');