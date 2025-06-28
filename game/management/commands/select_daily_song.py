from django.core.management.base import BaseCommand
from django.utils import timezone
from game.models import Song
import random

class Command(BaseCommand):
    help = 'Selects a random unused song for the day'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        
        # Check if a song is already selected for today
        if Song.objects.filter(display_date=today).exists():
            self.stdout.write(self.style.WARNING('A song is already selected for today'))
            return

        # Get all unused songs
        unused_songs = Song.objects.filter(is_used=False)
        
        if unused_songs.exists():
            # Randomly select one song
            today_song = random.choice(unused_songs)
            today_song.display_date = today
            today_song.is_used = True
            today_song.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully selected song: {today_song.title}')
            )
        else:
            # Reset all songs if none are unused
            Song.objects.all().update(is_used=False)
            self.stdout.write(
                self.style.WARNING('All songs reset to unused state. Run command again to select a song.')
            )