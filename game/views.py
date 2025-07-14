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




LAUNCH_DATE = date(2025, 6, 24)

def language_redirect(request):
    """Redirect root URL to Tamil version for backward compatibility"""
    return redirect('/tamil/')

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
