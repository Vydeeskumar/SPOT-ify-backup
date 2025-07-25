from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseRedirect
from .models import Song, UserScore, UserProfile, DailySong, LANGUAGE_CHOICES, Poll, PollOption, PollVote, Feedback, Announcement
from django import forms
from django.utils import timezone
from datetime import date

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default language if not specified
        if not self.instance.pk and 'language' not in self.initial:
            self.initial['language'] = 'tamil'

# Customize Admin Site
class SpotifyPaatuAdminSite(AdminSite):
    site_header = 'SPOT-ify Multi-Language Administration'
    site_title = 'SPOT-ify Admin'
    index_title = 'Multi-Language Game Management'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('language-dashboard/', self.admin_view(self.language_dashboard_view), name='language_dashboard'),
            path('set-daily-song/', self.admin_view(self.set_daily_song_view), name='set_daily_song'),
            path('language-stats/<str:language>/', self.admin_view(self.language_stats_view), name='language_stats'),
        ]
        return custom_urls + urls

    def index(self, request, extra_context=None):
        """Override admin index to add custom dashboard link"""
        extra_context = extra_context or {}
        extra_context['show_language_dashboard'] = True
        return super().index(request, extra_context)

    def language_dashboard_view(self, request):
        """Multi-language dashboard with tabs"""
        context = {
            'title': 'Multi-Language Dashboard',
            'languages': LANGUAGE_CHOICES,
            'today': timezone.now().date(),
        }

        # Get today's songs for each language
        today_songs = {}
        for lang_code, lang_name in LANGUAGE_CHOICES:
            song = Song.objects.filter(
                display_date=timezone.now().date(),
                language=lang_code
            ).first()
            today_songs[lang_code] = song

        context['today_songs'] = today_songs

        return render(request, 'admin/language_dashboard.html', context)

    def set_daily_song_view(self, request):
        """Set daily song for a specific language"""
        if request.method == 'POST':
            language = request.POST.get('language')
            song_id = request.POST.get('song_id')
            date_str = request.POST.get('date')

            try:
                song = Song.objects.get(id=song_id, language=language)
                target_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()

                # Update song's display date
                song.display_date = target_date
                song.save()

                # Create or update DailySong entry
                daily_song, created = DailySong.objects.get_or_create(
                    date=target_date,
                    language=language,
                    defaults={'song': song}
                )
                if not created:
                    daily_song.song = song
                    daily_song.save()

                return JsonResponse({'success': True, 'message': f'Daily song set for {language}'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

        return JsonResponse({'success': False, 'error': 'Invalid request'})

    def language_stats_view(self, request, language):
        """Get stats for a specific language"""
        today = timezone.now().date()

        # Get today's song
        today_song = Song.objects.filter(
            display_date=today,
            language=language
        ).first()

        stats = {
            'language': language,
            'today_song': today_song.title if today_song else None,
            'total_songs': Song.objects.filter(language=language).count(),
            'used_songs': Song.objects.filter(language=language, is_used=True).count(),
        }

        if today_song:
            stats['today_players'] = UserScore.objects.filter(
                song=today_song,
                attempt_date__date=today,
                language=language
            ).count()

        return JsonResponse(stats)

admin_site = SpotifyPaatuAdminSite(name='spotifyadmin')

# Song Admin
@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    form = SongAdminForm
    list_display = ('song_title_with_movie', 'artist', 'language_tag', 'display_date', 'status_tag')
    list_filter = ('language', 'is_used', 'display_date')
    search_fields = ('title', 'movie', 'artist')
    date_hierarchy = 'display_date'
    ordering = ('-display_date', 'language')
    list_per_page = 20
    fieldsets = (
        ('Spotify Search', {
            'fields': ('spotify_search',),
            'classes': ('wide',)
        }),

        ('Song Details', {
            'fields': ('title', 'artist', 'movie', 'language', 'spotify_id', 'spotify_duplicates'),
            'classes': ('wide',)
        }),
        ('Media', {
            'fields': ('snippet', 'reveal_snippet', 'image'),
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
        if obj.movie:
            return format_html(
                '<strong>{}</strong> <span style="color: #666;">from {}</span>',
                obj.title,
                obj.movie
            )
        else:
            return format_html(
                '<strong>{}</strong>',
                obj.title
            )
    song_title_with_movie.short_description = 'Song'

    def language_tag(self, obj):
        colors = {
            'tamil': '#B026FF',
            'english': '#1E90FF',
            'hindi': '#FF6B35'
        }
        color = colors.get(obj.language, '#666')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 10px; font-size: 0.8em;">{}</span>',
            color,
            obj.get_language_display()
        )
    language_tag.short_description = 'Language'

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
    list_display = ('user', 'song_details', 'language_tag', 'score_display', 'formatted_time', 'attempt_date')
    list_filter = ('language', 'attempt_date', 'score')
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

    def language_tag(self, obj):
        colors = {
            'tamil': '#B026FF',
            'english': '#1E90FF',
            'hindi': '#FF6B35'
        }
        color = colors.get(obj.language, '#666')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 8px; font-size: 0.75em;">{}</span>',
            color,
            obj.get_language_display()
        )
    language_tag.short_description = 'Lang'

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

# Add language dashboard to default admin
from django.urls import path as admin_path
from django.shortcuts import render as admin_render

def language_dashboard_simple(request):
    """Simple language dashboard for default admin"""
    context = {
        'title': 'Multi-Language Dashboard',
        'languages': LANGUAGE_CHOICES,
        'today': timezone.now().date(),
    }

    # Get today's songs for each language
    today_songs = {}
    for lang_code, lang_name in LANGUAGE_CHOICES:
        song = Song.objects.filter(
            display_date=timezone.now().date(),
            language=lang_code
        ).first()
        today_songs[lang_code] = song

    context['today_songs'] = today_songs
    return admin_render(request, 'admin/simple_language_dashboard.html', context)

# Add custom admin view - simpler approach
from django.urls import reverse
from django.http import HttpResponseRedirect

# Create a simple redirect view instead
def admin_language_redirect(request):
    """Redirect to a simple language management page"""
    return HttpResponseRedirect('/admin/game/song/?language=tamil')

# Register as a simple admin action instead of custom URL
# This avoids URL conflicts


# Community Admin Classes
class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 2
    min_num = 2

@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'created_at', 'is_active', 'total_votes']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    inlines = [PollOptionInline]

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new poll
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(PollVote)
class PollVoteAdmin(admin.ModelAdmin):
    list_display = ['poll', 'option', 'user', 'voted_at']
    list_filter = ['poll', 'voted_at']
    search_fields = ['user__username', 'poll__title']
    readonly_fields = ['voted_at']

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'type', 'submitted_at', 'is_resolved']
    list_filter = ['type', 'is_resolved', 'submitted_at']
    search_fields = ['title', 'message', 'user__username']
    readonly_fields = ['submitted_at', 'user']

    fieldsets = (
        ('Feedback Details', {
            'fields': ('user', 'type', 'title', 'message', 'submitted_at')
        }),
        ('Admin Response', {
            'fields': ('is_resolved', 'admin_response', 'responded_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        if obj.admin_response and not obj.responded_at:
            obj.responded_at = timezone.now()
        super().save_model(request, obj, form, change)

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at']

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new announcement
            obj.created_by = request.user
        super().save_model(request, obj, form, change)