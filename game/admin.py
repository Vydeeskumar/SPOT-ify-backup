from django.contrib import admin
from .models import Song, UserScore

admin.site.register(Song)
admin.site.register(UserScore)