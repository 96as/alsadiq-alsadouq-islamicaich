from django.db import models


# ============================================
# Choices
# ============================================

FLAG_TYPE_CHOICES = [
    ('inappropriate', 'Inappropriate Content'),
    ('harmful', 'Harmful Content'),
    ('sensitive', 'Sensitive Topic'),
    ('off_topic', 'Off Topic'),
]

ALERT_TYPE_CHOICES = [
    ('safety', 'Safety Concern'),
    ('mood', 'Mood Change'),
    ('milestone', 'Milestone'),
    ('session', 'Session Summary'),
]

# Flags created for no-parent-notify rules start their description with this
# exact prefix. Parent-facing code must never expose such a description.
NO_PARENT_NOTIFY_PREFIX = '[no-parent-notify] '
NEUTRAL_ALERT_DESCRIPTION = 'A conversation needs a gentle check-in.'


# ============================================
# Models
# ============================================

class SafetyFlag(models.Model):
    """Content safety flags.

    Extracted from MoralData.safety_filter_flag into its own model
    in the content_safety app where it belongs (proper separation of concerns).
    """
    message = models.ForeignKey(
        'conversation.Message',
        on_delete=models.CASCADE,
        related_name='safety_flags',
    )
    flag_type = models.CharField(max_length=50, choices=FLAG_TYPE_CHOICES)
    description = models.TextField(blank=True)
    is_blocked = models.BooleanField(default=False)
    flagged_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.flag_type}] Message {self.message_id}"


class Alert(models.Model):
    """Parent alerts triggered by sessions (schema.sql: Alerts).

    Notifies parents about safety concerns, mood changes,
    milestones, or session summaries.
    """
    session = models.ForeignKey(
        'conversation.Session',
        on_delete=models.CASCADE,
        related_name='alerts',
    )
    parent = models.ForeignKey(
        'authentication.ParentProfile',
        on_delete=models.CASCADE,
        related_name='alerts',
    )
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['session']),
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        return f"[{self.alert_type}] for {self.parent.name}"
