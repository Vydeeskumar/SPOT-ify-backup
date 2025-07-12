#!/usr/bin/env python
"""
Quick deployment script to apply multi-language fixes
"""
import subprocess
import sys

def run_command(command, description):
    """Run a command and print the result"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False
    return True

def main():
    """Deploy the multi-language fixes"""
    print("🚀 Deploying Multi-Language Fixes")
    print("=" * 40)
    
    commands = [
        ("python manage.py check", "Checking for errors"),
        ("python manage.py collectstatic --noinput", "Collecting static files"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"\n❌ Deployment failed at: {description}")
            return False
    
    print("\n" + "=" * 40)
    print("🎉 All fixes deployed successfully!")
    print("\n📋 What was fixed:")
    print("  ✅ Added language parameter to all views")
    print("  ✅ Fixed 500 errors in guest_login, give_up, profile, archive, friends")
    print("  ✅ Updated all views to filter by language")
    print("  ✅ Added language context to all templates")
    print("  ✅ Created simple admin language dashboard")
    print("\n🔗 Test these URLs:")
    print("  • Tamil: https://webzombies.pythonanywhere.com/tamil/")
    print("  • English: https://webzombies.pythonanywhere.com/english/")
    print("  • Hindi: https://webzombies.pythonanywhere.com/hindi/")
    print("  • Admin: https://webzombies.pythonanywhere.com/admin/language-dashboard/")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
