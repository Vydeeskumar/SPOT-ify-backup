#!/usr/bin/env python
"""
Deploy bug fixes for multi-language system
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
    """Deploy the bug fixes"""
    print("🚀 Deploying Bug Fixes for Multi-Language System")
    print("=" * 50)
    
    commands = [
        ("python manage.py check", "Checking for errors"),
        ("python manage.py collectstatic --noinput", "Collecting static files"),
        ("git add .", "Adding files to git"),
        ("git commit -m 'Fix multi-language bugs: give up, archive, compare scores, admin URLs'", "Committing changes"),
        ("git push origin main", "Pushing to repository"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"\n❌ Deployment failed at: {description}")
            return False
    
    print("\n" + "=" * 50)
    print("🎉 All bug fixes deployed successfully!")
    print("\n📋 Bugs Fixed:")
    print("  ✅ Give up button - Now uses correct language URLs")
    print("  ✅ Archive submit/give up - Fixed URL routing")
    print("  ✅ Compare scores - Added language filtering")
    print("  ✅ Admin language dashboard - Simplified approach")
    print("  ✅ All JavaScript - Updated to use current language")
    print("\n🚀 Next Steps for PythonAnywhere:")
    print("  1. cd ~/spotify-paatu")
    print("  2. git pull origin main")
    print("  3. python manage.py collectstatic --noinput")
    print("  4. Reload web app")
    print("\n🔗 Test these after deployment:")
    print("  • Give up button functionality")
    print("  • Archive page submit/give up")
    print("  • Compare scores with friends")
    print("  • Language switching")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
