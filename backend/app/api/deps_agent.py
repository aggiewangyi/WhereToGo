"""Agent 接口主体：优先 JWT（ToC 用户），其次可选 X-Agent-API-Key（自动化/对内）。"""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.config import get_settings
from app.core.security import decode_access_token
from app.crud.user import crud_user
from app.models.user import User

security_bearer_optional = HTTPBearer(auto_error=False)


async def get_agent_principal(
    db: AsyncSession = Depends(get_session),
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_bearer_optional)] = None,
    x_agent_api_key: Annotated[str | None, Header(alias="X-Agent-API-Key")] = None,
) -> User:
    settings = get_settings()

    if credentials and credentials.scheme.lower() == "bearer" and credentials.credentials:
        payload = decode_access_token(credentials.credentials)
        if payload is not None:
            sub = payload.get("sub")
            if sub is not None:
                try:
                    uid = int(sub)
                except (TypeError, ValueError):
                    uid = None
                else:
                    user = await crud_user.get(db, uid)
                    if user is not None and user.is_active:
                        return user

    expected = (settings.AGENT_SERVICE_API_KEY or "").strip()
    if expected:
        if (x_agent_api_key or "").strip() == expected:
            svc = await crud_user.get(db, int(settings.AGENT_SERVICE_USER_ID))
            if svc is None or not svc.is_active:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="AGENT_SERVICE_USER_ID 在库中不存在或未激活",
                )
            return svc
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请登录，或提供有效的 X-Agent-API-Key",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="请先登录",
    )
