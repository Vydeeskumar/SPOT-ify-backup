from django.contrib import admin
from .models import Song, UserScore, UserProfile

@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('title', 'movie', 'artist', 'display_date', 'is_used')
    list_filter = ('is_used', 'display_date')
    search_fields = ('title', 'movie', 'artist')
    date_hierarchy = 'display_date'
    ordering = ('-display_date',)
    list_per_page = 20

@admin.register(UserScore)
class UserScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'song', 'score', 'guess_time', 'attempt_date')
    list_filter = ('attempt_date', 'score')
    search_fields = ('user__username', 'song__title')
    date_hierarchy = 'attempt_date'
    ordering = ('-attempt_date',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_streak', 'longest_streak', 'total_points', 'total_songs_solved')
    search_fields = ('user__username',)
    ordering = ('-total_points',)