from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from pwdlib import PasswordHash
import jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import os
from exceptions import AuthError
from db import make_session, Staff


password_hash = PasswordHash.recommended()
SECRET_KEY = os.getenv("SECRET_KEY1", "")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    

#==============HELPERS=================
#=========================================
def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password):
    return password_hash.hash(password)

def create_access_token(data: dict):
    expires_delta:timedelta = timedelta(minutes = int(os.getenv("ACCESS_TOKEN_EXPIRATION_IN_MINUTES", 30)))
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None

def is_logged_in(request: Request):
    token = request.session.get("token")

    if not token:
        return False

    payload = decode_access_token(token)
    if not payload:
        return False
    
    username = payload.get("username")

    if not username:
        return False

    return True


def create_superuser_staff(session: Session):
    super_user_name = os.getenv("SUPER_USER_NAME")
    super_user_password = os.getenv("SUPER_USER_PASSWORD")

    if not super_user_name or not super_user_password:
        raise AuthError("Please set env vars for SUPER_USER_NAME and SUPER_USER_PASSWORD")

    existing_super_user = session.query(Staff).filter_by(username = super_user_name).first()

    if existing_super_user:
        return

    super_user_password = get_password_hash(super_user_password)
    super_user_staff = Staff(
        username = super_user_name,
        password = super_user_password,
        first_name = super_user_name,
        last_name = super_user_name,
        other_names = super_user_name
    )
    session.add(super_user_staff)
    session.commit()



#==============AUTH CLASS=================
#=========================================
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
                "staff_id": staff.id,
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
        return is_logged_in(request)