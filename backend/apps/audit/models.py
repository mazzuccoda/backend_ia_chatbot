from django.db import models


class AuditLog(models.Model):
    STATUS_CHOICES = [
        ("ok", "OK"),
        ("error", "Error"),
        ("low_confidence", "Low Confidence"),
        ("rejected", "Rejected"),
        ("timeout", "Timeout"),
    ]

    user_id = models.CharField(max_length=100, blank=True, default="")
    conversation_id = models.CharField(max_length=100, blank=True, default="")
    message = models.TextField(blank=True, null=True)
    intent = models.CharField(max_length=100, blank=True, default="")
    tool_used = models.CharField(max_length=100, blank=True, default="")
    input_payload = models.JSONField(default=dict)
    output_payload = models.JSONField(default=dict)
    sql_generated = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ok")
    error_code = models.CharField(max_length=100, blank=True, null=True)
    execution_time_ms = models.IntegerField(default=0)
    idempotency_key = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    endpoint = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["idempotency_key", "endpoint"],
                name="unique_idempotency_per_endpoint",
                condition=models.Q(idempotency_key__isnull=False),
            ),
        ]

    def __str__(self):
        return f"[{self.status}] {self.tool_used} @ {self.created_at:%Y-%m-%d %H:%M}"
