from django.db import models


# ============================================
# Choices
# ============================================

SENDER_CHOICES = [
    ('child', 'Child'),
    ('system', 'System'),
    ('parent', 'Parent'),
]

INPUT_TYPE_CHOICES = [
    ('text', 'Text'),
    ('voice', 'Voice'),
]

MOOD_CHOICES = [
    ('happy', 'Happy'),
    ('sad', 'Sad'),
    ('anxious', 'Anxious'),
    ('calm', 'Calm'),
    ('excited', 'Excited'),
    ('neutral', 'Neutral'),
    ('confused', 'Confused'),
    ('angry', 'Angry'),
]

SESSION_STATUS_CHOICES = [
    ('active', 'Active'),
    ('ended', 'Ended'),
]


# ============================================
# Models
# ============================================

class Session(models.Model):
    """Conversation session between child and system.

    Duration is NOT stored (3NF) — computed from ended_at - started_at.
    """
    child = models.ForeignKey(
        'authentication.ChildProfile',
        on_delete=models.CASCADE,
        related_name='sessions',
    )
    livekit_room_name = models.CharField(max_length=100, unique=True, blank=True)
    status = models.CharField(
        max_length=10, choices=SESSION_STATUS_CHOICES, default='active'
    )
    mood_state = models.CharField(
        max_length=50, blank=True, choices=MOOD_CHOICES
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    @property
    def duration(self):
        """Compute duration instead of storing it (3NF compliance)."""
        if self.ended_at and self.started_at:
            return self.ended_at - self.started_at
        return None

    class Meta:
        indexes = [
            models.Index(fields=['child']),
            models.Index(fields=['started_at']),
        ]

    def __str__(self):
        return f"Session {self.pk} - {self.child.nickname}"


class Message(models.Model):
    """Single message in a session (schema.sql: Conversations).

    Replaces separate text_input/voice_input columns with a single
    content field + input_type enum (proper 1NF).
    """
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    input_type = models.CharField(
        max_length=10, choices=INPUT_TYPE_CHOICES, default='text'
    )
    language = models.CharField(max_length=20, default='en')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['session']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"[{self.sender}] {self.content[:50]}"


# Legacy (before hk/12g): TurnAudit.mode of a row that marked its session as "never tell a parent".
# Nothing writes it any more (every safety concern alerts the parent); reports and alerts still read
# it so sessions recorded before the change keep their neutral treatment.
QUIET_AUDIT_MODE = 'SAFETY_QUIET'


class TurnAudit(models.Model):
    """What the turn guard decided for one child turn. Never stores any text.

    Written fire-and-forget by the voice agent. Feeds the eval, the parent's
    "questions to discuss" list (never rows with safety=True) and the submission
    evidence. ``served_item_ids`` are ContentItem ids (no FK: items may be
    re-seeded, and this table must survive that).
    """
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name='turn_audits'
    )
    level = models.CharField(max_length=1, blank=True)
    mode = models.CharField(max_length=24)
    served_item_ids = models.JSONField(default=list, blank=True)
    safety = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['session', 'created_at']),
        ]

    def __str__(self):
        return f"TurnAudit {self.pk} session={self.session_id} {self.mode}"
