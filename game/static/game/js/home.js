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

// 🎯 PERFECT ONBOARDING TOUR SYSTEM - GOD PROGRAMMER VERSION

const tourSteps = [
    {
        target: 'tour-vinyl-player',
        title: 'Welcome to SPOT-ify!',
        description: 'Let\'s learn how to play this amazing music guessing game! Click this vinyl record to play the song snippet.',
        position: 'bottom'
    },
    {
        target: 'tour-play-btn',
        title: 'Play Controls',
        description: 'Or use this button to control playback. The song will start playing automatically when you click it.',
        position: 'top'
    },
    {
        target: 'tour-timer',
        title: 'Timer',
        description: 'This timer shows how long you\'ve been guessing - faster guesses earn more points!',
        position: 'bottom'
    },
    {
        target: 'tour-points',
        title: 'Points System',
        description: 'Your points decrease over time, so guess quickly! Maximum 8 points for instant guesses.',
        position: 'bottom'
    },
    {
        target: 'tour-guess-input',
        title: 'Guess Input',
        description: 'Type your song guess here - smart suggestions will appear as you type to help you!',
        position: 'top'
    },
    {
        target: 'tour-submit-btn',
        title: 'Submit Guess',
        description: 'Click here to submit your guess and see if you got it right!',
        position: 'top'
    },
    {
        target: 'tour-giveup-btn',
        title: 'Give Up Option',
        description: 'If you\'re stuck, click here to reveal the answer - but you\'ll lose your streak!',
        position: 'top'
    },
    {
        target: '#languageOrb',
        title: 'Language Switcher',
        description: 'Click this floating orb to cycle between Tamil (Paatu), English (Song), and Hindi (Gaana) games - each language has different songs and separate leaderboards!',
        position: 'left'
    },
    {
        target: '.navbar',
        title: 'Navigation Menu',
        description: 'Use this menu to navigate between different pages and features.',
        position: 'bottom',
        action: 'openMobileNav'
    },
    {
        target: 'tour-archive-link',
        title: 'Archive Games',
        description: 'Play songs from previous days you missed! Note: Archive scores are just for fun - you\'ll see a \'hypothetical rank\' showing where you would have placed if you played that day, but it won\'t affect your real stats, streaks, or leaderboards. It\'s like time travel practice! 🕰️✨',
        position: 'bottom'
    },
    {
        target: 'tour-friends-link',
        title: 'Friends System',
        description: 'Add friends and compare your scores! Challenge each other and see who\'s the ultimate music master.',
        position: 'bottom'
    },
    {
        target: 'tour-profile-link',
        title: 'Your Profile',
        description: 'View your stats, streaks, achievements, and track your progress over time.',
        position: 'bottom'
    },
    {
        target: '#zombiebot-bubble',
        title: 'Zombiebot Assistant',
        description: 'Ask me questions about the game rules, features, and how everything works!',
        position: 'left'
    },
    {
        target: 'tour-leaderboard',
        title: 'Leaderboards',
        description: 'See how you rank against other players! Compete for the top spots in daily, weekly, and monthly rankings.',
        position: 'top'
    },
    {
        target: 'body',
        title: 'You\'re All Set!',
        description: 'That\'s everything! You\'re now ready to become a SPOT-ify master. Good luck and have fun guessing! 🎵🎯',
        position: 'center'
    }
];

class PerfectOnboardingTour {
    constructor() {
        this.currentStep = 0;
        this.isActive = false;
        this.dummyGameCreated = false;
        this.originalGameState = null;

        // DOM elements
        this.overlay = null;
        this.spotlight = null;
        this.tooltip = null;
        this.title = null;
        this.description = null;
        this.stepCounter = null;
        this.progressFill = null;
        this.nextBtn = null;
        this.skipBtn = null;
        this.closeBtn = null;

        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        this.overlay = document.getElementById('onboarding-tour');
        if (!this.overlay) {
            console.error('🎯 Tour overlay not found');
            return;
        }

        this.spotlight = this.overlay.querySelector('.tour-spotlight');
        this.tooltip = this.overlay.querySelector('.tour-tooltip');
        this.title = this.overlay.querySelector('.tour-title');
        this.description = this.overlay.querySelector('.tour-description');
        this.stepCounter = this.overlay.querySelector('.tour-step-counter');
        this.progressFill = this.overlay.querySelector('.tour-progress-fill');
        this.nextBtn = this.overlay.querySelector('#tour-next');
        this.skipBtn = this.overlay.querySelector('#tour-skip');
        this.closeBtn = this.overlay.querySelector('#tour-close');

        // Validate all elements exist
        const requiredElements = {
            spotlight: this.spotlight,
            tooltip: this.tooltip,
            title: this.title,
            description: this.description,
            stepCounter: this.stepCounter,
            progressFill: this.progressFill,
            nextBtn: this.nextBtn,
            skipBtn: this.skipBtn,
            closeBtn: this.closeBtn
        };

        for (const [name, element] of Object.entries(requiredElements)) {
            if (!element) {
                console.error(`🎯 Tour element missing: ${name}`);
            }
        }
    }

    bindEvents() {
        if (!this.overlay) return;

        // Button events with null checks
        if (this.nextBtn) {
            this.nextBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.nextStep();
            });
        }

        if (this.skipBtn) {
            this.skipBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.endTour();
            });
        }

        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.endTour();
            });
        }

        // Close on overlay click (but not tooltip click)
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) {
                this.endTour();
            }
        });

        // Keyboard navigation
        this.keyboardHandler = (e) => {
            if (!this.isActive) return;

            if (e.key === 'Escape') {
                e.preventDefault();
                this.endTour();
            } else if (e.key === 'ArrowRight' || e.key === 'Enter') {
                e.preventDefault();
                this.nextStep();
            } else if (e.key === 'ArrowLeft') {
                e.preventDefault();
                this.previousStep();
            }
        };

        document.addEventListener('keydown', this.keyboardHandler);
    }

    createDummyGame() {
        if (this.dummyGameCreated) return;

        // Save original game state
        const gameContainer = document.getElementById('game-container');
        const gameView = document.getElementById('game-view');

        if (gameContainer) {
            this.originalGameState = {
                gameContainer: gameContainer.cloneNode(true),
                display: gameContainer.style.display
            };
        }

        // Create dummy game elements with tour IDs
        const dummyHTML = `
            <div id="tour-dummy-game" style="position: relative; z-index: 1;">
                <div class="game-header">
                    <h2>Today's Demo Song</h2>
                    <div id="tour-timer" class="timer">00:00</div>
                    <div id="tour-points" class="points-indicator">Points: <span class="points-value">8</span></div>
                </div>

                <div id="tour-vinyl-player" class="vinyl-player">
                    <div class="vinyl-record">
                        <div class="vinyl-grooves"></div>
                        <div class="vinyl-center">
                            <i class="fas fa-play"></i>
                        </div>
                    </div>
                </div>

                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: 30%;"></div>
                    </div>
                </div>

                <div class="game-controls">
                    <button id="tour-play-btn" class="btn btn-play">
                        <i class="fas fa-play"></i> Play
                    </button>
                    <button id="tour-giveup-btn" class="btn btn-giveup">
                        <i class="fas fa-flag"></i> Give Up
                    </button>
                </div>

                <form class="guess-form">
                    <div class="mb-3 position-relative">
                        <input type="text" id="tour-guess-input" class="form-control"
                               placeholder="Enter song name" value="Demo Song Name">
                        <div class="suggestions-container">
                            <div class="suggestion-item">Demo Song 1</div>
                            <div class="suggestion-item">Demo Song 2</div>
                        </div>
                    </div>
                    <button type="button" id="tour-submit-btn" class="btn btn-play">Submit Guess</button>
                </form>
            </div>

            <!-- Dummy Navigation Links -->
            <div id="tour-nav-links" style="position: absolute; top: -9999px;">
                <a id="tour-archive-link" href="#" class="nav-link">Archive</a>
                <a id="tour-friends-link" href="#" class="nav-link">Friends</a>
                <a id="tour-profile-link" href="#" class="nav-link">Profile</a>
            </div>

            <!-- Dummy Leaderboard -->
            <div id="tour-leaderboard" style="position: absolute; top: -9999px;">
                <div class="leaderboard-container">
                    <h3>Leaderboard</h3>
                    <div class="leaderboard-item">Demo Player - 100 pts</div>
                </div>
            </div>
        `;

        // Insert dummy game
        if (gameContainer) {
            gameContainer.style.display = 'none';
            gameContainer.insertAdjacentHTML('afterend', dummyHTML);
        } else if (gameView) {
            gameView.style.display = 'none';
            gameView.insertAdjacentHTML('afterend', dummyHTML);
        } else {
            // Fallback: insert into game main
            const gameMain = document.getElementById('game-main');
            if (gameMain) {
                gameMain.insertAdjacentHTML('beforeend', dummyHTML);
            }
        }

        this.dummyGameCreated = true;
        console.log('🎯 Dummy game created for tour');
    }

    removeDummyGame() {
        if (!this.dummyGameCreated) return;

        // Remove dummy elements
        const dummyGame = document.getElementById('tour-dummy-game');
        const dummyNav = document.getElementById('tour-nav-links');
        const dummyLeaderboard = document.getElementById('tour-leaderboard');

        if (dummyGame) dummyGame.remove();
        if (dummyNav) dummyNav.remove();
        if (dummyLeaderboard) dummyLeaderboard.remove();

        // Restore original game
        if (this.originalGameState) {
            const gameContainer = document.getElementById('game-container');
            if (gameContainer) {
                gameContainer.style.display = this.originalGameState.display;
            }
        }

        this.dummyGameCreated = false;
        console.log('🎯 Dummy game removed');
    }

    start() {
        if (!this.overlay || this.isActive) {
            console.warn('🎯 Tour already active or overlay missing');
            return;
        }

        console.log('🎯 Starting perfect onboarding tour...');

        // Reset state
        this.currentStep = 0;
        this.isActive = true;

        // Create dummy game environment
        this.createDummyGame();

        // Disable real game interactions
        this.disableRealGame();

        // Show overlay
        this.overlay.style.display = 'block';

        // Small delay for smooth animation
        setTimeout(() => {
            if (this.overlay) {
                this.overlay.classList.add('active');
                this.showStep(0);
            }
        }, 150);

        console.log('🎯 Perfect onboarding tour started');
    }

    disableRealGame() {
        // Disable all real game interactions
        const realGameElements = [
            '#vinyl-player',
            '#playPauseBtn',
            '#giveUpBtn',
            '#guess-input',
            '#guess-form',
            'button[type="submit"]'
        ];

        realGameElements.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                el.style.pointerEvents = 'none';
                el.style.opacity = '0.3';
                el.setAttribute('data-tour-disabled', 'true');
            });
        });

        // Mute and pause all audio
        const audioElements = document.querySelectorAll('audio');
        audioElements.forEach(audio => {
            audio.muted = true;
            audio.pause();
            audio.setAttribute('data-tour-muted', 'true');
        });
    }

    enableRealGame() {
        // Re-enable all real game interactions
        const disabledElements = document.querySelectorAll('[data-tour-disabled="true"]');
        disabledElements.forEach(el => {
            el.style.pointerEvents = 'auto';
            el.style.opacity = '1';
            el.removeAttribute('data-tour-disabled');
        });

        // Unmute audio
        const mutedAudio = document.querySelectorAll('[data-tour-muted="true"]');
        mutedAudio.forEach(audio => {
            audio.muted = false;
            audio.removeAttribute('data-tour-muted');
        });
    }

    getTargetElement(targetId) {
        // Smart element targeting with fallbacks
        let element = null;

        if (targetId === 'body') {
            return document.body;
        }

        // Try direct ID first
        element = document.getElementById(targetId);
        if (element) return element;

        // Try as class
        element = document.querySelector(`.${targetId}`);
        if (element) return element;

        // Try as selector
        element = document.querySelector(targetId);
        if (element) return element;

        console.warn(`🎯 Target element not found: ${targetId}`);
        return null;
    }

    showStep(stepIndex) {
        if (stepIndex >= tourSteps.length) {
            this.endTour();
            return;
        }

        this.currentStep = stepIndex;
        const step = tourSteps[stepIndex];

        console.log(`🎯 Showing step ${stepIndex + 1}: ${step.title}`);

        // Handle special actions
        if (step.action === 'openMobileNav') {
            this.openMobileNavigation();
        }

        // Get target element
        const target = this.getTargetElement(step.target);

        // Update content with null checks
        if (this.title) this.title.textContent = step.title;
        if (this.description) this.description.textContent = step.description;
        if (this.stepCounter) this.stepCounter.textContent = `${stepIndex + 1} of ${tourSteps.length}`;
        if (this.progressFill) {
            this.progressFill.style.width = `${((stepIndex + 1) / tourSteps.length) * 100}%`;
        }

        // Update button text and visibility
        if (this.nextBtn) {
            if (stepIndex === tourSteps.length - 1) {
                this.nextBtn.textContent = 'Finish Tour';
                this.nextBtn.classList.add('tour-finish');
            } else {
                this.nextBtn.textContent = 'Next';
                this.nextBtn.classList.remove('tour-finish');
            }
            this.nextBtn.style.display = 'block';
        }

        if (this.skipBtn) {
            this.skipBtn.style.display = stepIndex === tourSteps.length - 1 ? 'none' : 'block';
        }

        // Position elements
        this.positionElements(target, step.position);

        // Highlight target
        this.highlightElement(target);

        // Ensure tooltip is visible
        if (this.tooltip) {
            this.tooltip.style.opacity = '1';
            this.tooltip.style.visibility = 'visible';
        }

        console.log(`🎯 Step ${stepIndex + 1} displayed successfully`);
    }

    nextStep() {
        if (this.currentStep < tourSteps.length - 1) {
            this.showStep(this.currentStep + 1);
        } else {
            this.endTour();
        }
    }

    previousStep() {
        if (this.currentStep > 0) {
            this.showStep(this.currentStep - 1);
        }
    }

    openMobileNavigation() {
        // Open mobile navigation if it exists
        const navToggle = document.querySelector('.navbar-toggler, .nav-toggle, .mobile-menu-toggle');
        const navCollapse = document.querySelector('.navbar-collapse, .nav-collapse');

        if (navToggle && navCollapse) {
            // Check if nav is collapsed (mobile)
            if (!navCollapse.classList.contains('show') && window.innerWidth <= 768) {
                navToggle.click();
                console.log('🎯 Opened mobile navigation');
            }
        }
    }

    positionElements(target, position) {
        if (!this.spotlight || !this.tooltip) return;

        if (!target || target === document.body) {
            // Center position for final step
            this.spotlight.style.display = 'none';
            this.tooltip.style.top = '50%';
            this.tooltip.style.left = '50%';
            this.tooltip.style.transform = 'translate(-50%, -50%)';
            this.tooltip.className = 'tour-tooltip';
            return;
        }

        const rect = target.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        const isMobile = viewportWidth <= 768;

        // Position spotlight
        this.spotlight.style.display = 'block';
        this.spotlight.style.top = `${rect.top - 8}px`;
        this.spotlight.style.left = `${rect.left - 8}px`;
        this.spotlight.style.width = `${rect.width + 16}px`;
        this.spotlight.style.height = `${rect.height + 16}px`;

        if (isMobile) {
            // Mobile: Always position tooltip at bottom
            this.tooltip.style.position = 'fixed';
            this.tooltip.style.bottom = '20px';
            this.tooltip.style.left = '50%';
            this.tooltip.style.transform = 'translateX(-50%)';
            this.tooltip.style.top = 'auto';
            this.tooltip.className = 'tour-tooltip mobile-position';
            return;
        }

        // Desktop positioning
        const tooltipRect = this.tooltip.getBoundingClientRect();
        let tooltipTop, tooltipLeft;
        let arrowClass = 'tour-tooltip';

        switch (position) {
            case 'top':
                tooltipTop = rect.top - tooltipRect.height - 30;
                tooltipLeft = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
                arrowClass += ' arrow-bottom';
                break;
            case 'bottom':
                tooltipTop = rect.bottom + 30;
                tooltipLeft = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
                arrowClass += ' arrow-top';
                break;
            case 'left':
                tooltipTop = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
                tooltipLeft = rect.left - tooltipRect.width - 30;
                arrowClass += ' arrow-right';
                break;
            case 'right':
                tooltipTop = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
                tooltipLeft = rect.right + 30;
                arrowClass += ' arrow-left';
                break;
            default:
                tooltipTop = rect.bottom + 30;
                tooltipLeft = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
                arrowClass += ' arrow-top';
        }

        // Keep tooltip within viewport
        const margin = 20;
        tooltipTop = Math.max(margin, Math.min(tooltipTop, viewportHeight - tooltipRect.height - margin));
        tooltipLeft = Math.max(margin, Math.min(tooltipLeft, viewportWidth - tooltipRect.width - margin));

        this.tooltip.style.position = 'absolute';
        this.tooltip.style.top = `${tooltipTop}px`;
        this.tooltip.style.left = `${tooltipLeft}px`;
        this.tooltip.style.bottom = 'auto';
        this.tooltip.style.transform = 'none';
        this.tooltip.className = arrowClass;
    }

    highlightElement(target) {
        // Remove previous highlights
        document.querySelectorAll('.tour-highlight').forEach(el => {
            el.classList.remove('tour-highlight');
        });

        // Add highlight to current target
        if (target && target !== document.body) {
            target.classList.add('tour-highlight');
        }
    }

    nextStep() {
        this.currentStep++;
        this.showStep(this.currentStep);
    }

    endTour() {
        if (!this.isActive) return;

        console.log('🎯 Ending perfect onboarding tour...');

        this.isActive = false;

        // Remove keyboard listener
        if (this.keyboardHandler) {
            document.removeEventListener('keydown', this.keyboardHandler);
        }

        // Re-enable real game
        this.enableRealGame();

        // Remove dummy game
        this.removeDummyGame();

        // Remove highlights
        document.querySelectorAll('.tour-highlight').forEach(el => {
            el.classList.remove('tour-highlight');
        });

        // Close mobile nav if opened
        const navCollapse = document.querySelector('.navbar-collapse.show');
        if (navCollapse && window.innerWidth <= 768) {
            const navToggle = document.querySelector('.navbar-toggler');
            if (navToggle) navToggle.click();
        }

        // Hide overlay with animation
        if (this.overlay) {
            this.overlay.classList.remove('active');
            setTimeout(() => {
                this.overlay.style.display = 'none';
            }, 400);
        }

        // Mark tour as completed
        localStorage.setItem('spotifyTourCompleted', 'true');
        console.log('🎯 Perfect onboarding tour completed successfully!');
    }

    openMobileNavigation() {
        const navToggle = document.querySelector('.navbar-toggler, .nav-toggle, .mobile-menu-toggle');
        const navCollapse = document.querySelector('.navbar-collapse, .nav-collapse');

        if (navToggle && navCollapse && window.innerWidth <= 768) {
            if (!navCollapse.classList.contains('show')) {
                navToggle.click();
                console.log('🎯 Opened mobile navigation for tour');

                // Wait for animation and assign IDs
                setTimeout(() => {
                    const navLinks = navCollapse.querySelectorAll('.nav-link');
                    navLinks.forEach(link => {
                        if (link.href.includes('archive')) {
                            link.id = 'tour-archive-link';
                        } else if (link.href.includes('friends')) {
                            link.id = 'tour-friends-link';
                        } else if (link.href.includes('profile')) {
                            link.id = 'tour-profile-link';
                        }
                    });
                }, 300);
            }
        }
    }

    shouldShowTour() {
        // Check if user has already played today by looking for game view vs result view
        const gameView = document.getElementById('game-view');
        const gameContainer = document.getElementById('game-container');
        const hasPlayedToday = gameView && gameView.style.display === 'none';

        // Don't show tour if already completed
        const tourCompleted = localStorage.getItem('spotifyTourCompleted');

        console.log('🎯 Tour check:', {
            hasPlayedToday,
            tourCompleted,
            gameViewDisplay: gameView?.style.display,
            gameViewExists: !!gameView
        });

        // Only show tour for new users who haven't played today and haven't completed tour
        return !hasPlayedToday && !tourCompleted;
    }
}

// Initialize tour system
let onboardingTour;

document.addEventListener('DOMContentLoaded', () => {
    onboardingTour = new PerfectOnboardingTour();

    console.log('🎯 Tour system initialized');

    // Auto-start tour for new users after a short delay
    setTimeout(() => {
        const shouldShow = onboardingTour.shouldShowTour();
        console.log('🎯 Should show tour:', shouldShow);

        if (shouldShow) {
            const gameView = document.getElementById('game-view');
            const isGameViewVisible = gameView && gameView.style.display !== 'none';

            console.log('🎯 Game view check:', {
                gameViewExists: !!gameView,
                isVisible: isGameViewVisible,
                display: gameView?.style.display
            });

            if (isGameViewVisible) {
                console.log('🎯 Starting tour...');
                onboardingTour.start();
            } else {
                console.log('🎯 Tour not started - game view not visible');
            }
        } else {
            console.log('🎯 Tour not started - conditions not met');
        }
    }, 2000); // 2 second delay to let page load
});

// Global function to manually start tour (for testing or settings)
window.startOnboardingTour = function() {
    if (onboardingTour) {
        console.log('🎯 Manually starting tour...');
        onboardingTour.start();
    }
};

// Global function to reset tour (for testing)
window.resetTour = function() {
    localStorage.removeItem('spotifyTourCompleted');
    console.log('🎯 Tour reset - will show on next page load');
};

console.log('🎯 Onboarding tour system loaded');