from pydantic import BaseModel, EmailStr

# 로그인 요청 시 사용
class LoginRequest(BaseModel):
    username: EmailStr
    password: str

# JWT 토큰 응답
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# 토큰 내 사용자 정보
class TokenData(BaseModel):
    sub: str | None = None  # 사용자 이메일
    role: str | None = "user"  # 권한 (user / admin)
