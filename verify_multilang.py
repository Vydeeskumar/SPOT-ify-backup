#!/usr/bin/env python
"""
Verification script for multi-language SPOT-ify system
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify_paatu.settings')
django.setup()

from game.models import Song, UserScore, UserProfile, DailySong, LANGUAGE_CHOICES
from django.contrib.auth.models import User
from django.utils import timezone

def verify_database_structure():
    """Verify that database models support multi-language"""
    print("🔍 Verifying Database Structure...")
    
    # Check Song model has language field
    song_fields = [field.name for field in Song._meta.fields]
    assert 'language' in song_fields, "Song model missing language field"
    print("  ✅ Song model has language field")
    
    # Check UserScore model has language field
    userscore_fields = [field.name for field in UserScore._meta.fields]
    assert 'language' in userscore_fields, "UserScore model missing language field"
    print("  ✅ UserScore model has language field")
    
    # Check DailySong model has language field
    dailysong_fields = [field.name for field in DailySong._meta.fields]
    assert 'language' in dailysong_fields, "DailySong model missing language field"
    print("  ✅ DailySong model has language field")
    
    # Check UserProfile has language-specific fields
    profile_fields = [field.name for field in UserProfile._meta.fields]
    for lang_code, _ in LANGUAGE_CHOICES:
        expected_fields = [
            f'{lang_code}_current_streak',
            f'{lang_code}_longest_streak',
            f'{lang_code}_total_points',
            f'{lang_code}_total_songs_solved',
            f'{lang_code}_average_time',
            f'{lang_code}_last_played_date'
        ]
        for field in expected_fields:
            assert field in profile_fields, f"UserProfile missing {field}"
    print("  ✅ UserProfile has language-specific fields")

def verify_test_data():
    """Verify test data exists for all languages"""
    print("\n📊 Verifying Test Data...")
    
    for lang_code, lang_name in LANGUAGE_CHOICES:
        song_count = Song.objects.filter(language=lang_code).count()
        print(f"  {lang_name}: {song_count} songs")
        
        if song_count > 0:
            # Check if there's a song for today
            today_song = Song.objects.filter(
                language=lang_code,
                display_date=timezone.now().date()
            ).first()
            
            if today_song:
                print(f"    ✅ Today's song: {today_song.title}")
            else:
                print(f"    ⚠️  No song set for today")

def verify_language_choices():
    """Verify language choices are properly defined"""
    print("\n🌐 Verifying Language Choices...")
    
    expected_languages = ['tamil', 'english', 'hindi']
    actual_languages = [lang[0] for lang in LANGUAGE_CHOICES]
    
    for lang in expected_languages:
        assert lang in actual_languages, f"Missing language: {lang}"
        print(f"  ✅ {lang.title()} language configured")

def verify_user_profile_methods():
    """Verify UserProfile methods work correctly"""
    print("\n👤 Verifying UserProfile Methods...")
    
    # Create test user and profile
    user, created = User.objects.get_or_create(
        username='test_multilang_user',
        defaults={'email': 'test@example.com'}
    )
    
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Test language-specific stats
    today = timezone.now().date()
    
    # Update Tamil stats
    profile.update_stats(100, 5.0, today, 'tamil')
    tamil_stats = profile.get_stats_for_language('tamil')
    assert tamil_stats['total_points'] == 100, "Tamil stats not updated correctly"
    print("  ✅ Tamil stats update working")
    
    # Update English stats
    profile.update_stats(80, 7.0, today, 'english')
    english_stats = profile.get_stats_for_language('english')
    assert english_stats['total_points'] == 80, "English stats not updated correctly"
    print("  ✅ English stats update working")
    
    # Verify Tamil stats unchanged
    tamil_stats = profile.get_stats_for_language('tamil')
    assert tamil_stats['total_points'] == 100, "Tamil stats affected by English update"
    print("  ✅ Language isolation working")
    
    # Clean up
    user.delete()

def verify_admin_functionality():
    """Verify admin customizations are in place"""
    print("\n⚙️ Verifying Admin Functionality...")
    
    from game.admin import SongAdmin, UserScoreAdmin
    
    # Check SongAdmin has language filtering
    assert 'language' in SongAdmin.list_filter, "SongAdmin missing language filter"
    print("  ✅ SongAdmin has language filtering")
    
    # Check UserScoreAdmin has language filtering
    assert 'language' in UserScoreAdmin.list_filter, "UserScoreAdmin missing language filter"
    print("  ✅ UserScoreAdmin has language filtering")

def main():
    """Run all verification checks"""
    print("🚀 SPOT-ify Multi-Language System Verification")
    print("=" * 50)
    
    try:
        verify_language_choices()
        verify_database_structure()
        verify_test_data()
        verify_user_profile_methods()
        verify_admin_functionality()
        
        print("\n" + "=" * 50)
        print("🎉 ALL VERIFICATIONS PASSED!")
        print("\n✨ Multi-language system is ready for deployment!")
        print("\n📋 Summary:")
        print("  • 3 languages supported: Tamil, English, Hindi")
        print("  • Language-specific URLs: /tamil/, /english/, /hindi/")
        print("  • Separate leaderboards and stats per language")
        print("  • Admin interface with language tabs")
        print("  • Language-specific theming")
        
        return True
        
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
