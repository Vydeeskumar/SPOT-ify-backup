from django.core.management.base import BaseCommand
from django.utils import timezone
from game.models import Song, LANGUAGE_CHOICES
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Create test songs for all languages'

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # Sample songs for each language
        test_songs = {
            'tamil': [
                {
                    'title': 'Vaseegara',
                    'artist': 'Bombay Jayashri',
                    'movie': 'Minnale',
                    'display_date': today
                },
                {
                    'title': 'Kadhal Rojave',
                    'artist': 'S.P. Balasubrahmanyam',
                    'movie': 'Roja',
                    'display_date': today + timedelta(days=1)
                },
                {
                    'title': 'Munbe Vaa',
                    'artist': 'Naresh Iyer',
                    'movie': 'Sillunu Oru Kaadhal',
                    'display_date': today + timedelta(days=2)
                }
            ],
            'english': [
                {
                    'title': 'Shape of You',
                    'artist': 'Ed Sheeran',
                    'movie': 'Single',
                    'display_date': today
                },
                {
                    'title': 'Blinding Lights',
                    'artist': 'The Weeknd',
                    'movie': 'After Hours',
                    'display_date': today + timedelta(days=1)
                },
                {
                    'title': 'Watermelon Sugar',
                    'artist': 'Harry Styles',
                    'movie': 'Fine Line',
                    'display_date': today + timedelta(days=2)
                }
            ],
            'hindi': [
                {
                    'title': 'Tum Hi Ho',
                    'artist': 'Arijit Singh',
                    'movie': 'Aashiqui 2',
                    'display_date': today
                },
                {
                    'title': 'Kesariya',
                    'artist': 'Arijit Singh',
                    'movie': 'Brahmastra',
                    'display_date': today + timedelta(days=1)
                },
                {
                    'title': 'Raataan Lambiyan',
                    'artist': 'Tanishk Bagchi',
                    'movie': 'Shershaah',
                    'display_date': today + timedelta(days=2)
                }
            ]
        }
        
        created_count = 0
        
        for language, songs in test_songs.items():
            self.stdout.write(f"\nCreating {language.title()} songs...")
            
            for song_data in songs:
                song, created = Song.objects.get_or_create(
                    title=song_data['title'],
                    language=language,
                    defaults={
                        'artist': song_data['artist'],
                        'movie': song_data['movie'],
                        'display_date': song_data['display_date'],
                        'is_used': False
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ Created: {song.title} - {song.artist} ({song.get_language_display()})"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  - Already exists: {song.title} ({song.get_language_display()})"
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎵 Successfully created {created_count} new songs across all languages!"
            )
        )
        
        # Show summary
        self.stdout.write("\n📊 Current song counts by language:")
        for lang_code, lang_name in LANGUAGE_CHOICES:
            count = Song.objects.filter(language=lang_code).count()
            self.stdout.write(f"  {lang_name}: {count} songs")
