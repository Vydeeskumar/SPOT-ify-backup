document.addEventListener('DOMContentLoaded', function() {
    console.log('Spotify search script loaded'); // Debug line
    const searchInput = document.querySelector('.spotify-search');
    console.log('Search input:', searchInput); // Debug line

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
            console.log('Got Spotify token'); // Debug line
        } catch (error) {
            console.error('Error getting Spotify token:', error);
        }
    }

    if (searchInput) {
        // Create dropdown container
        const dropdown = document.createElement('div');
        dropdown.className = 'spotify-dropdown';
        searchInput.parentNode.appendChild(dropdown);

        // Add search functionality
        let debounceTimeout;
        searchInput.addEventListener('input', async function() {
            console.log('Input event fired'); // Debug line
            clearTimeout(debounceTimeout);
            const query = this.value;

            debounceTimeout = setTimeout(async () => {
                if (query.length < 2) {
                    dropdown.style.display = 'none';
                    return;
                }

                if (!accessToken) await getSpotifyToken();

                try {
                    console.log('Searching for:', query); // Debug line
                    const response = await fetch(
                        `https://api.spotify.com/v1/search?q=${encodeURIComponent(query)}&type=track&market=IN&limit=5`,
                        {
                            headers: {
                                'Authorization': `Bearer ${accessToken}`
                            }
                        }
                    );

                    const data = await response.json();
                    console.log('Search results:', data); // Debug line
                    
                    dropdown.innerHTML = '';
                    data.tracks.items.forEach(track => {
                        const div = document.createElement('div');
                        div.className = 'spotify-result';
                        div.innerHTML = `
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <img src="${track.album.images[track.album.images.length-1].url}" 
                                     style="width: 40px; height: 40px; border-radius: 4px;">
                                <div>
                                    <strong>${track.name}</strong><br>
                                    <small>${track.artists[0].name} - ${track.album.name}</small>
                                </div>
                            </div>
                        `;
                        div.addEventListener('click', () => {
                            document.getElementById('id_title').value = track.name;
                            document.getElementById('id_artist').value = track.artists[0].name;
                            document.getElementById('id_movie').value = track.album.name;
                            document.getElementById('id_spotify_id').value = track.id;  // Add Spotify ID
                            console.log('Selected track ID:', track.id); // Debug line
                            dropdown.style.display = 'none';
                        });
                        dropdown.appendChild(div);
                    });
                    
                    dropdown.style.display = 'block';
                } catch (error) {
                    console.error('Error searching Spotify:', error);
                }
            }, 300);
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.spotify-search')) {
                dropdown.style.display = 'none';
            }
        });

        // Get token when page loads
        getSpotifyToken();
    }
});