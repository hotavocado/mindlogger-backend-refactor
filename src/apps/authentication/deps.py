from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.websockets import WebSocket
from jose import JWTError, jwt
from pydantic import EmailStr, ValidationError

from apps.authentication.domain.login import UserLoginRequest
from apps.authentication.domain.token import InternalToken, JWTClaim, TokenPayload, TokenPurpose
from apps.authentication.errors import AuthenticationError
from apps.authentication.services import AuthenticationService
from apps.users.cruds.user import UsersCRUD
from apps.users.domain import User
from config import settings
from infrastructure.database import atomic
from infrastructure.database.deps import get_session

oauth2_oauth = OAuth2PasswordBearer(tokenUrl="/auth/openapi", scheme_name="Bearer")


async def get_current_user_for_ws(websocket: WebSocket, session=Depends(get_session)):
    authorization = websocket.headers.get("sec-websocket-protocol")
    try:
        if not authorization:
            raise ValueError
        scheme, token = authorization.split("|")
        if scheme.lower() != "bearer":
            raise ValueError
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    async with atomic(session):
        try:
            payload = jwt.decode(
                token,
                settings.authentication.access_token.secret_key,
                algorithms=[settings.authentication.algorithm],
            )
            token_data = TokenPayload(**payload)

            if datetime.utcfromtimestamp(token_data.exp) < datetime.utcnow():
                raise AuthenticationError
        except (JWTError, ValidationError):
            raise AuthenticationError

        # Check if the token is in the blacklist
        revoked = await AuthenticationService(session).is_revoked(InternalToken(payload=token_data, raw_token=token))
        if revoked:
            raise AuthenticationError

        user = await UsersCRUD(session).get_by_id(id_=token_data.sub)

    return user


def get_current_token(type_: TokenPurpose = TokenPurpose.ACCESS):
    async def _get_current_token(
        token: str = Depends(oauth2_oauth),
    ) -> InternalToken:
        try:
            key = settings.authentication.access_token.secret_key
            if type_ == TokenPurpose.REFRESH:
                key = settings.authentication.refresh_token.secret_key
            payload = jwt.decode(
                token,
                key,
                algorithms=[settings.authentication.algorithm],
            )

            token_payload = TokenPayload(**payload)

            if datetime.utcfromtimestamp(token_payload.exp) < datetime.utcnow():
                raise AuthenticationError
        except (JWTError, ValidationError):
            raise AuthenticationError

        return InternalToken(payload=token_payload, raw_token=token)

    return _get_current_token


async def get_current_user(
    token: InternalToken = Depends(get_current_token()),
    session=Depends(get_session),
) -> User:
    async with atomic(session):
        # Check if the token is in the blacklist
        revoked = await AuthenticationService(session).is_revoked(token)
        if revoked:
            raise AuthenticationError

        user = await UsersCRUD(session).get_by_id(id_=token.payload.sub)
        await UsersCRUD(session).update_last_seen_by_id(token.payload.sub)

    return user


async def openapi_auth(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session=Depends(get_session),
):
    async with atomic(session):
        user_login_schema = UserLoginRequest(email=EmailStr(form_data.username), password=form_data.password)
        user: User = await AuthenticationService(session).authenticate_user(user_login_schema)
        if not user:
            raise AuthenticationError

        access_token = AuthenticationService.create_access_token({JWTClaim.sub: str(user.id)})

    return {
        "access_token": access_token,
        "token_type": settings.authentication.token_type,
    }
