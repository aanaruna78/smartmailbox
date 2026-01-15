from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer

from app.db.session import get_db
from app.core.security import jwt, oauth_google
from app.core.config import settings
from app.models.user import User
from app.models.mailbox import Mailbox
from app.schemas.user import Token, GoogleLogin, User as UserSchema
from app.core.security.deps import get_current_active_user

router = APIRouter()

from app.services.audit import create_audit_log
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security.jwt import create_access_token, create_refresh_token, pwd_context

@router.post("/login", response_model=Token)
async def login_for_access_token(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not user.hashed_password:
        await create_audit_log(db, "LOGIN_FAILED", request=request, details={"reason": "Invalid User"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not pwd_context.verify(form_data.password, user.hashed_password):
        await create_audit_log(db, "LOGIN_FAILED", user_id=user.id, request=request, details={"reason": "Invalid Password"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(subject=user.id)
    
    # Set cookies for frontend convenience
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=settings.ENV != "development",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    await create_audit_log(db, "LOGIN_SUCCESS", user_id=user.id, request=request)
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "refresh_token": refresh_token
    }

@router.post("/auth/google/login")
async def login_google(request: Request, response: Response, login_data: GoogleLogin, db: Session = Depends(get_db)):
    # 1. Verify Google Token
    google_user = await oauth_google.verify_google_token(login_data.token)
    if not google_user:
        await create_audit_log(db, "LOGIN_FAILED", request=request, details={"reason": "Invalid Token"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )
    
    # 2. Check if user exists
    email = google_user.get("email")
    if not email:
        await create_audit_log(db, "LOGIN_FAILED", request=request, details={"reason": "No Email"})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not found in Google token",
        )
        
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            full_name=google_user.get("name"),
            is_active=True,
            role="user"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        await create_audit_log(db, "USER_CREATED", user_id=user.id, request=request)
    
    if not user.is_active:
        await create_audit_log(db, "LOGIN_FAILED", user_id=user.id, request=request, details={"reason": "Inactive"})
        raise HTTPException(status_code=400, detail="Inactive user")

    # 3. Create Tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    refresh_token = jwt.create_refresh_token(subject=user.id)
    
    # 4. Set Cookies
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=settings.ENV != "development",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENV != "development",
        samesite="lax",
        max_age=7 * 24 * 60 * 60 # 7 days
    )
    
    await create_audit_log(db, "LOGIN_SUCCESS", user_id=user.id, request=request)
    return {
        "message": "Login successful",
        "access_token": access_token
    }

from pydantic import BaseModel as PydanticBaseModel

class GoogleOAuthLogin(PydanticBaseModel):
    access_token: str
    scope: str = None

@router.post("/auth/google/oauth")
async def login_google_oauth(request: Request, response: Response, login_data: GoogleOAuthLogin, db: Session = Depends(get_db)):
    """Handle OAuth access token from frontend for Gmail API access."""
    import httpx
    
    # 1. Get user info from Google using access token
    async with httpx.AsyncClient() as client:
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {login_data.access_token}"}
        )
        
        if userinfo_response.status_code != 200:
            await create_audit_log(db, "LOGIN_FAILED", request=request, details={"reason": "Invalid access token"})
            raise HTTPException(status_code=401, detail="Invalid Google access token")
        
        google_user = userinfo_response.json()
    
    # 2. Get or create user
    email = google_user.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not found")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            full_name=google_user.get("name"),
            is_active=True,
            role="user"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        await create_audit_log(db, "USER_CREATED", user_id=user.id, request=request)
    
    # 3. Store Google access token for Gmail API
    user.google_access_token = login_data.access_token
    
    # 3b. Auto-create default mailbox if it doesn't exist
    mailbox = db.query(Mailbox).filter(
        Mailbox.user_id == user.id,
        Mailbox.email_address == user.email
    ).first()
    
    if not mailbox:
        mailbox = Mailbox(
            user_id=user.id,
            email_address=user.email,
            provider="gmail",
            is_active=True
        )
        db.add(mailbox)
        
    db.commit()
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # 4. Create JWT tokens for session
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.create_access_token(subject=user.id, expires_delta=access_token_expires)
    refresh_token_val = jwt.create_refresh_token(subject=user.id)
    
    # 5. Set cookies
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=settings.ENV != "development",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token_val,
        httponly=True,
        secure=settings.ENV != "development",
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )
    
    await create_audit_log(db, "LOGIN_SUCCESS", user_id=user.id, request=request, details={"gmail_connected": True})
    return {
        "message": "Login successful", 
        "gmail_connected": True,
        "access_token": access_token
    }

@router.post("/auth/refresh")
async def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
         raise HTTPException(status_code=401, detail="Refresh token missing")
         
    try:
        payload = jwt.jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[jwt.ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("sub")
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = jwt.create_access_token(
            subject=user_id, expires_delta=access_token_expires
        )
        
        response.set_cookie(
            key="access_token",
            value=f"Bearer {new_access_token}",
            httponly=True,
            secure=settings.ENV != "development",
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
        await create_audit_log(db, "TOKEN_REFRESH", user_id=int(user_id), request=request)
        return {"message": "Token refreshed"}
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/auth/logout")
async def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    # Best effort to identify user before logout
    try:
        refresh_token = request.cookies.get("refresh_token")
        if refresh_token:
            payload = jwt.jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[jwt.ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                await create_audit_log(db, "LOGOUT", user_id=int(user_id), request=request)
    except:
        pass

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logout successful"}

@router.get("/auth/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
