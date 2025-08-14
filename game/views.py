from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Avg, Count, Max, Q
from django.http import JsonResponse
from django.contrib import messages
from .models import Song, UserScore, UserProfile, Friendship, DailySong, LANGUAGE_CHOICES
from .utils import calculate_points
from fuzzywuzzy import fuzz
import json
from django.contrib.auth.forms import UserCreationForm
import random
from django.contrib.auth import authenticate,login
from django.contrib.auth.models import User
import string
from django.http import HttpResponse
from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
from datetime import date
from django.views.decorators.http import require_GET
from datetime import datetime, timedelta
import requests
import re
from django.contrib import messages
from django.shortcuts import redirect
from allauth.socialaccount.signals import pre_social_login
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
import tempfile
import os




LAUNCH_DATE = date(2025, 6, 24)

# Signal handler to intercept Google logins
@receiver(user_logged_in)
def handle_user_login(sender, request, user, **kwargs):
    """Intercept all user logins and redirect Google logins to correct language"""
    print(f"🔥 USER LOGIN SIGNAL TRIGGERED!")
    print(f"🔥 User: {user.username}")
    print(f"🔥 Request path: {request.path}")
    print(f"🔥 Request GET: {request.GET}")
    print(f"🔥 Session keys: {list(request.session.keys())}")

    # Check if this is a Google login (social account login)
    if '/accounts/google/login/callback/' in request.path or 'google' in str(request.path):
        stored_language = request.session.get('selected_language', 'tamil')
        print(f"🔥 GOOGLE LOGIN DETECTED! Stored language: {stored_language}")

        if stored_language and stored_language != 'tamil':
            # Store a flag to redirect after login
            request.session['redirect_after_login'] = f'/{stored_language}/'
            print(f"🔥 Set redirect flag: /{stored_language}/")

    print(f"🔥 Signal handler complete")

def language_redirect(request):
    """Redirect root URL to Tamil version for backward compatibility"""
    return redirect('/tamil/')

def custom_login_redirect(request):
    """Custom login redirect that respects the ?next= parameter for language selection"""
    next_url = request.GET.get('next', '/tamil/')
    print(f"🔗 Custom login redirect: next={next_url}")
    print(f"🔗 Full request URL: {request.get_full_path()}")
    print(f"🔗 User authenticated: {request.user.is_authenticated}")

    # Validate that the next URL is one of our supported languages
    valid_redirects = ['/tamil/', '/english/', '/hindi/']
    if next_url in valid_redirects:
        print(f"✅ Valid redirect to: {next_url}")
        return redirect(next_url)
    else:
        print(f"❌ Invalid redirect, defaulting to Tamil: {next_url}")
        return redirect('/tamil/')

@csrf_exempt
def store_language(request):
    """Store selected language in session for Google OAuth redirect"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            language = data.get('language', 'tamil')
            request.session['selected_language'] = language
            print(f"🔗 Stored language in session: {language}")
            return JsonResponse({'success': True})
        except Exception as e:
            print(f"❌ Error storing language: {e}")
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

def google_login_redirect(request):
    """Handle redirect after Google login - EXACT same approach as guest login"""
    stored_language = request.session.get('selected_language', 'tamil')
    print(f"🔗 Google login redirect: stored_language={stored_language}")
    print(f"🔐 User authenticated: {request.user.is_authenticated}")
    print(f"🔗 Request path: {request.path}")
    print(f"🔗 Request GET params: {request.GET}")
    print(f"🔗 Request META: {request.META.get('HTTP_REFERER', 'No referer')}")

    # Clear the stored language
    if 'selected_language' in request.session:
        del request.session['selected_language']

    # EXACT same redirect logic as guest login
    redirect_url = f'/{stored_language}/'
    print(f"🎯 Google login successful, redirecting to {redirect_url}")
    return redirect(redirect_url)

# Direct Google callback interceptor
def google_callback_interceptor(request):
    """Intercept Google OAuth callback and redirect to correct language"""
    print(f"🔍 GOOGLE CALLBACK INTERCEPTED!")
    print(f"🔍 Request path: {request.path}")
    print(f"🔍 Request GET params: {request.GET}")
    print(f"🔍 Request META: {request.META.get('HTTP_REFERER', 'No referer')}")

    # Get stored language from session
    stored_language = request.session.get('selected_language', 'tamil')
    print(f"🔍 Stored language: {stored_language}")

    # Clear the stored language
    if 'selected_language' in request.session:
        del request.session['selected_language']

    # Redirect to the correct language
    redirect_url = f'/{stored_language}/'
    print(f"🔍 Redirecting to: {redirect_url}")

    # Continue with original flow by redirecting to allauth callback
    # with a special parameter that our adapter will recognize
    callback_url = f"{request.path}?{request.GET.urlencode()}&language_override={stored_language}"
    print(f"🔍 Continuing to: {callback_url}")
    return redirect(callback_url)

def get_language_from_request(request):
    """Extract language from URL path"""
    # Get language from URL resolver kwargs
    return getattr(request, 'resolver_match', {}).kwargs.get('language', 'tamil')

def is_google_enabled():
    if settings.ENVIRONMENT == "production":
        return SocialApp.objects.filter(provider="google").exists()
    return False


def google_site_verification(request):
    return HttpResponse(
        "google-site-verification: googled2c2d6345bb867a9.html",
        content_type="text/plain"
    )

from django.http import FileResponse
import os
from django.conf import settings

def sitemap_view(request):
    filepath = os.path.join(settings.BASE_DIR, 'sitemap.xml')
    return FileResponse(open(filepath, 'rb'), content_type='application/xml')



def get_today_song(language='tamil'):
    """Get today's song for a specific language"""
    today = timezone.now().date()
    song = Song.objects.filter(display_date=today, language=language).first()

    if song:
        # Create or update DailySong entry for today
        daily_song, created = DailySong.objects.get_or_create(
            date=today,
            language=language,
            defaults={'song': song}
        )

        # Update total players if it already exists
        if not created:
            total_players = UserScore.objects.filter(
                song=song,
                attempt_date__date=today,
                language=language
            ).count()
            daily_song.total_players = total_players
            daily_song.save()

    return song



def check_answer(guess, correct_answer, spotify_id=None, today_song=None):
    # ✅ First: check if the guessed Spotify ID matches any known ID
    if spotify_id and today_song:
        all_ids = today_song.get_all_spotify_ids() if hasattr(today_song, "get_all_spotify_ids") else []
        print(f"All Spotify IDs: {all_ids}")
        if spotify_id in all_ids:
            return True, 100  # Full score for ID match

    # ✅ Fallback: fuzzy match on text
    guess = guess.lower().strip()
    correct = correct_answer.lower().strip()
    correct_movie = today_song.movie.lower().strip() if today_song and today_song.movie else ""

    # 🔍 Debug
    print(f"Comparing - Guess from Spotify: '{guess}'")
    print(f"Correct from Database: '{correct}'")
    print(f"Movie should be: '{correct_movie}'")

    # ✅ Require movie name to be included in guess
    if correct_movie and correct_movie not in guess:
        return False, 0

    # ✅ Check fuzzy similarity
    ratio = fuzz.ratio(guess, correct)
    partial_ratio = fuzz.partial_ratio(guess, correct)
    token_sort_ratio = fuzz.token_sort_ratio(guess, correct)

    print(f"Similarity Ratios - Full: {ratio}, Partial: {partial_ratio}, Token Sort: {token_sort_ratio}")

    # ✅ If similarity is good enough, accept it
    if ratio > 80 or partial_ratio > 80 or token_sort_ratio > 80:
        return True, max(ratio, partial_ratio, token_sort_ratio)

    return False, ratio


@login_required
def home(request, language='tamil'):
    # Get language from URL or default to Tamil
    current_language = language
    today_song = get_today_song(current_language)
    user_already_played = False

    current_time = timezone.localtime(timezone.now())
    print(f"Current IST time: {current_time}")
    print(f"Current IST date: {current_time.date()}")
    print(f"Current language: {current_language}")

    if not today_song:
        messages.warning(request, f"No {current_language} song is available for today. Please check back later!")
        return render(request, 'game/home.html', {
            'today_song': None,
            'current_language': current_language
        })

    user_already_played = UserScore.objects.filter(
        user=request.user,
        song=today_song,
        attempt_date__date=timezone.now().date(),
        language=current_language
    ).exists()

    if request.method == 'POST':
        if user_already_played:
            return JsonResponse({'error': 'You have already played today'}, status=400)

        try:
            data = json.loads(request.body)
            guess = data.get('guess', '').lower().strip()
            spotify_id = data.get('spotify_id')
            time_taken = float(data.get('time_taken', 0))
            
            print("Received data:", data)
            
            is_correct, similarity = check_answer(guess, today_song.title, spotify_id, today_song)

            if is_correct:
                points = calculate_points(time_taken)

                UserScore.objects.create(
                    user=request.user,
                    song=today_song,
                    score=points,
                    guess_time=time_taken,
                    language=current_language
                )

                profile, created = UserProfile.objects.get_or_create(user=request.user)
                profile.update_stats(points, time_taken, timezone.now().date(), current_language)

                # Get language-specific streak
                language_stats = profile.get_stats_for_language(current_language)
                current_streak = language_stats['current_streak']

                return JsonResponse({
                    'correct': True,
                    'points': points,
                    'streak': current_streak,
                    'message': f'Correct! You earned {points} points! 🔥 Streak: {current_streak}'
                })
            else:
                return JsonResponse({
                    'correct': False,
                    'message': 'Wrong guess, try again!'
                })
        except Exception as e:
            print("Error:", str(e))
            return JsonResponse({'error': str(e)}, status=500)

    # Get user profile for displaying streak
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Get language-specific stats
    language_stats = profile.get_stats_for_language(current_language)

    # Calculate accurate streaks from database
    current_streak, longest_streak = calculate_streaks_from_db(request.user, current_language)

    # Initialize context with basic data
    context = {
        'today_song': today_song,
        'user_already_played': user_already_played,
        'user_score': UserScore.objects.filter(
            user=request.user,
            song=today_song,
            attempt_date__date=timezone.now().date(),
            language=current_language
        ).first() if user_already_played else None,
        'give_up': False,
        'current_streak': current_streak,
        'longest_streak': longest_streak,
        'current_language': current_language,
        'language_display': dict(LANGUAGE_CHOICES)[current_language],
    }

    # Add daily leaderboard data if user has played
    if user_already_played:
        # Get daily scores for current language
        daily_scores = UserScore.objects.filter(
            song=today_song,
            attempt_date__date=timezone.now().date(),
            language=current_language
        ).select_related('user').order_by('-score', 'guess_time')[:10]

        # Get user's score for today
        user_score = UserScore.objects.get(
            user=request.user,
            song=today_song,
            attempt_date__date=timezone.now().date(),
            language=current_language
        )

        # Get user's rank (considering both score and time)
        better_scores = UserScore.objects.filter(
            song=today_song,
            attempt_date__date=timezone.now().date(),
            language=current_language,
            score__gt=user_score.score
        ).count()

        same_score_faster = UserScore.objects.filter(
            song=today_song,
            attempt_date__date=timezone.now().date(),
            language=current_language,
            score=user_score.score,
            guess_time__lt=user_score.guess_time
        ).count()

        user_rank = better_scores + same_score_faster + 1

        # Get total players today for current language
        total_players_today = UserScore.objects.filter(
            song=today_song,
            attempt_date__date=timezone.now().date(),
            language=current_language
        ).count()

        # Add to context
        context.update({
            'daily_scores': daily_scores,
            'user_daily_rank': user_rank,
            'user_score': user_score,
            'total_players_today': total_players_today
        })

    return render(request, 'game/home.html', context)

@login_required
def profile(request, language='tamil'):
    current_language = language
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Handle opt-in toggle
    if request.method == 'POST' and 'email_notifications_opt_in' in request.POST:
        opt_in_value = request.POST.get('email_notifications_opt_in') == 'on'
        profile.email_notifications_opt_in = opt_in_value
        profile.save(update_fields=['email_notifications_opt_in'])
        messages.success(request, 'Email reminder preference updated.')

    # Get recent activity (last 5 songs) for current language
    recent_scores = UserScore.objects.filter(
        user=request.user,
        language=current_language
    ).order_by('-attempt_date')[:10]

    # Get monthly statistics for current language
    today = timezone.now().date()
    month_start = today.replace(day=1)
    monthly_stats = UserScore.objects.filter(
        user=request.user,
        language=current_language,
        attempt_date__date__gte=month_start
    ).aggregate(
        monthly_points=Sum('score'),
        monthly_avg_time=Avg('guess_time'),
        monthly_songs=Count('id')
    )

    # Get all-time statistics for current language (same as compare friends)
    all_time_stats = UserScore.objects.filter(
        user=request.user,
        language=current_language
    ).aggregate(
        total_points=Sum('score'),
        avg_score=Avg('score'),
        avg_time=Avg('guess_time', filter=Q(score__gt=0)),  # Only successful attempts
        total_songs=Count('id')
    )

    # Get language-specific stats from UserProfile model
    language_stats = profile.get_stats_for_language(current_language)

    # Override language_stats with actual database values for accuracy
    language_stats['total_points'] = all_time_stats['total_points'] or 0
    language_stats['total_songs_solved'] = all_time_stats['total_songs'] or 0
    language_stats['average_time'] = all_time_stats['avg_time'] or 0

    # Calculate accurate streaks from database
    current_streak, longest_streak = calculate_streaks_from_db(request.user, current_language)
    language_stats['current_streak'] = current_streak
    language_stats['longest_streak'] = longest_streak

    # Calculate success rate for current language
    total_attempts = UserScore.objects.filter(user=request.user, language=current_language).count()
    if total_attempts > 0:
        success_rate = (language_stats['total_songs_solved'] / total_attempts) * 100
    else:
        success_rate = 0

    # Get streak history (last 7 days) for current language
    streak_history = []
    for i in range(7):
        date = today - timedelta(days=i)
        played = UserScore.objects.filter(
            user=request.user,
            language=current_language,
            attempt_date__date=date
        ).exists()
        streak_history.append({
            'date': date,
            'played': played
        })
    streak_history.reverse()

    context = {
        'profile': profile,
        'recent_scores': recent_scores,
        'monthly_stats': monthly_stats,
        'all_time_stats': all_time_stats,
        'success_rate': round(success_rate, 1),
        'streak_history': streak_history,
        'today': today,
        'current_language': current_language,
        'language_display': dict(LANGUAGE_CHOICES)[current_language],
        'language_stats': language_stats,
        'current_streak': current_streak,
        'email_notifications_opt_in': profile.email_notifications_opt_in,
    }
    return render(request, 'game/profile.html', context)

# Add the Smart Chatbot class and remaining functions
class SmartZombieBot:
    """Smart Rule-Based + NLP Chatbot for SPOT-ify"""

    def __init__(self, username, language='tamil'):
        self.username = username
        self.language = language

        # Intent patterns
        self.intents = {
            'greeting': [
                'hi', 'hello', 'hey', 'sup', 'yo', 'hola', 'vanakkam', 'namaste'
            ],
            'game_help': [
                'how to play', 'rules', 'how does', 'explain', 'what is', 'help'
            ],
            'scoring': [
                'points', 'score', 'scoring', 'how many points', 'calculate'
            ],
            'features': [
                'features', 'what can', 'leaderboard', 'friends', 'profile', 'archive'
            ],
            'donation': [
                'donate', 'support', 'money', 'pay', 'gpay', 'upi', 'contribute'
            ],
            'creator': [
                'who made', 'creator', 'developer', 'built', 'insulin zombies'
            ],
            'goodbye': [
                'bye', 'goodbye', 'see you', 'later', 'exit', 'quit'
            ]
        }

        # Response templates
        self.responses = {
            'greeting': [
                f"Hey there {username}! 🎵 Ready to SPOT-ify some paatu today?",
                f"Vanakkam {username}! 🧟‍♂️ Let's groove with some Tamil tunes!",
                f"Yo {username}! 🎧 Time to test your music knowledge!",
                f"Hello {username}! 🎶 What musical adventure awaits us today?"
            ],
            'game_help': [
                f"Easy peasy {username}! 🎵 Listen to the audio snippet, guess the song name as fast as possible! Faster = more points (8 for ≤10s, down to 1 for >60s). Daily challenges + archive mode for practice!",
                f"Here's the deal {username}! 🎧 Play button → Listen → Type your guess → Submit! Speed matters: 10s = 8pts, 20s = 5pts, 30s = 4pts, 45s = 3pts, 60s = 2pts, slower = 1pt. Simple!",
                f"Welcome to the musical battlefield {username}! 🎯 Hear snippet → Guess song → Get points based on speed → Climb leaderboard → Become Tamil music legend! Easy right?"
            ],
            'scoring': [
                f"Points game is simple {username}! ⚡ Lightning fast (≤10s) = 8 points, Quick (≤20s) = 5 points, Good (≤30s) = 4 points, Decent (≤45s) = 3 points, Just made it (≤60s) = 2 points, Slow but steady (>60s) = 1 point!",
                f"Speed kills {username}! 🚀 The faster you guess, the more points you get. Think of it like a musical race - first place gets the gold! ⚡"
            ],
            'features': [
                f"So many cool features {username}! 🎮 Daily challenges, Archive mode (play old songs), Leaderboards (daily/weekly/all-time), Friends system (add & compare scores), Profile stats (streaks & achievements), and multi-language support!",
                f"This game is packed {username}! 📱 Daily Tamil songs, compete with friends, track your streaks, browse the archive, and climb those leaderboards! Plus Tamil, English & Hindi versions!"
            ],
            'donation': [
                f"Aww, you're too sweet {username}! 🍬✨ My creator runs this with pure passion (and lots of coffee ☕)! Even ₹5 helps buy Milk Bikis for coding sessions! 💸 UPI: rvydeeskumar@oksbi - Any amount appreciated! I'll moonwalk in your honor! 😎🧟‍♂️⚡"
            ],
            'creator': [
                f"I was created by the legendary Insulin Zombies 💀! Like Jarvis to Iron Man, but neon-soaked! 🎮 Follow the mastermind: instagram.com/insulin_zombies - He's the genius behind this musical madness!"
            ],
            'goodbye': [
                f"Bye bye {username}! 👋 Keep those Tamil tunes playing in your head! Come back for tomorrow's challenge! 🎵",
                f"See you later {username}! 🧟‍♂️ May the musical force be with you! Don't forget to play daily! ⚡",
                f"Catch you on the flip side {username}! 🎧 Keep SPOTifying those paatus! 🎶"
            ],
            'default': [
                f"Hmm {username}, that's an interesting question! 🤔 I'm still learning, but I'm great at helping with game stuff! Try asking about how to play, scoring, or features!",
                f"Good question {username}! 🧠 My zombie brain is processing... Try asking me about the game rules, points system, or cool features!",
                f"Ooh {username}, you got me thinking! 💭 I'm best at helping with SPOT-ify questions - game help, scoring, features, that sort of thing!"
            ]
        }

    def detect_intent(self, message):
        """Detect user intent from message"""
        message_lower = message.lower()

        # Check each intent
        for intent, keywords in self.intents.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return intent

        return 'default'

    def get_response(self, message):
        """Generate smart response based on message"""
        intent = self.detect_intent(message)

        # Special case for Tamil/Tanglish
        tamil_detected = bool(re.search(r'[அ-ஹஂஃ]', message))

        response = random.choice(self.responses[intent])

        # Add Tamil disclaimer if Tamil detected
        if tamil_detected:
            response += "\n\nSorry for her Bad Tamil - The Creator 🫠"

        return response

@csrf_exempt
def zombiebot(request, language='tamil'):
    current_language = language
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        user_prompt = data.get('message', '').strip()
        username = request.user.username if request.user.is_authenticated else "player"
        lower_prompt = user_prompt.lower()

        # 🧠 Short replies for fun phrases
        special_cases = {
            "vydees loosey": "Tiger Tariq loosey 😎",
            "vydees massey": "Vivek vaathiyaar loosey 😎",
            "vaithees loosey": "Tiger Tariq loosey 😎",
            "vaithees massey": "Vivek vaathiyaar loosey 😎",
            "kaithees massey": "Tiger Tariq loosey 😎",
        }
        for phrase in special_cases:
            if phrase in lower_prompt:
                return JsonResponse({"reply": special_cases[phrase]})

        # 🤖 Use Smart Zombie Bot instead of API
        smart_bot = SmartZombieBot(username, current_language)
        response_text = smart_bot.get_response(user_prompt)

        return JsonResponse({"reply": response_text})

    except Exception as e:
        # Better error handling for server errors
        error_msg = f"Oops {username}! Something went wrong in my circuits 🤖⚡ Please try again!"
        print(f"Zombiebot error: {str(e)}")  # Log for debugging
        return JsonResponse({"reply": error_msg})

# Add all missing functions
@login_required
def leaderboard(request, language='tamil'):
    # Get language from URL or default to Tamil
    current_language = language
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    def get_ranked_scores(base_queryset):
        """Helper function to get ranked scores with consistent calculation"""
        return base_queryset.values(
            'user',
            'user__username'
        ).annotate(
            total_score=Sum('score'),
            avg_time=Avg('guess_time'),
            songs_played=Count('id'),
            avg_score=Avg('score')
        ).order_by(
            '-total_score',
            'avg_time'
        )

    # Get complete ranked lists for current language
    weekly_queryset = UserScore.objects.filter(
        attempt_date__date__gte=week_start,
        language=current_language
    )
    monthly_queryset = UserScore.objects.filter(
        attempt_date__date__gte=month_start,
        language=current_language
    )
    alltime_queryset = UserScore.objects.filter(language=current_language)

    weekly_all = get_ranked_scores(weekly_queryset)
    monthly_all = get_ranked_scores(monthly_queryset)
    alltime_all = get_ranked_scores(alltime_queryset)

    # Get top 10 for each category
    weekly_scores = list(weekly_all[:10])
    monthly_scores = list(monthly_all[:10])
    all_time_scores = list(alltime_all[:10])

    # Initialize user stats
    user_stats = {
        'weekly': {'rank': None, 'total_score': 0, 'songs_played': 0, 'avg_score': 0},
        'monthly': {'rank': None, 'total_score': 0, 'songs_played': 0, 'avg_score': 0},
        'alltime': {'rank': None, 'total_score': 0, 'songs_played': 0, 'avg_score': 0}
    }

    if request.user.is_authenticated:
        # Get user's stats and rank for each period
        for index, score in enumerate(weekly_all, 1):
            if score['user'] == request.user.id:
                user_stats['weekly'] = {
                    'rank': index,
                    'total_score': score['total_score'],
                    'songs_played': score['songs_played'],
                    'avg_score': round(score['avg_score'], 2)
                }
                break

        for index, score in enumerate(monthly_all, 1):
            if score['user'] == request.user.id:
                user_stats['monthly'] = {
                    'rank': index,
                    'total_score': score['total_score'],
                    'songs_played': score['songs_played'],
                    'avg_score': round(score['avg_score'], 2)
                }
                break

        for index, score in enumerate(alltime_all, 1):
            if score['user'] == request.user.id:
                user_stats['alltime'] = {
                    'rank': index,
                    'total_score': score['total_score'],
                    'songs_played': score['songs_played'],
                    'avg_score': round(score['avg_score'], 2)
                }
                break

    # Get total players count for each period
    total_players = {
        'weekly': weekly_all.count(),
        'monthly': monthly_all.count(),
        'alltime': alltime_all.count()
    }

    # Get current streak for navbar display
    current_streak = 0
    if request.user.is_authenticated:
        current_streak, _ = calculate_streaks_from_db(request.user, current_language)

    context = {
        'weekly_scores': weekly_scores,
        'monthly_scores': monthly_scores,
        'all_time_scores': all_time_scores,
        'user_weekly_rank': user_stats['weekly']['rank'],
        'user_monthly_rank': user_stats['monthly']['rank'],
        'user_all_time_rank': user_stats['alltime']['rank'],
        'user_stats': user_stats,
        'total_players': total_players,
        'week_start': week_start,
        'month_start': month_start,
        'current_language': current_language,
        'language_display': dict(LANGUAGE_CHOICES)[current_language],
        'current_streak': current_streak,
    }

    return render(request, 'game/leaderboard.html', context)

@login_required
def give_up(request, language='tamil'):
    current_language = language
    if request.method == 'POST':
        today_song = get_today_song(current_language)
        if not today_song:
            return JsonResponse({'error': 'No song available'}, status=400)

        # Check if user already played
        if UserScore.objects.filter(
            user=request.user,
            song=today_song,
            attempt_date__date=timezone.now().date()
        ).exists():
            return JsonResponse({'error': 'Already played today'}, status=400)

        # Create score entry with 0 points
        UserScore.objects.create(
            user=request.user,
            song=today_song,
            score=0,
            guess_time=3600,  # Maximum time
            language=current_language
        )

        # Update user profile - reset language-specific streak on give up
        profile, created = UserProfile.objects.get_or_create(user=request.user)

        # Reset the correct language-specific streak
        streak_field = f'{current_language}_current_streak'
        setattr(profile, streak_field, 0)

        # Also update legacy field if Tamil (for backward compatibility)
        if current_language == 'tamil':
            profile.current_streak = 0

        profile.save()

        # Create message with or without movie info
        if today_song.movie:
            message = f'The song was "{today_song.title}" from "{today_song.movie}"'
        else:
            message = f'The song was "{today_song.title}" by {today_song.artist}'

        return JsonResponse({
            'message': message,
            'title': today_song.title,
            'movie': today_song.movie,
            'artist': today_song.artist,
            'give_up': True
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)

def guest_login(request, language='tamil'):
    if request.method == 'POST':
        username = request.POST.get('username')

        # Add a random suffix to avoid username conflicts
        base_username = username
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{random.randint(1000, 9999)}"

        # Generate a random password
        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

        # Create a temporary user
        user = User.objects.create_user(
            username=username,
            password=temp_password,
            is_active=True
        )

        # Authenticate and login the user
        authenticated_user = authenticate(
            request,
            username=username,
            password=temp_password,
            backend='django.contrib.auth.backends.ModelBackend'
        )

        if authenticated_user:
            login(request, authenticated_user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'Welcome, {username}! You are playing as a guest.')
            # Debug logging
            print(f"🎯 Guest login successful for {username}, redirecting to /{language}/")
            print(f"🔐 User authenticated: {authenticated_user.is_authenticated}")
            # Redirect to the correct language home page
            return redirect(f'/{language}/')
        else:
            print(f"❌ Authentication failed for guest user {username}")

    print(f"❌ Guest login failed, redirecting to account_login")
    return redirect('account_login')

@login_required
def friends_list(request, language='tamil'):
    current_language = language
    # Get user's friends
    friends = Friendship.objects.filter(user=request.user).select_related('friend')

    # Get friend requests if you want to implement that
    friend_requests = Friendship.objects.filter(friend=request.user)

    # Get random suggested users (not already friends and not self)
    suggested_users = User.objects.exclude(
        id__in=friends.values_list('friend_id', flat=True)
    ).exclude(
        id=request.user.id
    ).order_by('?')[:5]  # Random 5 users

    context = {
        'friends': friends,
        'friend_requests': friend_requests,
        'suggested_friends': suggested_users,
        'current_language': current_language,
        'language_display': dict(LANGUAGE_CHOICES)[current_language],
    }
    return render(request, 'game/friends.html', context)

@login_required
def add_friend(request, language='tamil'):
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            friend = User.objects.get(username=username)
            if friend != request.user:
                Friendship.objects.get_or_create(user=request.user, friend=friend)
                messages.success(request, f'Added {username} as friend!')
            else:
                messages.error(request, "You can't add yourself as a friend!")
        except User.DoesNotExist:
            messages.error(request, f'User {username} not found.')
    return redirect('friends_list', language=language)

@login_required
def remove_friend(request, friend_id, language='tamil'):
    if request.method == 'POST':
        try:
            friendship = Friendship.objects.get(user=request.user, friend_id=friend_id)
            friendship.delete()
            messages.success(request, 'Friend removed.')
        except Friendship.DoesNotExist:
            messages.error(request, 'Friend not found.')
    return redirect('friends_list', language=language)

@login_required
def compare_scores(request, friend_id, language='tamil'):
    current_language = language
    try:
        friend = User.objects.get(id=friend_id)

        # Get user's best time attempt (lowest time with score > 0) for current language
        user_best_attempt = UserScore.objects.filter(
            user=request.user,
            language=current_language,
            score__gt=0
        ).order_by('guess_time').first()

        # Get friend's best time attempt for current language
        friend_best_attempt = UserScore.objects.filter(
            user=friend,
            language=current_language,
            score__gt=0
        ).order_by('guess_time').first()

        # Get user's stats - exclude give-ups for average time, filter by language
        user_stats = UserScore.objects.filter(
            user=request.user,
            language=current_language
        ).aggregate(
            total_score=Sum('score'),
            avg_time=Avg('guess_time', filter=Q(score__gt=0)),  # Only include successful attempts
            games_played=Count('id'),
        )

        user_stats['best_time'] = user_best_attempt.guess_time if user_best_attempt else 0
        user_stats['best_time_score'] = user_best_attempt.score if user_best_attempt else 0

        # Get friend's stats - exclude give-ups for average time, filter by language
        friend_stats = UserScore.objects.filter(
            user=friend,
            language=current_language
        ).aggregate(
            total_score=Sum('score'),
            avg_time=Avg('guess_time', filter=Q(score__gt=0)),  # Only include successful attempts
            games_played=Count('id'),

        )

        friend_stats['best_time'] = friend_best_attempt.guess_time if friend_best_attempt else 0
        friend_stats['best_time_score'] = friend_best_attempt.score if friend_best_attempt else 0

        # Get recent games for current language
        user_recent = UserScore.objects.filter(
            user=request.user,
            language=current_language
        ).order_by('-attempt_date')[:5]
        friend_recent = UserScore.objects.filter(
            user=friend,
            language=current_language
        ).order_by('-attempt_date')[:5]

        context = {
            'friend': friend,
            'user_stats': user_stats,
            'friend_stats': friend_stats,
            'user_recent': user_recent,
            'friend_recent': friend_recent,
            'current_language': current_language,
            'language_display': dict(LANGUAGE_CHOICES)[current_language],
        }
        return render(request, 'game/compare_scores.html', context)
    except User.DoesNotExist:
        messages.error(request, 'Friend not found.')
        return redirect('friends_list', language=current_language)

@login_required
def get_daily_rankings(request, language='tamil'):
    # Get language from URL or default to Tamil
    current_language = language
    today_song = get_today_song(current_language)

    # Get current IST date
    ist_now = timezone.localtime(timezone.now())
    ist_date = ist_now.date()

    # Get daily scores using IST date for current language
    daily_scores = UserScore.objects.filter(
        song=today_song,
        attempt_date__date=ist_date,
        language=current_language
    ).select_related('user').order_by('-score', 'guess_time')[:10]

    try:
        # Get user's score
        user_score = UserScore.objects.get(
            user=request.user,
            song=today_song,
            attempt_date__date=ist_date,
            language=current_language
        )

        # Calculate user's rank (considering both score and time)
        better_scores = UserScore.objects.filter(
            song=today_song,
            attempt_date__date=ist_date,
            language=current_language,
            score__gt=user_score.score
        ).count()

        same_score_faster = UserScore.objects.filter(
            song=today_song,
            attempt_date__date=ist_date,
            language=current_language,
            score=user_score.score,
            guess_time__lt=user_score.guess_time
        ).count()

        user_rank = better_scores + same_score_faster + 1

    except UserScore.DoesNotExist:
        user_rank = "-"  # Handle case where user hasn't played yet

    # Format scores for JSON response
    scores_data = [{
        'username': score.user.username,
        'score': score.score,
        'guessTime': f"{score.guess_time:.1f}",
        'isCurrentUser': score.user == request.user
    } for score in daily_scores]

    return JsonResponse({
        'scores': scores_data,
        'userRank': user_rank,
        'totalPlayers': UserScore.objects.filter(
            song=today_song,
            attempt_date__date=ist_date,
            language=current_language
        ).count()
    })

def robots_txt(request):
    domain = request.get_host()
    content = f"User-agent: *\nAllow: /\nSitemap: https://{domain}/sitemap.xml"
    return HttpResponse(content, content_type="text/plain")

LAUNCH_DATE = date(2024, 5, 20)  # Adjust if different

@login_required
def archive(request, language='tamil'):
    current_language = language
    selected_date_str = request.GET.get('date')
    selected_song = None
    user_guess_result = None
    prev_date = next_date = None
    selected_date = None
    date_error = None  # NEW: for user feedback if invalid

    # Process selected date
    if selected_date_str:
        try:
            parsed_date = parse_date(selected_date_str)
            if not parsed_date:
                raise ValueError("Invalid date format")

            selected_date = parsed_date

            if selected_date == date.today():
                selected_song = None  # Don't show today's song
            elif selected_date < LAUNCH_DATE:
                selected_song = None  # SPOT-ify not born
            else:
                selected_song = Song.objects.filter(
                    display_date=selected_date,
                    language=current_language
                ).first()

                # Find prev/next for current language
                prev_song = Song.objects.filter(
                    display_date__lt=selected_date,
                    display_date__gte=LAUNCH_DATE,
                    language=current_language
                ).order_by('-display_date').first()

                next_song = Song.objects.filter(
                    display_date__gt=selected_date,
                    display_date__lt=date.today(),
                    language=current_language
                ).order_by('display_date').first()

                prev_date = prev_song.display_date if prev_song else None
                next_date = next_song.display_date if next_song else None

        except ValueError as ve:
            print("Archive date error:", ve)
            date_error = "Invalid date format. Please pick a valid date."
        except Exception as e:
            print("Archive date error:", e)
            date_error = "Something went wrong. Please try again."

    # Handle guess
    if request.method == 'POST' and selected_song:
        try:
            data = json.loads(request.body)
            guess = data.get('guess', '').strip().lower()
            spotify_id = data.get('spotify_id')
            time_taken = float(data.get('time_taken', 0))

            is_correct, similarity = check_answer(guess, selected_song.title, spotify_id, selected_song)

            if is_correct:
                points = calculate_points(time_taken)
                total_players = UserScore.objects.filter(
                    song=selected_song,
                    language=current_language
                ).count()
                better_scores = UserScore.objects.filter(
                    song=selected_song,
                    language=current_language,
                    score__gt=points
                ).count()
                rank = better_scores + 1

                user_guess_result = {
                    'correct': True,
                    'points': points,
                    'rank': rank,
                    'total_players': total_players
                }
            else:
                user_guess_result = {'correct': False, 'message': 'Wrong guess'}

        except Exception as e:
            print("Archive guess error:", str(e))
            user_guess_result = {'error': str(e)}

    # Get current streak for navbar display
    current_streak = 0
    if request.user.is_authenticated:
        current_streak, _ = calculate_streaks_from_db(request.user, current_language)

    context = {
        'selected_date': selected_date,
        'selected_song': selected_song,
        'user_guess_result': user_guess_result,
        'prev_date': prev_date,
        'next_date': next_date,
        'date_error': date_error,  # Pass to template
        'current_language': current_language,
        'language_display': dict(LANGUAGE_CHOICES)[current_language],
        'current_streak': current_streak,
    }
    return render(request, 'game/archive.html', context)

@login_required
@require_GET
def load_archive_song(request, language='tamil'):
    current_language = language
    date_str = request.GET.get('date')
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Invalid date format'}, status=400)


    if selected_date == date.today():
        return JsonResponse({'success': False, 'message': 'Cannot play today\'s song in archive'}, status=403)

    if selected_date < LAUNCH_DATE:
        return JsonResponse({'success': False, 'message': 'SPOT-ify wasn\'t born yet!'}, status=400)

    song = Song.objects.filter(
        display_date=selected_date,
        language=current_language
    ).first()
    if not song:
        return JsonResponse({'success': False, 'message': 'No song found for that date'}, status=404)

    print(f"Load archive song - Date: {selected_date}, Song: {song.title} (DB ID: {song.id}, Spotify: {song.spotify_id})")

    return JsonResponse({
        'success': True,
        'snippet_url': song.snippet.url,
        'reveal_url': song.reveal_snippet.url if song.reveal_snippet else '',
        'song_id': song.spotify_id,  # For JavaScript compatibility
        'db_song_id': song.id,  # Database ID for backend submission
        'title': song.title,
        'movie': song.movie,
        'artist': song.artist,
        'image': song.image.url if song.image else '',
        'reveal_audio_url': song.reveal_snippet.url if song.reveal_snippet else ''

    })

@login_required
@require_GET
def get_archive_navigation(request, language='tamil'):
    """Get previous and next available dates for archive navigation"""
    current_language = language
    date_str = request.GET.get('date')

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid date format'}, status=400)

    # Use same logic as archive view to find prev/next dates
    prev_song = Song.objects.filter(
        display_date__lt=selected_date,
        display_date__gte=LAUNCH_DATE,
        language=current_language
    ).order_by('-display_date').first()

    next_song = Song.objects.filter(
        display_date__gt=selected_date,
        display_date__lt=date.today(),
        language=current_language
    ).order_by('display_date').first()

    prev_date = prev_song.display_date.strftime('%Y-%m-%d') if prev_song else None
    next_date = next_song.display_date.strftime('%Y-%m-%d') if next_song else None

    return JsonResponse({
        'success': True,
        'prev_date': prev_date,
        'next_date': next_date,
        'prev_display': prev_song.display_date.strftime('%b %d') if prev_song else None,
        'next_display': next_song.display_date.strftime('%b %d') if next_song else None
    })

@csrf_exempt
@login_required
def archive_submit(request, language='tamil'):
    current_language = language
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        data = json.loads(request.body)
        user_guess = data.get('guess')
        spotify_id = data.get('spotify_id')
        song_id = data.get('song_id')
        play_date = data.get('play_date')
        time_taken = float(data.get('time_taken', 999))

        print(f"Archive submit received - song_id: {song_id}, play_date: {play_date}, guess: {user_guess}")

        song = Song.objects.get(id=song_id)
        print(f"Found song in DB: {song.title} (ID: {song.id}, Spotify: {song.spotify_id})")
        is_correct, _ = check_answer(user_guess, song.title, spotify_id, song)

        if is_correct:
            points = calculate_points(time_taken)

            # Calculate rank considering both score and time
            better_scores = UserScore.objects.filter(song=song, score__gt=points).count()
            same_score_faster = UserScore.objects.filter(
                song=song,
                score=points,
                guess_time__lt=time_taken
            ).count()
            rank = better_scores + same_score_faster + 1

            return JsonResponse({
                'correct': True,
                'song_title': song.title,
                'movie': song.movie,
                'artist': song.artist,
                'image':song.image.url if song.image else '',
                'rank': rank,
                'points': points,
                'time_taken': time_taken
            })
        else:
            return JsonResponse({
                'correct': False,
                'message': 'Wrong guess! Try again.'
            })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_GET
def giveup_archive(request, language='tamil'):
    current_language = language
    song_id = request.GET.get('song_id')
    try:
        song = Song.objects.get(id=song_id)
    except Song.DoesNotExist:
        return JsonResponse({'error': 'Song not found'}, status=404)

    points = 0  # give up → 0 points
    time_taken = 30.0  # Default time for give up

    # Rank = count of users who scored > 0 + count of users who gave up faster + 1
    better_scores = UserScore.objects.filter(song=song, score__gt=points).count()
    same_score_faster = UserScore.objects.filter(
        song=song,
        score=points,
        guess_time__lt=time_taken
    ).count()
    rank = better_scores + same_score_faster + 1
    total_players = UserScore.objects.filter(song=song).count()

    return JsonResponse({
        'song_title': song.title,
        'movie': song.movie,
        'artist': song.artist,
        'image': song.image.url if song.image else '',
        'points': points,
        'rank': rank,
        'time_taken': 0,
        'total_players': total_players
    })

@login_required
def get_archive_leaderboard(request, language='tamil'):
    """Get actual leaderboard for a specific archive date"""
    current_language = language
    date_str = request.GET.get('date')
    user_rank = int(request.GET.get('user_rank', 0))
    user_points = int(request.GET.get('user_points', 0))
    user_time = float(request.GET.get('user_time', 0))

    try:
        # Get the song by date and language (more reliable than song_id)
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        song = Song.objects.get(
            display_date=selected_date,
            language=current_language
        )

        # Get actual players from that date
        actual_players = UserScore.objects.filter(
            song=song,
            attempt_date__date=selected_date,
            language=current_language
        ).order_by('-score', 'guess_time')[:5]

        # Build leaderboard with hypothetical user inserted
        leaderboard = []
        user_inserted = False

        for i, player_score in enumerate(actual_players):
            current_rank = i + 1

            # Insert user's hypothetical score at correct position
            if not user_inserted and user_rank <= current_rank:
                leaderboard.append({
                    'rank': user_rank,
                    'username': '[YOU]',
                    'score': user_points,
                    'time': user_time,
                    'is_hypothetical': True
                })
                user_inserted = True

                # Adjust current player's rank if needed
                if user_rank == current_rank:
                    current_rank += 1

            leaderboard.append({
                'rank': current_rank,
                'username': player_score.user.username,
                'score': player_score.score,
                'time': player_score.guess_time,
                'is_hypothetical': False
            })

        # If user rank is beyond top 5, add them at the end
        if not user_inserted:
            leaderboard.append({
                'rank': user_rank,
                'username': '[YOU]',
                'score': user_points,
                'time': user_time,
                'is_hypothetical': True
            })

        return JsonResponse({
            'success': True,
            'leaderboard': leaderboard[:5],  # Limit to 5 entries
            'date': date_str
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def calculate_points(seconds):
    if seconds <= 10: return 8
    elif seconds <= 20: return 5
    elif seconds <= 30: return 4
    elif seconds <= 45: return 3
    elif seconds <= 60: return 2
    else: return 1

def calculate_streaks_from_db(user, language):
    """Calculate current and longest streaks directly from database"""
    from datetime import timedelta

    # Get all user scores for this language, ordered by date
    scores = UserScore.objects.filter(
        user=user,
        language=language
    ).order_by('attempt_date__date').values_list('attempt_date__date', 'score')

    if not scores:
        return 0, 0

    # Convert to list of (date, score) tuples
    score_list = list(scores)

    # Group by date (in case multiple attempts per day, take the latest)
    daily_scores = {}
    for date, score in score_list:
        daily_scores[date] = score  # This will keep the last score for each date

    # Sort dates
    sorted_dates = sorted(daily_scores.keys())

    current_streak = 0
    longest_streak = 0
    temp_streak = 0

    # Calculate streaks
    for i, date in enumerate(sorted_dates):
        score = daily_scores[date]

        if score > 0:  # Successful attempt
            if i == 0:  # First date
                temp_streak = 1
            else:
                prev_date = sorted_dates[i-1]
                if date == prev_date + timedelta(days=1):  # Consecutive day
                    temp_streak += 1
                else:  # Gap in dates
                    temp_streak = 1
        else:  # Give up (score = 0)
            temp_streak = 0

        # Update longest streak
        longest_streak = max(longest_streak, temp_streak)

    # Current streak is the streak ending on the most recent date
    today = timezone.now().date()
    if sorted_dates:
        last_date = sorted_dates[-1]
        last_score = daily_scores[last_date]

        if last_score > 0:  # Last game was successful
            # Check if it's recent enough to count as current streak
            if last_date >= today - timedelta(days=1):  # Today or yesterday
                current_streak = temp_streak
            else:
                current_streak = 0  # Too old
        else:
            current_streak = 0  # Last game was a give-up

    return current_streak, longest_streak

@login_required
def public_profile(request, username, language='tamil'):
    current_language = language
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(UserProfile, user=user)
    recent_scores = UserScore.objects.filter(
        user=user,
        language=current_language
    ).order_by('-attempt_date')[:10]

    # Get language-specific stats for public profile
    language_stats = profile.get_stats_for_language(current_language)

    # Get accurate stats from database (same as compare friends)
    db_stats = UserScore.objects.filter(
        user=user,
        language=current_language
    ).aggregate(
        total_points=Sum('score'),
        avg_time=Avg('guess_time', filter=Q(score__gt=0)),
        total_songs=Count('id')
    )

    # Override with accurate database values
    language_stats['total_points'] = db_stats['total_points'] or 0
    language_stats['total_songs_solved'] = db_stats['total_songs'] or 0
    language_stats['average_time'] = db_stats['avg_time'] or 0

    # Calculate accurate streaks from database
    current_streak, longest_streak = calculate_streaks_from_db(user, current_language)
    language_stats['current_streak'] = current_streak
    language_stats['longest_streak'] = longest_streak

    is_friend = Friendship.objects.filter(user=request.user, friend=user).exists()
    request_sent = Friendship.objects.filter(user=request.user, friend=user).exists()

    return render(request, 'game/profile.html', {
        'user': user,
        'profile': profile,
        'recent_scores': recent_scores,
        'public': True,
        'is_friend': is_friend,
        'request_sent': request_sent,
        'profile_user': user,  # alias for template
        'current_language': current_language,
        'language_display': dict(LANGUAGE_CHOICES)[current_language],
        'language_stats': language_stats,
        'current_streak': current_streak,
    })

@login_required
def send_friend_request(request, username, language='tamil'):
    to_user = get_object_or_404(User, username=username)

    if to_user == request.user:
        messages.error(request, "You can't add yourself!")
        return redirect('public_profile', username=username, language=language)

    if Friendship.objects.filter(user=request.user, friend=to_user).exists():
        messages.info(request, "You're already friends!")
    else:
        Friendship.objects.create(user=request.user, friend=to_user)
        messages.success(request, "Friend request sent!")

    return redirect('public_profile', username=username, language=language)


# 🎤 Voice Recognition Processing Endpoint
@login_required
def process_voice_audio(request):
    """
    Process audio file with Whisper for better accuracy
    Fallback when Web Speech API confidence is low
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        # Get audio file from request
        audio_file = request.FILES.get('audio')
        language = request.POST.get('language', 'tamil')

        if not audio_file:
            return JsonResponse({'error': 'No audio file provided'}, status=400)

        # CORRECTED: Language mapping for Whisper
        # Both Tamil AND Hindi songs are in English letters (Romanized)!
        whisper_lang_map = {
            'tamil': 'en',    # Tamil songs written in English letters!
            'english': 'en',  # English songs
            'hindi': 'en'     # Hindi songs ALSO written in English letters!
        }

        whisper_lang = whisper_lang_map.get(language, 'en')

        # Save temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            for chunk in audio_file.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name

        try:
            # TODO: Implement Whisper processing
            # For now, return a placeholder response
            # In production, you would:
            # 1. Install whisper: pip install openai-whisper
            # 2. Load model: model = whisper.load_model("base")
            # 3. Transcribe: result = model.transcribe(temp_path, language=whisper_lang)

            # Placeholder response
            transcript = "Whisper processing not implemented yet"
            confidence = 0.8

            return JsonResponse({
                'success': True,
                'transcript': transcript,
                'confidence': confidence,
                'language': language,
                'method': 'whisper'
            })

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        return JsonResponse({
            'error': f'Voice processing failed: {str(e)}',
            'success': False
        }, status=500)


# 🏆 Celebration Modals Endpoint
@login_required
def check_celebrations(request, language):
    """
    Check if user should see celebration modals:
    1. Weekly/Monthly winners (for all users on new week/month)
    2. Daily top 10 achievement (for individual users who ranked top 10 yesterday)
    """
    try:
        # Get current time in UTC
        now = timezone.now()
        today = now.date()

        response_data = {
            'success': True,
            'weekly_winners': None,
            'monthly_winners': None,
            'daily_achievement': None
        }

        # Check if it's the start of a new week (Monday)
        if today.weekday() == 0:  # Monday = 0
            weekly_winners = get_weekly_winners(language)
            if weekly_winners:
                response_data['weekly_winners'] = weekly_winners

        # Check if it's the start of a new month (1st day)
        if today.day == 1:
            monthly_winners = get_monthly_winners(language)
            if monthly_winners:
                response_data['monthly_winners'] = monthly_winners

        # Check if user was in top 10 yesterday
        yesterday = today - timedelta(days=1)
        daily_rank = get_user_daily_rank(request.user, yesterday, language)
        if daily_rank and daily_rank <= 10:
            response_data['daily_achievement'] = {
                'rank': daily_rank,
                'date': yesterday.isoformat()
            }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({
            'error': f'Failed to check celebrations: {str(e)}',
            'success': False
        }, status=500)


def get_weekly_winners(language):
    """Get top 3 weekly winners"""
    try:
        now = timezone.now()
        today = now.date()

        # Calculate last week's date range
        last_monday = today - timedelta(days=today.weekday() + 7)
        last_sunday = last_monday + timedelta(days=6)

        # Get weekly leaderboard for last week
        weekly_leaders = UserScore.objects.filter(
            song__language=language,
            attempt_date__date__gte=last_monday,
            attempt_date__date__lte=last_sunday
        ).values('user__username').annotate(
            total_score=Sum('score'),
            avg_time=Avg('guess_time'),
            games_played=Count('id')
        ).order_by('-total_score', 'avg_time')[:3]

        return list(weekly_leaders) if weekly_leaders else None

    except Exception as e:
        print(f"Error getting weekly winners: {e}")
        return None


def get_monthly_winners(language):
    """Get top 3 monthly winners"""
    try:
        now = timezone.now()
        today = now.date()

        # Calculate last month's date range
        if today.month == 1:
            last_month = 12
            last_year = today.year - 1
        else:
            last_month = today.month - 1
            last_year = today.year

        last_month_start = today.replace(year=last_year, month=last_month, day=1)

        # Calculate last day of last month
        if last_month == 12:
            next_month_start = today.replace(year=last_year + 1, month=1, day=1)
        else:
            next_month_start = today.replace(year=last_year, month=last_month + 1, day=1)

        last_month_end = next_month_start - timedelta(days=1)

        # Get monthly leaderboard for last month
        monthly_leaders = UserScore.objects.filter(
            song__language=language,
            attempt_date__date__gte=last_month_start,
            attempt_date__date__lte=last_month_end
        ).values('user__username').annotate(
            total_score=Sum('score'),
            avg_time=Avg('guess_time'),
            games_played=Count('id')
        ).order_by('-total_score', 'avg_time')[:3]

        return list(monthly_leaders) if monthly_leaders else None

    except Exception as e:
        print(f"Error getting monthly winners: {e}")
        return None


def get_user_daily_rank(user, date, language):
    """Get user's rank for a specific date"""
    try:
        # Get daily leaderboard for the specified date
        daily_leaders = UserScore.objects.filter(
            song__language=language,
            attempt_date__date=date
        ).values('user').annotate(
            total_score=Sum('score'),
            avg_time=Avg('guess_time')
        ).order_by('-total_score', 'avg_time')

        # Find user's rank
        for index, leader in enumerate(daily_leaders):
            if leader['user'] == user.id:
                return index + 1  # Rank is 1-based

        return None  # User not found in rankings

    except Exception as e:
        print(f"Error getting user daily rank: {e}")
        return None


# Community Views
@login_required
def community(request):
    from .models import Poll, Announcement, Feedback

    # Get active polls
    active_polls = Poll.objects.filter(is_active=True).order_by('-created_at')[:5]

    # Get recent announcements
    announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:3]

    # Get user's recent feedback
    user_feedback = Feedback.objects.filter(user=request.user).order_by('-submitted_at')[:5]

    context = {
        'active_polls': active_polls,
        'announcements': announcements,
        'user_feedback': user_feedback,
    }

    return render(request, 'game/community.html', context)

@login_required
def submit_feedback(request):
    if request.method == 'POST':
        from .models import Feedback

        feedback_type = request.POST.get('type', 'feedback')
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()

        if title and message:
            Feedback.objects.create(
                user=request.user,
                type=feedback_type,
                title=title,
                message=message
            )
            messages.success(request, 'Your feedback has been submitted successfully!')
        else:
            messages.error(request, 'Please fill in all fields.')

    return redirect('community')

@login_required
def vote_poll(request):
    if request.method == 'POST':
        from .models import Poll, PollOption, PollVote

        poll_id = request.POST.get('poll_id')
        option_id = request.POST.get('option_id')

        try:
            poll = Poll.objects.get(id=poll_id, is_active=True)
            option = PollOption.objects.get(id=option_id, poll=poll)

            # Check if user already voted
            existing_vote = PollVote.objects.filter(poll=poll, user=request.user).first()

            if existing_vote:
                # Update existing vote
                existing_vote.option = option
                existing_vote.save()
                messages.success(request, 'Your vote has been updated!')
            else:
                # Create new vote
                PollVote.objects.create(
                    poll=poll,
                    option=option,
                    user=request.user
                )
                messages.success(request, 'Thank you for voting!')

        except (Poll.DoesNotExist, PollOption.DoesNotExist):
            messages.error(request, 'Invalid poll or option.')

    return redirect('community')

@login_required
def submit_question(request):
    if request.method == 'POST':
        from .models import Feedback

        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()

        if title and message:
            Feedback.objects.create(
                user=request.user,
                type='question',
                title=title,
                message=message
            )
            messages.success(request, 'Your question has been submitted!')
        else:
            messages.error(request, 'Please fill in all fields.')

    return redirect('community')

@login_required
def update_username(request):
    if request.method != 'POST':
        return redirect('profile')
 
    new_username = request.POST.get('new_username', '').strip()
    if not new_username:
        messages.error(request, 'Username cannot be empty.')
        return redirect('profile')
 
    # Basic validation
    if len(new_username) < 3 or len(new_username) > 30:
        messages.error(request, 'Username must be between 3 and 30 characters.')
        return redirect('profile')
 
    if not new_username.isalnum():
        messages.error(request, 'Username must be alphanumeric (letters and numbers only).')
        return redirect('profile')
 
    # Check uniqueness
    if User.objects.filter(username__iexact=new_username).exclude(id=request.user.id).exists():
        messages.error(request, 'That username is already taken.')
        return redirect('profile')
 
    # Update username
    old_username = request.user.username
    request.user.username = new_username
    request.user.save(update_fields=['username'])
    messages.success(request, f'Username updated from {old_username} to {new_username}.')
    return redirect('profile')
