from fastapi import APIRouter, Request, Depends, HTTPException, Cookie
from authlib.integrations.starlette_client import OAuth
from fastapi.responses import JSONResponse, Response, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt
import os

from database import getDB
from models import User

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

router = APIRouter()

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
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
        except Exception:
            pass

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
        try:
            db.commit()
            db.refresh(user)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database commit failed: {e}")

    user_data = {"sub": str(user.id), "username": user.username, "email": user.email}
    access_token = create_access_token(data=user_data)

    response = JSONResponse(
        content={
            "message": "Login successful",
            "user": {"username": user.username, "email": user.email},
            "token_type": "bearer",
        }
    )
    frontend_url = "http://localhost:5173/symptoms"
    response = RedirectResponse(url=frontend_url)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=False,
        secure=False,  # Set True in production with HTTPS
        samesite="lax",
        max_age=3600,
    )

    return response

@router.get("/me")
async def get_current_user(access_token: str = Cookie(None), db: Session = Depends(getDB)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return {"user": {"username": user.username, "email": user.email}}



@router.post("/logout")
async def logout():
    response = Response(content="Logged out")
    # Clear cookie by setting max_age=0
    response.delete_cookie(key="access_token", path="/")
    return response