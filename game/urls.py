from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('give-up/', views.give_up, name='give_up'), 
    path('guest-login/', views.guest_login, name='guest_login'),
    path('friends/', views.friends_list, name='friends_list'),
    path('friends/add/', views.add_friend, name='add_friend'),
    path('friends/remove/<int:friend_id>/', views.remove_friend, name='remove_friend'),
    path('friends/compare/<int:friend_id>/', views.compare_scores, name='compare_scores'),
    path('get-daily-rankings/', views.get_daily_rankings, name='get_daily_rankings'),
    path('archive/', views.archive, name='archive'),
    path('archive/submit/', views.archive_submit, name='archive_submit'),
    path('load-archive-song/', views.load_archive_song, name='load_archive_song'),
    path('giveup-archive/', views.giveup_archive, name='giveup_archive'),
    path('profile/<str:username>/', views.public_profile, name='public_profile'),

]