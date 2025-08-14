from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('give-up/', views.give_up, name='give_up'), 
    path('compare-scores/', views.compare_scores, name='compare_scores'),
    path('friends/', views.friends, name='friends'),
    path('add-friend/<str:username>/', views.send_friend_request, name='send_friend_request'),
    path('profile/<str:username>/', views.public_profile, name='public_profile'),
    path('giveup-archive/', views.giveup_archive, name='giveup_archive'),
    path('archive-leaderboard/', views.get_archive_leaderboard, name='archive_leaderboard'),
    path('zombiebot/', views.zombiebot, name='zombiebot'),
    path('voice-process/', views.process_voice_input, name='process_voice_input'),
    path('update-username/', views.update_username, name='update_username'),
]