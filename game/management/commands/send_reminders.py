from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q
from datetime import datetime
import pytz

from game.models import UserScore, UserProfile, LANGUAGE_CHOICES


class Command(BaseCommand):
    help = "Send daily reminder emails to users who haven't played today, and one-time notice for reminders."

    def handle(self, *args, **options):
        # Current date in IST
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)
        today_ist = now_ist.date()

        # Determine today's window in UTC for querying attempt_date (timezone-aware)
        # We consider any play today in any language as 'played'
        start_of_day_ist = ist.localize(datetime.combine(today_ist, datetime.min.time()))
        end_of_day_ist = ist.localize(datetime.combine(today_ist, datetime.max.time()))
        start_utc = start_of_day_ist.astimezone(timezone.utc)
        end_utc = end_of_day_ist.astimezone(timezone.utc)

        self.stdout.write(self.style.NOTICE(f"Sending reminders for {today_ist} IST (now {now_ist:%H:%M})"))

        # One-time informational notice to opted-in users who haven't received it
        notice_subject = "SPOT-ify reminders enabled"
        notice_body = (
            "Hi there!\n\n"
            "You've been opted in to daily reminders to play SPOT-ify. "
            "You'll receive one reminder each day before 7:30 AM IST if you haven't played yet.\n\n"
            "You can turn this off anytime from your Profile page.\n\n"
            "Play now: https://webzombies.pythonanywhere.com/tamil/\n\n"
            "- Team SPOT-ify"
        )

        profiles_needing_notice = UserProfile.objects.filter(
            email_notifications_opt_in=True,
            email_notifications_notice_sent=False,
            user__email__isnull=False
        ).select_related('user')

        sent_notices = 0
        for profile in profiles_needing_notice:
            user = profile.user
            if not user.email:
                continue
            try:
                send_mail(
                    subject=notice_subject,
                    message=notice_body,
                    from_email=None,  # use DEFAULT_FROM_EMAIL
                    recipient_list=[user.email],
                    fail_silently=True,
                )
                profile.email_notifications_notice_sent = True
                profile.save(update_fields=['email_notifications_notice_sent'])
                sent_notices += 1
            except Exception:
                # fail silently per send_mail
                pass

        self.stdout.write(self.style.SUCCESS(f"Sent notices: {sent_notices}"))

        # Daily reminder to users who haven't played today in any language
        reminder_subject = "Reminder: Play today’s SPOT-ify before it’s gone!"
        reminder_body_template = (
            "Hey {username},\n\n"
            "Your daily music challenge awaits! You haven't played yet today.\n\n"
            "Play now: https://webzombies.pythonanywhere.com/tamil/\n\n"
            "Tip: Scores and streaks are tracked per language (Tamil/English/Hindi).\n\n"
            "- Team SPOT-ify"
        )

        # Users opted-in with an email address
        candidates = User.objects.filter(
            userprofile__email_notifications_opt_in=True,
            email__isnull=False
        ).select_related('userprofile')

        sent_reminders = 0
        for user in candidates:
            # Has played today in any language?
            played_today = UserScore.objects.filter(
                user=user,
                attempt_date__gte=start_utc,
                attempt_date__lte=end_utc,
            ).exists()

            if played_today:
                continue

            # Send reminder
            try:
                body = reminder_body_template.format(username=user.username)
                send_mail(
                    subject=reminder_subject,
                    message=body,
                    from_email=None,  # use DEFAULT_FROM_EMAIL
                    recipient_list=[user.email],
                    fail_silently=True,
                )
                sent_reminders += 1
            except Exception:
                # ignore failures for now
                pass

        self.stdout.write(self.style.SUCCESS(f"Sent reminders: {sent_reminders}"))