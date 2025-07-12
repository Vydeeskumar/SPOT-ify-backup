from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from game.models import Song, UserScore, UserProfile, DailySong, LANGUAGE_CHOICES
from datetime import date

class MultiLanguageTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.today = timezone.now().date()
        
        # Create test songs for each language
        self.songs = {}
        for lang_code, lang_name in LANGUAGE_CHOICES:
            song = Song.objects.create(
                title=f'Test Song {lang_name}',
                artist=f'Test Artist {lang_name}',
                movie=f'Test Movie {lang_name}',
                language=lang_code,
                display_date=self.today,
                is_used=False
            )
            self.songs[lang_code] = song

    def test_language_urls_accessible(self):
        """Test that all language URLs are accessible"""
        for lang_code, lang_name in LANGUAGE_CHOICES:
            url = f'/{lang_code}/'
            response = self.client.get(url, follow=True)
            # Should redirect to login since @login_required
            self.assertIn(response.status_code, [200, 302])
            # Check that we end up at login page
            final_url = response.redirect_chain[-1][0] if response.redirect_chain else response.request['PATH_INFO']
            self.assertTrue('/accounts/login/' in final_url or '/login/' in final_url)

    def test_language_specific_songs(self):
        """Test that each language shows its own songs"""
        self.client.login(username='testuser', password='testpass123')
        
        for lang_code, lang_name in LANGUAGE_CHOICES:
            url = f'/{lang_code}/'
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            
            # Check that the correct song is shown
            expected_song = self.songs[lang_code]
            self.assertContains(response, expected_song.title)
            
            # Check that songs from other languages are NOT shown
            for other_lang, other_song in self.songs.items():
                if other_lang != lang_code:
                    self.assertNotContains(response, other_song.title)

    def test_language_specific_leaderboards(self):
        """Test that leaderboards are language-specific"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create scores for different languages
        for lang_code, song in self.songs.items():
            UserScore.objects.create(
                user=self.user,
                song=song,
                score=100,
                guess_time=5.0,
                language=lang_code
            )
        
        # Test leaderboard for each language
        for lang_code, lang_name in LANGUAGE_CHOICES:
            url = f'/{lang_code}/leaderboard/'
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            
            # Should contain scores for this language
            self.assertContains(response, 'testuser')
            self.assertContains(response, '100')

    def test_language_context_variables(self):
        """Test that language context variables are set correctly"""
        self.client.login(username='testuser', password='testpass123')
        
        for lang_code, lang_name in LANGUAGE_CHOICES:
            url = f'/{lang_code}/'
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            
            # Check context variables
            self.assertEqual(response.context['current_language'], lang_code)
            self.assertEqual(response.context['language_display'], lang_name)

    def test_user_profile_language_stats(self):
        """Test that user profile tracks language-specific stats"""
        profile = UserProfile.objects.create(user=self.user)
        
        # Update stats for Tamil
        profile.update_stats(100, 5.0, self.today, 'tamil')
        self.assertEqual(profile.tamil_total_points, 100)
        self.assertEqual(profile.tamil_current_streak, 1)
        
        # Update stats for English
        profile.update_stats(80, 7.0, self.today, 'english')
        self.assertEqual(profile.english_total_points, 80)
        self.assertEqual(profile.english_current_streak, 1)
        
        # Tamil stats should remain unchanged
        self.assertEqual(profile.tamil_total_points, 100)

    def test_daily_song_language_separation(self):
        """Test that daily songs are separate for each language"""
        for lang_code, song in self.songs.items():
            daily_song = DailySong.objects.create(
                song=song,
                date=self.today,
                language=lang_code
            )
            self.assertEqual(daily_song.language, lang_code)
        
        # Should have 3 daily songs for today (one per language)
        daily_songs_count = DailySong.objects.filter(date=self.today).count()
        self.assertEqual(daily_songs_count, 3)

    def test_admin_language_filtering(self):
        """Test that admin interface filters by language"""
        # Create admin user
        admin_user = User.objects.create_superuser(
            username='admin',
            password='adminpass123',
            email='admin@test.com'
        )
        self.client.login(username='admin', password='adminpass123')
        
        # Test admin song list
        response = self.client.get('/admin/game/song/')
        self.assertEqual(response.status_code, 200)
        
        # Should show all songs with language indicators
        for song in self.songs.values():
            self.assertContains(response, song.title)

    def test_language_switcher_urls(self):
        """Test that language switcher generates correct URLs"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test home page for each language
        for lang_code, lang_name in LANGUAGE_CHOICES:
            url = f'/{lang_code}/'
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            
            # Check that language switcher contains links to other languages
            for other_lang, other_name in LANGUAGE_CHOICES:
                if other_lang != lang_code:
                    expected_url = f'/{other_lang}/'
                    self.assertContains(response, expected_url)

    def test_root_url_redirect(self):
        """Test that root URL redirects to Tamil"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/tamil/')

class MultiLanguageAdminTestCase(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='adminpass123',
            email='admin@test.com'
        )
        self.client = Client()
        self.client.login(username='admin', password='adminpass123')

    def test_language_dashboard_access(self):
        """Test that language dashboard is accessible"""
        response = self.client.get('/admin/language-dashboard/')
        self.assertEqual(response.status_code, 200)
        
        # Should contain language tabs
        for lang_code, lang_name in LANGUAGE_CHOICES:
            self.assertContains(response, lang_name)

    def test_language_stats_api(self):
        """Test language stats API endpoint"""
        for lang_code, lang_name in LANGUAGE_CHOICES:
            url = f'/admin/language-stats/{lang_code}/'
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertEqual(data['language'], lang_code)
            self.assertIn('total_songs', data)
            self.assertIn('used_songs', data)
