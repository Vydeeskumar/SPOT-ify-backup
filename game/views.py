from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Avg, Count
from django.http import JsonResponse
from django.contrib import messages
from .models import Song, UserScore, UserProfile
from .utils import calculate_points
from fuzzywuzzy import fuzz
import json
from django.contrib.auth.forms import UserCreationForm




def get_today_song():
    today = timezone.now().date()
    return Song.objects.filter(display_date=today).first()

def check_answer(guess, correct_answer):
    # Convert both to lowercase and strip spaces
    guess = guess.lower().strip()
    correct = correct_answer.lower().strip()
    
    # Direct match
    if guess == correct:
        return True, 100
    
    # Calculate similarity ratio
    ratio = fuzz.ratio(guess, correct)
    partial_ratio = fuzz.partial_ratio(guess, correct)
    
    print(f"Guess: {guess}, Correct: {correct}, Ratio: {ratio}, Partial Ratio: {partial_ratio}")  # For testing
    
    # If either ratio is above 85%, consider it correct
    if ratio > 85 or partial_ratio > 85:
        return True, ratio
    
    return False, ratio

@login_required
def home(request):
    today_song = get_today_song()
    user_already_played = False
    
    if not today_song:
        messages.warning(request, "No song is available for today. Please check back later!")
        return render(request, 'game/home.html', {'today_song': None})
    
    user_already_played = UserScore.objects.filter(
        user=request.user,
        song=today_song,
        attempt_date__date=timezone.now().date()
    ).exists()

    if request.method == 'POST':
        if user_already_played:
            return JsonResponse({'error': 'You have already played today'}, status=400)

        data = json.loads(request.body)
        guess = data.get('guess', '').lower().strip()
        time_taken = float(data.get('time_taken', 0))
        
        is_correct, similarity = check_answer(guess, today_song.title)

        if is_correct:
            points = calculate_points(time_taken)
            # If answer wasn't exact, reduce points slightly
            if similarity < 100:
                points = max(1, points - 1)  # Reduce by 1 but ensure minimum 1 point
                
            UserScore.objects.create(
                user=request.user,
                song=today_song,
                score=points,
                guess_time=time_taken
            )
            
            # Update user profile
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.update_stats(points, time_taken, timezone.now().date())

            return JsonResponse({
                'correct': True,
                'points': points,
                'streak': profile.current_streak,
                'message': f'Correct! You earned {points} points! 🔥 Streak: {profile.current_streak}'
            })
        else:
            return JsonResponse({
                'correct': False,
                'message': 'Wrong guess, try again!'
            })

    # Get user profile for displaying streak
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'today_song': today_song,
        'user_already_played': user_already_played,
        'current_streak': profile.current_streak,
        'longest_streak': profile.longest_streak,
    }
    return render(request, 'game/home.html', context)

@login_required
def profile(request):
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get recent activity (last 5 songs)
    recent_scores = UserScore.objects.filter(
        user=request.user
    ).select_related('song').order_by('-attempt_date')[:5]
    
    # Get monthly statistics
    today = timezone.now().date()
    month_start = today.replace(day=1)
    monthly_stats = UserScore.objects.filter(
        user=request.user,
        attempt_date__date__gte=month_start
    ).aggregate(
        monthly_points=Sum('score'),
        monthly_avg_time=Avg('guess_time'),
        monthly_songs=Count('id')
    )

    # Get all-time statistics
    all_time_stats = UserScore.objects.filter(
        user=request.user
    ).aggregate(
        total_points=Sum('score'),
        avg_score=Avg('score'),
        avg_time=Avg('guess_time'),
        total_songs=Count('id')
    )

    # Calculate success rate
    total_attempts = UserScore.objects.filter(user=request.user).count()
    if total_attempts > 0:
        success_rate = (profile.total_songs_solved / total_attempts) * 100
    else:
        success_rate = 0

    # Get streak history (last 7 days)
    streak_history = []
    for i in range(7):
        date = today - timedelta(days=i)
        played = UserScore.objects.filter(
            user=request.user,
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
    }
    return render(request, 'game/profile.html', context)

@login_required
def leaderboard(request):
    # Get weekly leaderboard
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    weekly_scores = UserScore.objects.filter(
        attempt_date__date__gte=week_start
    ).values('user__username').annotate(
        total_score=Sum('score'),
        avg_time=Avg('guess_time'),
        songs_solved=Count('id')
    ).order_by('-total_score')[:10]

    # Get monthly leaderboard
    month_start = today.replace(day=1)
    monthly_scores = UserScore.objects.filter(
        attempt_date__date__gte=month_start
    ).values('user__username').annotate(
        total_score=Sum('score'),
        avg_time=Avg('guess_time'),
        songs_solved=Count('id')
    ).order_by('-total_score')[:10]

    # Get all-time leaderboard
    all_time_scores = UserScore.objects.values('user__username').annotate(
        total_score=Sum('score'),
        avg_time=Avg('guess_time'),
        songs_solved=Count('id')
    ).order_by('-total_score')[:10]

    # Get user's rank
    user_weekly_rank = None
    user_monthly_rank = None
    user_all_time_rank = None

    if request.user.is_authenticated:
        # Calculate user's ranks
        weekly_rank = list(UserScore.objects.filter(
            attempt_date__date__gte=week_start
        ).values('user').annotate(
            total_score=Sum('score')
        ).order_by('-total_score').values_list('user', flat=True))
        
        monthly_rank = list(UserScore.objects.filter(
            attempt_date__date__gte=month_start
        ).values('user').annotate(
            total_score=Sum('score')
        ).order_by('-total_score').values_list('user', flat=True))
        
        all_time_rank = list(UserScore.objects.values('user').annotate(
            total_score=Sum('score')
        ).order_by('-total_score').values_list('user', flat=True))

        try:
            user_weekly_rank = weekly_rank.index(request.user.id) + 1
        except ValueError:
            pass

        try:
            user_monthly_rank = monthly_rank.index(request.user.id) + 1
        except ValueError:
            pass

        try:
            user_all_time_rank = all_time_rank.index(request.user.id) + 1
        except ValueError:
            pass

    context = {
        'weekly_scores': weekly_scores,
        'monthly_scores': monthly_scores,
        'all_time_scores': all_time_scores,
        'user_weekly_rank': user_weekly_rank,
        'user_monthly_rank': user_monthly_rank,
        'user_all_time_rank': user_all_time_rank,
    }
    return render(request, 'game/leaderboard.html', context)

@login_required
def give_up(request):
    if request.method == 'POST':
        today_song = get_today_song()
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
            guess_time=3600  # Maximum time
        )
        
        # Update user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.current_streak = 0  # Reset streak on give up
        profile.save()
        
        return JsonResponse({
            'message': f'The song was "{today_song.title}" from "{today_song.movie}"',
            'title': today_song.title,
            'movie': today_song.movie,
            'artist': today_song.artist
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)