from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Max

class Song(models.Model):
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200)
    movie = models.CharField(max_length=200, null=True, blank=True)
    snippet = models.FileField(upload_to='song_snippets/')
    reveal_snippet = models.FileField(upload_to='song_snippets/', null=True, blank=True)  
    image = models.ImageField(upload_to='song_images/', null=True, blank=True) 
    display_date = models.DateField(unique=True, null=True, blank=True)
    is_used = models.BooleanField(default=False)
    spotify_id = models.CharField(max_length=200, null=True, blank=True) 

    def __str__(self):
        return f"{self.title} - {self.artist}"

class UserScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    score = models.IntegerField()
    guess_time = models.FloatField()  # Time taken in seconds
    attempt_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score', 'guess_time']  # Order by highest score and lowest time

    def __str__(self):
        return f"{self.user.username} - {self.song.title} - {self.score} points"
    

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    total_songs_solved = models.IntegerField(default=0)
    average_time = models.FloatField(default=0)
    last_played_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def update_stats(self, score, guess_time, date):
        from datetime import timedelta
        
        # Update streak
        if self.last_played_date:
            if self.last_played_date == date - timedelta(days=1):
                self.current_streak += 1
            elif self.last_played_date != date:
                self.current_streak = 1
        else:
            self.current_streak = 1

        # Update longest streak
        self.longest_streak = max(self.longest_streak, self.current_streak)
        
        # Update other stats
        self.total_points += score
        self.total_songs_solved += 1
        self.average_time = ((self.average_time * (self.total_songs_solved - 1)) + guess_time) / self.total_songs_solved
        self.last_played_date = date
        self.save()

class Friendship(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships')
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_of')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'friend']
        
    def __str__(self):
        return f"{self.user.username} -> {self.friend.username}"
    
class DailySong(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    date = models.DateField()
    total_players = models.IntegerField(default=0)
    average_time = models.FloatField(null=True)
    

    class Meta:
        ordering = ['-date']