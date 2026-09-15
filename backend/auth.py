from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from pwdlib import PasswordHash
import jwt
from datetime import datetime, timedelta, timezone
import os
from db import make_session, Staff


password_hash = PasswordHash.recommended()
SECRET_KEY = os.getenv("SECRET_KEY1", "")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    

#helpers
def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password):
    return password_hash.hash(password)

def create_access_token(data: dict):
    expires_delta:timedelta = timedelta(minutes = int(os.getenv("ACCESS_TOKEN_EXPIRATION_IN_MINUTES", 60)))
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt   

#Auth Class
class AuthAdmin(AuthenticationBackend):
    async def login(self, request: Request) -> bool|RedirectResponse:
        form = await request.form()
        username, password = form["username"], form["password"]

        session = make_session()
        try:
            staff = session.query(Staff).filter_by(username = username).first()
            if not staff:
                return False

            if not verify_password(password, staff.password):
                return False

            token = create_access_token({
                "id": staff.id,
                "username": staff.username,
                "first_name": staff.first_name,
                "last_name": staff.last_name
            })

            request.session.update({"token": token})

            return True
        except Exception:
            return False
        finally:
            session.close()


    async def logout(self, request: Request) -> bool|RedirectResponse:
        request.session.clear()
        return True


    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        if not token:
            return False

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")

        if not username:
            return False

        return True