import uuid
from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        INFO = "INFO", "Info"
        WARNING = "WARNING", "Warning"
        SUCCESS = "SUCCESS", "Success"
        ERROR = "ERROR", "Error"

    class Category(models.TextChoices):
        WORKFLOW = "WORKFLOW", "Workflow"
        CHAT = "CHAT", "Chat"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.INFO,
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.WORKFLOW,
    )
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.title}"


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preference",
    )
    include_chat_in_general_notifications = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification Preference - {self.user}"