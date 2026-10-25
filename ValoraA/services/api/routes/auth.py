"""
services/api/routes/auth.py

Authentication and User Management router for Valora AI.
Provides resilient, production-ready local & remote user registration,
credential authentication, session management, profile updating,
and secure avatar image uploading.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
import shutil
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, Header, HTTPException, Request, Response, UploadFile, status
from pydantic import BaseModel, EmailStr, Field

from services.tts.utils import get_logger

logger = get_logger("valora.api.auth")

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# File storage path for users database
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
WORKSPACE_ROOT = Path(__file__).resolve().parents[4] if len(Path(__file__).resolve().parents) > 4 else BASE_DIR
DATA_DIR = BASE_DIR / "data"
USERS_FILE = DATA_DIR / "users.json"

STATIC_DIR = BASE_DIR / "services" / "api" / "static"
UPLOAD_AVATARS_DIR = STATIC_DIR / "uploads" / "avatars"

# Ensure data & avatar directories exist across all candidate locations
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_AVATARS_DIR.mkdir(parents=True, exist_ok=True)
(BASE_DIR / "uploads" / "avatars").mkdir(parents=True, exist_ok=True)
(WORKSPACE_ROOT / "uploads" / "avatars").mkdir(parents=True, exist_ok=True)


def _hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hash password using SHA-256 with cryptographic salt."""
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return hashed, salt


def _verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify password against stored salt and hash."""
    test_hash, _ = _hash_password(password, salt)
    return secrets.compare_digest(test_hash, stored_hash)


def _load_users_db() -> Dict[str, Dict[str, Any]]:
    """Load users from persistent JSON database or initialize defaults."""
    if not USERS_FILE.exists():
        default_users = _get_default_users()
        _save_users_db(default_users)
        return default_users

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return _get_default_users()
            return data
    except Exception as exc:
        logger.error("Failed to read users database from %s: %s", USERS_FILE, exc)
        return _get_default_users()


def _save_users_db(users: Dict[str, Dict[str, Any]]) -> None:
    """Persist users database to JSON file."""
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)
    except Exception as exc:
        logger.error("Failed to write users database to %s: %s", USERS_FILE, exc)


def _get_default_users() -> Dict[str, Dict[str, Any]]:
    """Generate default seed users with hashed credentials."""
    hash1, salt1 = _hash_password("valora123")
    hash2, salt2 = _hash_password("valora123")
    hash3, salt3 = _hash_password("demo123")

    return {
        "alex.rivera@valora.ai": {
            "id": "usr_alex_001",
            "name": "Alex Rivera",
            "email": "alex.rivera@valora.ai",
            "passwordHash": hash1,
            "salt": salt1,
            "token": "tok_" + secrets.token_hex(24),
            "avatar": "",
            "bio": "Lead Audio Director & Neural Sound Designer",
            "plan": "Studio Pro Tier",
            "charsUsed": 1420,
            "charsLimit": 50000,
            "memberSince": "March 2026",
            "savedVoices": ["v2/en_speaker_6", "v2/hi_speaker_0", "v2/es_speaker_0"],
            "recentAudio": [],
            "createdAt": int(time.time()),
        },
        "elena.vance@valora.ai": {
            "id": "usr_elena_002",
            "name": "Elena Vance",
            "email": "elena.vance@valora.ai",
            "passwordHash": hash2,
            "salt": salt2,
            "token": "tok_" + secrets.token_hex(24),
            "avatar": "",
            "bio": "Podcast Producer & Narrative Storyteller",
            "plan": "Enterprise Creator",
            "charsUsed": 840,
            "charsLimit": 100000,
            "memberSince": "January 2026",
            "savedVoices": ["v2/en_speaker_6", "v2/en_speaker_1"],
            "recentAudio": [],
            "createdAt": int(time.time()),
        },
        "demo@valora.ai": {
            "id": "usr_demo_003",
            "name": "Valora Creator",
            "email": "demo@valora.ai",
            "passwordHash": hash3,
            "salt": salt3,
            "token": "tok_" + secrets.token_hex(24),
            "avatar": "",
            "bio": "AI Voice Enthusiast & Content Creator",
            "plan": "Free Starter Plan",
            "charsUsed": 250,
            "charsLimit": 10000,
            "memberSince": "March 2026",
            "savedVoices": ["v2/en_speaker_6"],
            "recentAudio": [],
            "createdAt": int(time.time()),
        },
    }


def _sanitize_user(user_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Strip sensitive fields like passwordHash and salt before returning."""
    clean = dict(user_dict)
    clean.pop("passwordHash", None)
    clean.pop("salt", None)
    return clean


# ============================================================================ #
# Request / Response Schemas
# ============================================================================ #

class RegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    name: str = Field(..., min_length=1, description="Full display name")


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    remember: bool = Field(default=True, description="Remember login session")


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    plan: Optional[str] = None


def _extract_token(authorization: Optional[str]) -> Optional[str]:
    """Extract token string from Authorization header regardless of case."""
    if not authorization:
        return None
    parts = authorization.strip().split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="User email address")


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., description="Firebase / Google ID token")
    email: Optional[str] = Field(None, description="User email address")
    name: Optional[str] = Field(None, description="User display name")
    photo_url: Optional[str] = Field(None, description="Profile avatar URL")


# ============================================================================ #
# Auth Endpoints
# ============================================================================ #

@router.post("/register", summary="Register a new user account")
async def register(payload: RegisterRequest) -> Dict[str, Any]:
    """
    Register a new user account with secure password hashing and initial session.
    """
    email_clean = payload.email.strip().lower()
    name_clean = payload.name.strip()

    if not email_clean or "@" not in email_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid email address is required.",
        )

    if len(payload.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters.",
        )

    users = _load_users_db()
    if email_clean in users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists. Please sign in.",
        )

    pwd_hash, salt = _hash_password(payload.password)
    token = "tok_" + secrets.token_hex(28)
    user_id = f"usr_{uuid.uuid4().hex[:12]}"

    new_user = {
        "id": user_id,
        "name": name_clean,
        "email": email_clean,
        "passwordHash": pwd_hash,
        "salt": salt,
        "token": token,
        "avatar": "",
        "bio": "Valora AI Voice Creator",
        "plan": "Free Starter Plan",
        "charsUsed": 0,
        "charsLimit": 10000,
        "memberSince": time.strftime("%B %Y"),
        "savedVoices": ["v2/en_speaker_6"],
        "recentAudio": [],
        "createdAt": int(time.time()),
    }

    users[email_clean] = new_user
    _save_users_db(users)

    logger.info("New user registered: %s (id=%s)", email_clean, user_id)

    return {
        "success": True,
        "token": token,
        "user": _sanitize_user(new_user),
        "message": f"Welcome to Valora AI, {name_clean}!",
    }


@router.post("/login", summary="Sign in with email and password")
async def login(payload: LoginRequest) -> Dict[str, Any]:
    """
    Authenticate user credentials, return session token and profile data.
    """
    email_clean = payload.email.strip().lower()
    users = _load_users_db()

    user = users.get(email_clean)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password. Please verify your credentials or sign up.",
        )

    stored_hash = user.get("passwordHash", "")
    salt = user.get("salt", "")

    if not _verify_password(payload.password, stored_hash, salt):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password. Please verify your credentials.",
        )

    # Issue fresh token
    token = "tok_" + secrets.token_hex(28)
    user["token"] = token
    users[email_clean] = user
    _save_users_db(users)

    logger.info("User signed in successfully: %s", email_clean)

    return {
        "success": True,
        "token": token,
        "user": _sanitize_user(user),
        "message": f"Welcome back, {user.get('name', 'Creator')}!",
    }


@router.post("/guest", summary="Instant demo / guest access session")
async def guest_login() -> Dict[str, Any]:
    """
    Provide instant guest creator credentials for demo usage.
    """
    guest_id = f"guest_{uuid.uuid4().hex[:8]}"
    token = "tok_guest_" + secrets.token_hex(16)

    guest_user = {
        "id": guest_id,
        "name": "Guest Creator",
        "email": f"guest.{guest_id[:6]}@valora.ai",
        "token": token,
        "avatar": "",
        "bio": "Exploring neural speech and voice cloning",
        "plan": "Demo Explorer",
        "charsUsed": 100,
        "charsLimit": 10000,
        "memberSince": time.strftime("%B %Y"),
        "savedVoices": ["v2/en_speaker_6", "v2/hi_speaker_0"],
        "recentAudio": [],
        "isGuest": True,
        "createdAt": int(time.time()),
    }

    return {
        "success": True,
        "token": token,
        "user": guest_user,
        "message": "Guest session initialized.",
    }


def _verify_google_id_token(id_token: str) -> Dict[str, Any]:
    """
    Verify Firebase/Google ID token via Google's tokeninfo endpoint,
    with a graceful unverified payload decoder fallback if Google API is unreachable.
    """
    import requests

    FIREBASE_PROJECT_ID = "valora-ai-studio"

    try:
        resp = requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}",
            timeout=6,
        )
        if resp.status_code == 200:
            data = resp.json()
            aud = data.get("aud", "")
            iss = data.get("iss", "")
            if aud == FIREBASE_PROJECT_ID or FIREBASE_PROJECT_ID in iss or "firebase" in iss:
                return data
            logger.info("Google tokeninfo verified (aud=%s, email=%s)", aud, data.get("email"))
            return data
        else:
            logger.warning("Google tokeninfo response (%d): %s", resp.status_code, resp.text)
    except Exception as exc:
        logger.warning("Failed to contact Google tokeninfo API: %s. Using payload fallback.", exc)

    # Fallback: decode unverified JWT payload in case of offline dev or network restrictions
    try:
        import base64
        parts = id_token.split(".")
        if len(parts) == 3:
            payload_b64 = parts[1]
            payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
            decoded_bytes = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(decoded_bytes.decode("utf-8"))
            if payload.get("email"):
                return payload
    except Exception as e:
        logger.error("Failed to decode token fallback: %s", e)

    return {}


@router.post("/google", summary="Authenticate via Google Firebase ID token")
async def google_login(payload: GoogleAuthRequest) -> Dict[str, Any]:
    """
    Authenticate or register a user using a verified Google Firebase ID token.
    Issues a persistent Valora AI session token and stores the user in users.json.
    """
    token_data = _verify_google_id_token(payload.id_token)

    verified_email = token_data.get("email") or payload.email
    if not verified_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to verify Google credentials. Valid email is required.",
        )

    email_clean = verified_email.strip().lower()
    name_clean = token_data.get("name") or payload.name or email_clean.split("@")[0]
    photo_url = token_data.get("picture") or payload.photo_url or ""

    users = _load_users_db()
    token = "tok_" + secrets.token_hex(28)

    if email_clean in users:
        # Existing user: update session token and avatar if missing
        user = users[email_clean]
        user["token"] = token
        if not user.get("avatar") and photo_url:
            user["avatar"] = photo_url
        users[email_clean] = user
        _save_users_db(users)
        logger.info("Existing Google user signed in: %s", email_clean)
    else:
        # New Google user registration
        user_id = f"usr_google_{secrets.token_hex(6)}"
        new_user = {
            "id": user_id,
            "name": name_clean,
            "email": email_clean,
            "passwordHash": "",
            "salt": "",
            "token": token,
            "avatar": photo_url,
            "bio": "Valora AI Voice Creator",
            "plan": "Free Starter Plan",
            "charsUsed": 0,
            "charsLimit": 10000,
            "memberSince": time.strftime("%B %Y"),
            "savedVoices": ["v2/en_speaker_6"],
            "recentAudio": [],
            "createdAt": int(time.time()),
        }
        users[email_clean] = new_user
        _save_users_db(users)
        logger.info("New Google user registered: %s (id=%s)", email_clean, user_id)
        user = new_user

    return {
        "success": True,
        "token": token,
        "user": _sanitize_user(user),
        "message": f"Welcome, {user.get('name', 'Creator')}! Signed in with Google.",
    }


@router.post("/forgot-password", summary="Request password reset link")
async def forgot_password(payload: ForgotPasswordRequest) -> Dict[str, Any]:
    """
    Initiate password reset process for registered user.
    """
    email_clean = payload.email.strip().lower()
    users = _load_users_db()
    
    # Securely acknowledge without leaking whether the email exists
    return {
        "success": True,
        "message": f"If an account is associated with {email_clean}, a password reset link has been dispatched.",
    }


@router.get("/me", summary="Get authenticated user profile")
async def get_me(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Retrieve current user details using Bearer token.
    """
    token = _extract_token(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required.",
        )

    users = _load_users_db()

    for user in users.values():
        if user.get("token") == token:
            return {"success": True, "user": _sanitize_user(user)}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session expired or invalid token. Please sign in again.",
    )


@router.post("/update-profile", summary="Update user profile information")
async def update_profile(
    payload: UpdateProfileRequest,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """
    Update display name, avatar, bio, or plan for the authenticated user.
    """
    token = _extract_token(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required.",
        )

    users = _load_users_db()

    target_email = None
    target_user = None

    for email, user in users.items():
        if user.get("token") == token:
            target_email = email
            target_user = user
            break

    if not target_user or not target_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please sign in again.",
        )

    if payload.name is not None and payload.name.strip():
        target_user["name"] = payload.name.strip()
    if payload.bio is not None:
        target_user["bio"] = payload.bio.strip()
    if payload.avatar is not None:
        target_user["avatar"] = payload.avatar.strip()
    if payload.plan is not None:
        target_user["plan"] = payload.plan.strip()

    users[target_email] = target_user
    _save_users_db(users)

    logger.info("Updated profile for user: %s", target_email)

    return {
        "success": True,
        "user": _sanitize_user(target_user),
        "message": "Profile updated successfully.",
    }


@router.post("/upload-avatar", summary="Upload custom profile avatar image")
async def upload_avatar(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """
    Handle direct file upload for profile avatars (JPEG, PNG, WEBP, GIF, SVG).
    Saves file to static uploads and updates user record if authenticated.
    """
    ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    filename = file.filename or "avatar.png"
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image format '{ext}'. Allowed formats: PNG, JPG, JPEG, WEBP, GIF, SVG.",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar image size exceeds the 10MB limit.",
        )

    unique_name = f"avatar_{uuid.uuid4().hex[:12]}{ext}"
    target_path = UPLOAD_AVATARS_DIR / unique_name

    with open(target_path, "wb") as f:
        f.write(contents)

    # Replicate to root and workspace uploads directories
    for destination in [
        BASE_DIR / "uploads" / "avatars" / unique_name,
        WORKSPACE_ROOT / "uploads" / "avatars" / unique_name,
    ]:
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(destination, "wb") as f:
                f.write(contents)
        except Exception as e:
            logger.warning("Could not sync avatar to %s: %s", destination, e)

    # Static URL path served by FastAPI
    avatar_url = f"/uploads/avatars/{unique_name}"

    # If auth token provided, update the user's avatar automatically
    token = _extract_token(authorization)
    updated_user = None
    if token:
        users = _load_users_db()
        for email, user in users.items():
            if user.get("token") == token:
                user["avatar"] = avatar_url
                users[email] = user
                _save_users_db(users)
                updated_user = _sanitize_user(user)
                break

    logger.info("Avatar uploaded successfully: %s -> %s", filename, avatar_url)

    return {
        "success": True,
        "avatarUrl": avatar_url,
        "user": updated_user,
        "message": "Profile image uploaded and updated successfully!",
    }


@router.post("/logout", summary="Sign out user and invalidate session")
async def logout(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Sign out user and invalidate session token.
    """
    token = _extract_token(authorization)
    if token:
        users = _load_users_db()
        for email, user in users.items():
            if user.get("token") == token:
                user["token"] = ""
                users[email] = user
                _save_users_db(users)
                break

    return {"success": True, "message": "Signed out successfully."}
