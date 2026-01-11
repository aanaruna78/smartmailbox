from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security.rbac import RoleChecker
from app.core.security.deps import get_current_active_user
from app.models.user import User
from app.schemas.user import User as UserSchema, UserUpdate
from app.db.session import get_db
from app.services.audit import create_audit_log

router = APIRouter()

allow_admin = RoleChecker(["admin"])

@router.get("/admin/users", response_model=List[UserSchema], dependencies=[Depends(allow_admin)])
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    users = db.query(User).all()
    return users

@router.patch("/admin/users/{user_id}", response_model=UserSchema, dependencies=[Depends(allow_admin)])
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_update.role is not None:
        user.role = user_update.role
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
        
    db.commit()
    db.refresh(user)
    
    # Audit logic
    await create_audit_log(
        db, 
        "USER_UPDATE", 
        user_id=current_user.id, 
        details={
            "target_user_id": user_id, 
            "updates": user_update.dict(exclude_unset=True)
        }
    )
    
    return user
