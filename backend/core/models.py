from django.db import models
from django.utils import timezone
from django.db.models import JSONField
from django.contrib.auth.hashers import make_password, check_password

# 파일 업로드 기록
class UploadRecord(models.Model):
    filename = models.CharField(max_length=255)  # 업로드한 파일명
    uploaded_at = models.DateTimeField(default=timezone.now)  # 업로드 시각
    file_size = models.BigIntegerField(null=True, blank=True)  # 파일 크기 (Byte)

    # 이미지/CSV 결과 저장
    prediction = models.CharField(max_length=50, null=True, blank=True)  # 이미지 예측
    confidence = models.FloatField(null=True, blank=True)               # 이미지 신뢰도
    statistics = JSONField(null=True, blank=True)                        # CSV 통계 결과

    # CSV 결과
    statistics = JSONField(null=True, blank=True)  # CSV 통계 결과

    # 공용 처리 상태
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILURE", "Failure"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    def __str__(self):
        return f"{self.filename} ({self.uploaded_at})"


# 챗봇 대화 기록
class ChatRecord(models.Model):
    user_message = models.TextField()  # 사용자가 입력한 메시지
    bot_response = models.TextField()  # 챗봇의 응답
    created_at = models.DateTimeField(default=timezone.now)  # 대화 발생 시각

    def __str__(self):
        return f"[{self.created_at}] {self.user_message[:20]}..."


# FAQ 데이터 (사전 등록된 질의응답)
class FAQ(models.Model):
    question = models.TextField()
    answer = models.TextField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.question

# Intent DB 모델
class Intent(models.Model):
    name = models.CharField(max_length=50)
    keywords = models.CharField(max_length=255, default="default_keyword")  # 쉼표로 구분
    response = models.TextField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.question

# 로그인 User 관리
class User(models.Model):
    email = models.EmailField(unique=True)
    hashed_password = models.CharField(max_length=128)
    role = models.CharField(max_length=20, default="user")
    created_at = models.DateTimeField(default=timezone.now)

    def set_password(self, raw_password):
        self.hashed_password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.hashed_password)

    def __str__(self):
        return self.email