from django.db import models
from django.utils import timezone


# 파일 업로드 기록
class UploadRecord(models.Model):
    filename = models.CharField(max_length=255)  # 업로드한 파일명
    uploaded_at = models.DateTimeField(default=timezone.now)  # 업로드 시각
    file_size = models.BigIntegerField(null=True, blank=True)  # 파일 크기 (Byte)

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
    question = models.CharField(max_length=500, unique=True)  # 질문
    answer = models.TextField()  # 답변
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.question
