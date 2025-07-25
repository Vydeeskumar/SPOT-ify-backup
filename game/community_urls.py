from django.urls import path
from . import views

urlpatterns = [
    path('', views.community, name='community'),
    path('submit-feedback/', views.submit_feedback, name='submit_feedback'),
    path('vote-poll/', views.vote_poll, name='vote_poll'),
    path('submit-question/', views.submit_question, name='submit_question'),
]
