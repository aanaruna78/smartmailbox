from fastapi import Depends, HTTPException, status
from typing import List, Union
from app.models.user import User
from app.core.security.deps import get_current_active_user

class RoleChecker:
    def __init__(self, allowed_roles: Union[List[str], str]):
        if isinstance(allowed_roles, str):
            self.allowed_roles = [allowed_roles]
        else:
            self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_active_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return user
