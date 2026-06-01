"""
send_announcement.py

Sends the launch announcement email to all users in users_waitlist.
Run from backend/:
  python send_announcement.py
"""

import os
import sys
import time
import resend
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.connection import supabase

resend.api_key = os.getenv("RESEND_API_KEY")

BRIEFING_URL = "https://www.resonance-news.com/auth"


def send_announcement(name: str, email: str):
    first_name = (name or "there").split()[0]

    resend.Emails.send({
        "from":    "Poshitha and Kent <noreply@resonance-news.com>",
        "to":      [email],
        "subject": "From Poshitha and Kent: Resonance News",
        "html":    f"""
        <div style="font-family:-apple-system,Georgia,serif;max-width:560px;margin:48px auto;color:#1a1a1a;padding:0 24px">

          <div style="font-size:12px;color:#999;letter-spacing:3px;text-transform:uppercase;margin-bottom:40px">
            Resonance News
          </div>

          <p style="font-size:16px;line-height:1.8;margin-bottom:20px">Hi {first_name},</p>

          <p style="font-size:16px;line-height:1.8;margin-bottom:20px">
            We are excited to announce that your first briefing is now available to read!
            From here on out, you will receive a personalized collection of articles every
            morning based on the interests you described when signing up.
          </p>

          <p style="font-size:16px;line-height:1.8;margin-bottom:36px">
            Check it out here:
          </p>

          <a href="{BRIEFING_URL}"
             style="background:transparent;color:#1a1a1a;border:1px solid #1a1a1a;padding:14px 32px;
                    text-decoration:none;font-size:13px;letter-spacing:0.08em;font-family:sans-serif;
                    display:inline-block">
            Read my briefing
          </a>

          <p style="font-size:16px;line-height:1.8;margin-top:40px;margin-bottom:20px;color:#1a1a1a">
            If you get the chance, we would appreciate any feedback you may have to help us
            better understand how we are doing to ultimately improve your briefings. Any
            comments are helpful and they will be anonymous.
          </p>

          <p style="font-size:15px;line-height:1.8;margin-top:40px;color:#1a1a1a">
            Best regards,<br/>
            Poshitha and Kent<br/>
            <span style="color:#999;font-size:13px">Resonance News</span>
          </p>

        </div>
        """,
    })


def run():
    result = supabase.table("users").select("name, email").execute()
    users = result.data or []

    if not users:
        print("No users found in users_waitlist.")
        return

    print(f"Found {len(users)} users. Sending...\n")

    success = 0
    failed = 0
    for u in users:
        try:
            send_announcement(u["name"], u["email"])
            print(f"  ✓ {u['email']}")
            success += 1
        except Exception as e:
            print(f"  ✗ {u['email']} — {e}")
            failed += 1
        time.sleep(0.3)

    print(f"\nDone. {success} sent, {failed} failed.")


if __name__ == "__main__":
    run()
