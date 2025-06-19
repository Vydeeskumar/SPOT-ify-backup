from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Avg, Count, Max
from django.http import JsonResponse
from django.contrib import messages
from .models import Song, UserScore, UserProfile, Friendship
from .utils import calculate_points
from fuzzywuzzy import fuzz
import json
from django.contrib.auth.forms import UserCreationForm
import random
from django.contrib.auth import authenticate,login
from django.contrib.auth.models import User
import string







def get_today_song():
    today = timezone.now().date()
    return Song.objects.filter(display_date=today).first()

def check_answer(guess, correct_answer, spotify_id=None, today_song=None):
    # First check Spotify ID match if available
    if spotify_id and today_song and hasattr(today_song, 'spotify_id'):
        if spotify_id == today_song.spotify_id:
            return True, 100
    
    # Fallback to your existing fuzzy matching
    guess = guess.lower().strip()
    correct = correct_answer.lower().strip()
    correct_movie = today_song.movie.lower().strip()
    
    # Print for debugging
    print(f"Comparing - Guess from Spotify: '{guess}'")
    print(f"Correct from Database: '{correct}'")
    print(f"Movie should be: '{correct_movie}'")
    
    # Check if the guess includes the correct movie name
    if correct_movie not in guess:
        return False, 0
    
    # Calculate similarity ratio only if movie matches
    ratio = fuzz.ratio(guess, correct)
    partial_ratio = fuzz.partial_ratio(guess, correct)
    token_sort_ratio = fuzz.token_sort_ratio(guess, correct)
    
    print(f"Similarity Ratios - Full: {ratio}, Partial: {partial_ratio}, Token Sort: {token_sort_ratio}")
    if today_song:
        print(f"Spotify IDs - Guess: {spotify_id}, Correct: {getattr(today_song, 'spotify_id', None)}")
    
    # If any ratio is above 80% AND movie matches, consider it correct
    if ratio > 80 or partial_ratio > 80 or token_sort_ratio > 80:
        return True, max(ratio, partial_ratio, token_sort_ratio)
    
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

        try:  # Add try-except block
            data = json.loads(request.body)
            guess = data.get('guess', '').lower().strip()
            spotify_id = data.get('spotify_id')  # Get Spotify ID from request
            time_taken = float(data.get('time_taken', 0))
            
            print("Received data:", data)  # Debug print
            
            is_correct, similarity = check_answer(guess, today_song.title, spotify_id, today_song)

            if is_correct:
                points = calculate_points(time_taken)
                    
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
        except Exception as e:
            print("Error:", str(e))  # Debug print
            return JsonResponse({'error': str(e)}, status=500)

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

def guest_login(request):
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
            return redirect('home')
        
    return redirect('account_login')

@login_required
def friends_list(request):
    # Get user's friends
    friends = Friendship.objects.filter(user=request.user).select_related('friend')
    
    # Get friend requests if you want to implement that
    friend_requests = Friendship.objects.filter(friend=request.user)
    
    # Get friend suggestions (users with similar scores)
    user_score = UserScore.objects.filter(user=request.user).aggregate(total=Sum('score'))['total'] or 0
    
    similar_users = User.objects.annotate(
        total_score=Sum('userscore__score')
    ).filter(
        total_score__range=(user_score * 0.8, user_score * 1.2)
    ).exclude(
        id__in=friends.values_list('friend_id', flat=True)
    ).exclude(id=request.user.id)[:5]

    context = {
        'friends': friends,
        'friend_requests': friend_requests,
        'suggested_friends': similar_users,
    }
    return render(request, 'game/friends.html', context)

@login_required
def add_friend(request):
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
    return redirect('friends_list')

@login_required
def remove_friend(request, friend_id):
    if request.method == 'POST':
        try:
            friendship = Friendship.objects.get(user=request.user, friend_id=friend_id)
            friendship.delete()
            messages.success(request, 'Friend removed.')
        except Friendship.DoesNotExist:
            messages.error(request, 'Friend not found.')
    return redirect('friends_list')

@login_required
def compare_scores(request, friend_id):
    try:
        friend = User.objects.get(id=friend_id)
        
        # Get user's stats
        user_stats = UserScore.objects.filter(user=request.user).aggregate(
            total_score=Sum('score'),
            avg_score=Avg('score'),
            games_played=Count('id'),
            best_score=Max('score')
        )
        
        # Get friend's stats
        friend_stats = UserScore.objects.filter(user=friend).aggregate(
            total_score=Sum('score'),
            avg_score=Avg('score'),
            games_played=Count('id'),
            best_score=Max('score')
        )
        
        # Get recent games
        user_recent = UserScore.objects.filter(user=request.user).order_by('-attempt_date')[:5]
        friend_recent = UserScore.objects.filter(user=friend).order_by('-attempt_date')[:5]
        
        context = {
            'friend': friend,
            'user_stats': user_stats,
            'friend_stats': friend_stats,
            'user_recent': user_recent,
            'friend_recent': friend_recent,
        }
        return render(request, 'game/compare_scores.html', context)
    except User.DoesNotExist:
        messages.error(request, 'Friend not found.')
        return redirect('friends_list')