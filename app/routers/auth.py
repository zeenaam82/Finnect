from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import bcrypt
from datetime import timedelta
from app.core.security import create_access_token
from app.schemas.auth import Token

router = APIRouter(prefix="/auth", tags=["auth"])

# 임시 고정 해시값
pw1 = "secret"
hashed1 = bcrypt.hashpw(pw1.encode(), bcrypt.gensalt())
pw2 = "adminsecret"
hashed2 = bcrypt.hashpw(pw2.encode(), bcrypt.gensalt())

# 임시 유저 검증 (실제: DB 조회, bcrypt 비교)
fake_users_db = {
    "user@example.com": {
        "username": "user@example.com",
        # "password": bcrypt.hashpw("secret".encode(), bcrypt.gensalt()),
        "password": hashed1,
        "role": "user"
    },
    "admin@example.com": {
        "username": "admin@example.com",
        # "password": bcrypt.hashpw("adminsecret".encode(), bcrypt.gensalt()),
        "password": hashed2,
        "role": "admin"
    }
}

@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not bcrypt.checkpw(form_data.password.encode(), user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=60)
    token = create_access_token(
        {
            "sub": user["username"],
            "role": user["role"]
        }, 
         expires_delta=access_token_expires
    )
    
    return {"access_token": token, "token_type": "bearer"}
