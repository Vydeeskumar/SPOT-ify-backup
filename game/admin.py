from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from .models import Song, UserScore, UserProfile
from django import forms

class SongAdminForm(forms.ModelForm):
    spotify_search = forms.CharField(
        required=False,
        label='Search Spotify',
        widget=forms.TextInput(attrs={'class': 'spotify-search'}),
        help_text='Search for a song on Spotify to auto-fill details'
    )

    class Meta:
        model = Song
        fields = '__all__'

# Customize Admin Site
class SpotifyPaatuAdminSite(AdminSite):
    site_header = 'SPOT-ify the Paatu Administration'
    site_title = 'SPOT-ify the Paatu Admin'
    index_title = 'Game Management'

admin_site = SpotifyPaatuAdminSite(name='spotifyadmin')

# Song Admin
@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    form = SongAdminForm 
    list_display = ('song_title_with_movie', 'artist', 'display_date', 'status_tag')
    list_filter = ('is_used', 'display_date')
    search_fields = ('title', 'movie', 'artist')
    date_hierarchy = 'display_date'
    ordering = ('-display_date',)
    list_per_page = 20
    fieldsets = (
        ('Spotify Search', {
            'fields': ('spotify_search',),
            'classes': ('wide',)
        }),

        ('Song Details', {
            'fields': ('title', 'artist', 'movie', 'spotify_id'),
            'classes': ('wide',)
        }),
        ('Media', {
            'fields': ('snippet', 'reveal_snippet', 'image'),  # Added reveal_snippet here
            'classes': ('wide',)
        }),
        ('Schedule', {
            'fields': ('display_date', 'is_used'),
            'classes': ('wide',)
        }),
    )
    class Media:
        js = ('game/admin/js/spotify-search.js',)  # Update this path
        css = {
            'all': ('game/admin/css/spotify-search.css',)  # Update this path
        }


    def song_title_with_movie(self, obj):
        return format_html(
            '<strong>{}</strong> <span style="color: #666;">from {}</span>',
            obj.title,
            obj.movie
        )
    song_title_with_movie.short_description = 'Song'

    def status_tag(self, obj):
        if obj.is_used:
            return format_html(
                '<span style="background-color: #e8f5e9; color: #2e7d32; padding: 3px 10px; border-radius: 10px;">Used</span>'
            )
        return format_html(
            '<span style="background-color: #fff3e0; color: #f57c00; padding: 3px 10px; border-radius: 10px;">Pending</span>'
        )
    status_tag.short_description = 'Status'

# User Score Admin
@admin.register(UserScore)
class UserScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'song_details', 'score_display', 'formatted_time', 'attempt_date')
    list_filter = ('attempt_date', 'score')
    search_fields = ('user__username', 'song__title')
    date_hierarchy = 'attempt_date'
    ordering = ('-attempt_date',)
    
    def song_details(self, obj):
        return format_html(
            '{} <span style="color: #666;">from {}</span>',
            obj.song.title,
            obj.song.movie
        )
    song_details.short_description = 'Song'

    def score_display(self, obj):
        color = '#2e7d32' if obj.score > 5 else '#f57c00' if obj.score > 2 else '#c62828'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} points</span>',
            color,
            obj.score
        )
    score_display.short_description = 'Score'

    def formatted_time(self, obj):
        return f"{obj.guess_time:.1f}s"
    formatted_time.short_description = 'Time Taken'

# User Profile Admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'streak_display', 'total_points', 'total_songs_solved', 'avg_time_display')
    search_fields = ('user__username',)
    ordering = ('-total_points',)
    
    def streak_display(self, obj):
        return format_html(
            '🔥 Current: {} | 🏆 Best: {}',
            obj.current_streak,
            obj.longest_streak
        )
    streak_display.short_description = 'Streaks'

    def avg_time_display(self, obj):
        return f"{obj.average_time:.1f}s"
    avg_time_display.short_description = 'Avg Time'

# Unregister default User admin and register custom one
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'date_joined', 'last_login', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)