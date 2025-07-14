#!/usr/bin/env python
"""
Deploy critical URL fixes
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
    """Deploy the critical fixes"""
    print("🚀 Deploying Critical URL Fixes")
    print("=" * 40)
    
    commands = [
        ("git add .", "Adding files to git"),
        ("git commit -m \"Fix profile URLs and login redirect to use Tamil by default\"", "Committing changes"),
        ("git push origin main", "Pushing to repository"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"\n❌ Deployment failed at: {description}")
            return False
    
    print("\n" + "=" * 40)
    print("🎉 Critical fixes deployed successfully!")
    print("\n📋 Fixes Applied:")
    print("  ✅ Profile links now use current language (Tamil/English/Hindi)")
    print("  ✅ Login redirect now goes to Tamil by default")
    print("  ✅ Daily leaderboard profile links fixed")
    print("  ✅ Leaderboard page profile links fixed")
    print("  ✅ Public profile view updated for language filtering")
    print("\n🚀 PythonAnywhere Steps:")
    print("  1. git pull origin main")
    print("  2. python manage.py collectstatic --noinput")
    print("  3. Reload web app")
    print("\n🔗 Test After Deployment:")
    print("  • Login should go to /tamil/ by default")
    print("  • Profile links should stay in current language")
    print("  • Daily leaderboard profile links should work")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
