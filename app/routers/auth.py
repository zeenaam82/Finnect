from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.integrations.django_bridge import core_models_user as User
from app.core.security import create_access_token
from datetime import timedelta
from app.schemas.auth import Token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"Have User: {User.objects.count()}")
    # Django ORM으로 사용자 조회
    try:
        user = User.objects.get(email=form_data.username)
    except User.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username"
        )

    # 비밀번호 검증
    if not user.check_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    # JWT 토큰 생성
    access_token_expires = timedelta(minutes=60)
    token = create_access_token(
        {"sub": user.email, "role": user.role},
        expires_delta=access_token_expires
    )

    return {"access_token": token, "token_type": "bearer"}
