from django.db import models


class ConversationMemory(models.Model):
    user_id = models.CharField(max_length=100, db_index=True)
    conversation_id = models.CharField(max_length=100, db_index=True)
    key = models.CharField(max_length=100)
    value = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user_id", "conversation_id", "key")
        verbose_name = "Conversation Memory"
        verbose_name_plural = "Conversation Memories"

    def __str__(self):
        return f"{self.user_id}/{self.conversation_id}/{self.key}"
