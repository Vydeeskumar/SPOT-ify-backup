from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Max

# Language choices for the multi-language system
LANGUAGE_CHOICES = [
    ('tamil', 'Tamil'),
    ('english', 'English'),
    ('hindi', 'Hindi'),
]

class Song(models.Model):
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200)
    movie = models.CharField(max_length=200, null=True, blank=True)
    snippet = models.FileField(upload_to='song_snippets/')
    reveal_snippet = models.FileField(upload_to='song_snippets/', null=True, blank=True)
    image = models.ImageField(upload_to='song_images/', null=True, blank=True)
    display_date = models.DateField(null=True, blank=True)  # Removed unique=True for multi-language
    is_used = models.BooleanField(default=False)
    spotify_id = models.CharField(max_length=200, null=True, blank=True)

    # ✅ NEW: Language support for multi-language system
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='tamil')

    # ✅ NEW: Optional comma-separated duplicate Spotify IDs
    spotify_duplicates = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.title} - {self.artist} ({self.get_language_display()})"

    class Meta:
        # Ensure unique display_date per language
        unique_together = ['display_date', 'language']

    def get_all_spotify_ids(self):
        """Returns list of primary + duplicate Spotify IDs"""
        ids = [self.spotify_id.strip()] if self.spotify_id else []
        ids += [x.strip() for x in self.spotify_duplicates.split(",") if x.strip()]
        return ids


class UserScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    score = models.IntegerField()
    guess_time = models.FloatField()  # Time taken in seconds
    attempt_date = models.DateTimeField(auto_now_add=True)

    # ✅ NEW: Language support for multi-language leaderboards
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='tamil')

    class Meta:
        ordering = ['-score', 'guess_time']  # Order by highest score and lowest time

    def __str__(self):
        return f"{self.user.username} - {self.song.title} - {self.score} points ({self.get_language_display()})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # ✅ UPDATED: Language-specific stats
    # Tamil stats
    tamil_current_streak = models.IntegerField(default=0)
    tamil_longest_streak = models.IntegerField(default=0)
    tamil_total_points = models.IntegerField(default=0)
    tamil_total_songs_solved = models.IntegerField(default=0)
    tamil_average_time = models.FloatField(default=0)
    tamil_last_played_date = models.DateField(null=True, blank=True)

    # English stats
    english_current_streak = models.IntegerField(default=0)
    english_longest_streak = models.IntegerField(default=0)
    english_total_points = models.IntegerField(default=0)
    english_total_songs_solved = models.IntegerField(default=0)
    english_average_time = models.FloatField(default=0)
    english_last_played_date = models.DateField(null=True, blank=True)

    # Hindi stats
    hindi_current_streak = models.IntegerField(default=0)
    hindi_longest_streak = models.IntegerField(default=0)
    hindi_total_points = models.IntegerField(default=0)
    hindi_total_songs_solved = models.IntegerField(default=0)
    hindi_average_time = models.FloatField(default=0)
    hindi_last_played_date = models.DateField(null=True, blank=True)

    # Legacy fields (for backward compatibility)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    total_songs_solved = models.IntegerField(default=0)
    average_time = models.FloatField(default=0)
    last_played_date = models.DateField(null=True, blank=True)

    # ✅ Email reminders settings
    email_notifications_opt_in = models.BooleanField(default=True)
    email_notifications_notice_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_stats_for_language(self, language):
        """Get stats for a specific language"""
        return {
            'current_streak': getattr(self, f'{language}_current_streak'),
            'longest_streak': getattr(self, f'{language}_longest_streak'),
            'total_points': getattr(self, f'{language}_total_points'),
            'total_songs_solved': getattr(self, f'{language}_total_songs_solved'),
            'average_time': getattr(self, f'{language}_average_time'),
            'last_played_date': getattr(self, f'{language}_last_played_date'),
        }

    def update_stats(self, score, guess_time, date, language='tamil'):
        """Update stats for a specific language"""
        from datetime import timedelta

        # Get current language-specific stats
        current_streak_field = f'{language}_current_streak'
        longest_streak_field = f'{language}_longest_streak'
        total_points_field = f'{language}_total_points'
        total_songs_field = f'{language}_total_songs_solved'
        average_time_field = f'{language}_average_time'
        last_played_field = f'{language}_last_played_date'

        current_streak = getattr(self, current_streak_field)
        longest_streak = getattr(self, longest_streak_field)
        total_points = getattr(self, total_points_field)
        total_songs = getattr(self, total_songs_field)
        average_time = getattr(self, average_time_field)
        last_played_date = getattr(self, last_played_field)

        # Update streak
        if last_played_date:
            if last_played_date == date - timedelta(days=1):
                current_streak += 1
            elif last_played_date != date:
                current_streak = 1
        else:
            current_streak = 1

        # Update longest streak
        longest_streak = max(longest_streak, current_streak)

        # Update other stats
        total_points += score
        total_songs += 1
        if total_songs > 1:
            average_time = ((average_time * (total_songs - 1)) + guess_time) / total_songs
        else:
            average_time = guess_time

        # Set updated values
        setattr(self, current_streak_field, current_streak)
        setattr(self, longest_streak_field, longest_streak)
        setattr(self, total_points_field, total_points)
        setattr(self, total_songs_field, total_songs)
        setattr(self, average_time_field, average_time)
        setattr(self, last_played_field, date)

        # Also update legacy fields for backward compatibility (use Tamil as default)
        if language == 'tamil':
            self.current_streak = current_streak
            self.longest_streak = longest_streak
            self.total_points = total_points
            self.total_songs_solved = total_songs
            self.average_time = average_time
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

    # ✅ NEW: Language support for daily songs
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='tamil')

    class Meta:
        ordering = ['-date']
        # Ensure unique date per language
        unique_together = ['date', 'language']

    def __str__(self):
        return f"{self.song.title} - {self.date} ({self.get_language_display()})"


# Community Models
class Poll(models.Model):
    POLL_TYPES = [
        ('poll', 'Poll'),
        ('question', 'Question/Quiz'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    poll_type = models.CharField(max_length=20, choices=POLL_TYPES, default='poll')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def total_votes(self):
        return sum(option.votes.count() for option in self.options.all())

    def is_question(self):
        return self.poll_type == 'question' or any(keyword in self.title.lower() for keyword in ['question', 'quiz', 'mcq', 'trivia'])

class PollOption(models.Model):
    poll = models.ForeignKey(Poll, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.poll.title} - {self.text}"

class PollVote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    option = models.ForeignKey(PollOption, related_name='votes', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['poll', 'user']  # One vote per user per poll

class Feedback(models.Model):
    FEEDBACK_TYPES = [
        ('feedback', 'General Feedback'),
        ('bug', 'Bug Report'),
        ('suggestion', 'Feature Suggestion'),
        ('question', 'Question'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=FEEDBACK_TYPES, default='feedback')
    title = models.CharField(max_length=200)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    admin_response = models.TextField(blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_type_display()} - {self.title}"

    class Meta:
        ordering = ['-submitted_at']

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
