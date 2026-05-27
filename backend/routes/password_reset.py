from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
import secrets
import bcrypt
import os
import sys
import resend
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import supabase

resend.api_key = os.getenv("RESEND_API_KEY")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

router = APIRouter()


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    result = supabase.table("users_waitlist").select("id, name, email").eq("email", data.email).execute()

    # Always return success so we don't leak whether an email exists
    if not result.data:
        return {"success": True}

    user = result.data[0]
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

    supabase.table("password_reset_tokens").insert({
        "user_id":    user["id"],
        "token":      token,
        "expires_at": expires_at,
    }).execute()

    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
    first_name = (user.get("name") or "there").split()[0]

    resend.Emails.send({
        "from":    "resonance <onboarding@resend.dev>",
        "to":      [data.email],
        "subject": "reset your resonance password",
        "html":    f"""
        <div style="font-family:-apple-system,sans-serif;max-width:480px;margin:40px auto;color:#1a1a1a">
          <div style="font-size:13px;color:#999;letter-spacing:2px;margin-bottom:24px">resonance</div>
          <h2 style="font-weight:400;font-size:22px;margin-bottom:16px">hi {first_name},</h2>
          <p style="color:#555;line-height:1.7;margin-bottom:32px">
            we got a request to reset your password. click below — this link expires in 1 hour.
          </p>
          <a href="{reset_link}" style="background:#1a1a1a;color:#f5f4f0;padding:12px 28px;text-decoration:none;font-size:13px;letter-spacing:0.04em">
            reset password
          </a>
          <p style="color:#bbb;font-size:12px;margin-top:40px">
            if you didn't request this, ignore this email.
          </p>
        </div>
        """,
    })

    return {"success": True}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    result = supabase.table("password_reset_tokens").select("*").eq("token", data.token).eq("used", False).execute()

    if not result.data:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    token_row = result.data[0]
    expires_at = datetime.fromisoformat(token_row["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Reset link has expired")

    new_hash = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()
    user_id = token_row["user_id"]

    supabase.table("users_waitlist").update({"password_hash": new_hash}).eq("id", user_id).execute()
    supabase.table("password_reset_tokens").update({"used": True}).eq("id", token_row["id"]).execute()

    return {"success": True}
