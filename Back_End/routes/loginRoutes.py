from fastapi import APIRouter, Request, Depends, HTTPException
from authlib.integrations.starlette_client import OAuth
from starlette.responses import RedirectResponse
from database import getDB
from models import User
from sqlalchemy.orm import Session
import os

router = APIRouter()

# Configure OAuth with environment variables or settings
oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    },
)

@router.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/auth")
async def auth(request: Request, db: Session = Depends(getDB)):
    token = await oauth.google.authorize_access_token(request)
    user_info = None

    if "id_token" in token:
        try:
            user_info = await oauth.google.parse_id_token(request, token)
        except Exception as e:
            print("ID token parsing failed:", e)

    if not user_info:
        user_info = await oauth.google.userinfo(token=token)

    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to fetch user info")
    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not found in Google account")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(username=email.split("@")[0], email=email, hashed_password=None)
        db.add(user)
        db.commit()
        db.refresh(user)


    #use tokens here

    return {"message": "Login successful", "user": {"username": user.username, "email": user.email}}