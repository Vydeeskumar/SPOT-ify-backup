from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Avg, Count, Max
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




LAUNCH_DATE = date(2025, 6, 24)

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

    # Clear the stored language
    if 'selected_language' in request.session:
        del request.session['selected_language']

    # EXACT same redirect logic as guest login
    redirect_url = f'/{stored_language}/'
    print(f"🎯 Google login successful, redirecting to {redirect_url}")
    return redirect(redirect_url)

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
        'current_streak': language_stats['current_streak'],
        'longest_streak': language_stats['longest_streak'],
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

    # Get recent activity (last 5 songs) for current language
    recent_scores = UserScore.objects.filter(
        user=request.user,
        language=current_language
    ).select_related('song').order_by('-attempt_date')[:5]

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

    # Get all-time statistics for current language
    all_time_stats = UserScore.objects.filter(
        user=request.user,
        language=current_language
    ).aggregate(
        total_points=Sum('score'),
        avg_score=Avg('score'),
        avg_time=Avg('guess_time'),
        total_songs=Count('id')
    )

    # Get language-specific stats
    language_stats = profile.get_stats_for_language(current_language)

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

        return JsonResponse({
            'message': f'The song was "{today_song.title}" from "{today_song.movie}"',
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

    context = {
        'selected_date': selected_date,
        'selected_song': selected_song,
        'user_guess_result': user_guess_result,
        'prev_date': prev_date,
        'next_date': next_date,
        'date_error': date_error,  # Pass to template
        'current_language': current_language,
        'language_display': dict(LANGUAGE_CHOICES)[current_language],
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


    return JsonResponse({
        'success': True,
        'snippet_url': song.snippet.url,
        'reveal_url': song.reveal_snippet.url if song.reveal_snippet else '',
        'song_id': song.spotify_id,
        'title': song.title,
        'movie': song.movie,
        'artist': song.artist,
        'image': song.image.url if song.image else '',
        'reveal_audio_url': song.reveal_snippet.url if song.reveal_snippet else ''

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

        song = Song.objects.get(id=song_id)
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

def calculate_points(seconds):
    if seconds <= 10: return 8
    elif seconds <= 20: return 5
    elif seconds <= 30: return 4
    elif seconds <= 45: return 3
    elif seconds <= 60: return 2
    else: return 1

@login_required
def public_profile(request, username, language='tamil'):
    current_language = language
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(UserProfile, user=user)
    recent_scores = UserScore.objects.filter(
        user=user,
        language=current_language
    ).order_by('-attempt_date')[:10]

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
