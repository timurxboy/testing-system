from fastapi import Depends, HTTPException, status

from apps.auth.domain.roles import Role
from apps.auth.models.admin_user import AdminUser
from apps.auth.api.deps import get_current_user


def require_role(*allowed_roles: Role):
    async def checker(
        user: AdminUser = Depends(get_current_user),
    ) -> AdminUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return checker
