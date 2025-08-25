from django.contrib import admin
from .models import UploadRecord, ChatRecord, FAQ, Intent


@admin.register(UploadRecord)
class UploadRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "filename", "file_size", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("filename",)


@admin.register(ChatRecord)
class ChatRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "user_message", "bot_response", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user_message", "bot_response")


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "answer", "active")
    list_filter = ("active",)
    search_fields = ("question", "answer")

@admin.register(Intent)
class IntentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "response", "active")
    list_filter = ("active",)
    search_fields = ("name", "keywords", "response")