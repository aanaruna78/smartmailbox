from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer

from app.db.session import get_db
from app.core.security import jwt, oauth_google
from app.core.config import settings
from app.models.user import User
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
    return {"message": "Login successful"}

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
