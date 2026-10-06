from django.db import models


# ============================================
# Choices
# ============================================

QUEST_STATUS_CHOICES = [
    ('not_started', 'Not Started'),
    ('in_progress', 'In Progress'),
    ('pending_verification', 'Pending Verification'),
    ('completed', 'Completed'),
]

QUEST_TYPE_CHOICES = [
    # Completed during a chat with the companion; the companion marks it done.
    ('conversation', 'Conversation'),
    # Done in the real world; verified by a parent (or self-reported).
    ('real_world', 'Real World'),
    # In-app reflection (e.g. think/journal then tell the companion).
    ('reflection', 'Reflection'),
]

QUEST_VERIFICATION_CHOICES = [
    ('self', 'Self-reported'),
    ('companion', 'Companion-verified'),
    ('parent', 'Parent-verified'),
]

BADGE_CATEGORY_CHOICES = [
    ('streak', 'Streak'),
    ('values', 'Values'),
    ('quest', 'Quest'),
    ('level', 'Level'),
    ('conversation', 'Conversation'),
    ('special', 'Special'),
]

BADGE_REQUIREMENT_CHOICES = [
    ('streak_days', 'Streak of N days'),
    ('quests_completed', 'N quests completed'),
    ('level_reached', 'Level N reached'),
    ('values_practised', 'N distinct values practised'),
    ('sessions_count', 'N sessions held'),
    ('points_total', 'N total points'),
    ('manual', 'Manually awarded'),
]

POINTS_SOURCE_CHOICES = [
    ('conversation', 'Conversation'),
    ('quest', 'Quest'),
    ('streak', 'Streak'),
    ('badge', 'Badge'),
    ('adjustment', 'Adjustment'),
]


# ============================================
# Models
# ============================================

class Level(models.Model):
    """Level definitions with point thresholds.

    A child's current level is computed dynamically from their
    total points (see Points.current_level property).
    """
    number = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=50)
    required_points = models.PositiveIntegerField()

    class Meta:
        ordering = ['number']

    def __str__(self):
        return f"Level {self.number}: {self.name}"


class Points(models.Model):
    """Child's total points (1:1 per child).

    current_level is computed here as a property (3NF compliance),
    not stored in ChildProfile.
    """
    child = models.OneToOneField(
        'authentication.ChildProfile',
        on_delete=models.CASCADE,
        related_name='points',
    )
    total = models.PositiveIntegerField(default=0)

    @property
    def current_level(self):
        """Compute current level from total points (3NF — no stored value)."""
        return Level.objects.filter(
            required_points__lte=self.total
        ).order_by('-required_points').first()

    class Meta:
        verbose_name_plural = 'Points'

    def __str__(self):
        return f"{self.child.nickname}: {self.total} points"


class PointsEvent(models.Model):
    """Audit ledger of every point change (Points.total stays the aggregate).

    Lets the conversation agent award/deduct in real time, gives parents a
    transparent activity feed, and makes level changes explainable.
    """
    child = models.ForeignKey(
        'authentication.ChildProfile',
        on_delete=models.CASCADE,
        related_name='points_events',
    )
    delta = models.IntegerField()
    reason = models.CharField(max_length=255, blank=True)
    source = models.CharField(
        max_length=20, choices=POINTS_SOURCE_CHOICES, default='adjustment'
    )
    session = models.ForeignKey(
        'conversation.Session',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='points_events',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['child', 'created_at']),
        ]

    def __str__(self):
        sign = '+' if self.delta >= 0 else ''
        return f"{self.child.nickname}: {sign}{self.delta} ({self.source})"


class ChildStreak(models.Model):
    """Consecutive-day session streak (1:1 per child)."""
    child = models.OneToOneField(
        'authentication.ChildProfile',
        on_delete=models.CASCADE,
        related_name='streak',
    )
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.child.nickname}: {self.current_streak} day streak"


class Badge(models.Model):
    """Badge definitions (normalized from Gamification.badge_awarded).

    category groups badges in the UI; requirement_type/value let the
    badge engine (services.evaluate_badges) auto-award them.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=255, blank=True)
    category = models.CharField(
        max_length=20, choices=BADGE_CATEGORY_CHOICES, default='special'
    )
    requirement_type = models.CharField(
        max_length=30, choices=BADGE_REQUIREMENT_CHOICES, default='manual'
    )
    requirement_value = models.PositiveIntegerField(default=0)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['category', 'sort_order', 'name']

    def __str__(self):
        return self.name


class ChildBadge(models.Model):
    """Tracks which child earned which badge and when.

    Junction table for the M2M relationship between
    ChildProfile and Badge (proper 3NF).
    """
    child = models.ForeignKey(
        'authentication.ChildProfile',
        on_delete=models.CASCADE,
        related_name='badges',
    )
    badge = models.ForeignKey(
        Badge, on_delete=models.CASCADE, related_name='awarded_to'
    )
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('child', 'badge')
        indexes = [
            models.Index(fields=['child']),
        ]

    def __str__(self):
        return f"{self.child.nickname} earned {self.badge.name}"


class Quest(models.Model):
    """Quest definitions (normalized from Gamification.quest_id).

    Each quest may optionally link to a bank Value (``value``) for the
    "values practised" badge track. ``moral_theme`` is the legacy theme FK,
    kept until the MoralTheme path is retired. quest_type drives how the
    quest is completed and verification_method who confirms it.
    """
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    reward_points = models.PositiveIntegerField(default=0)
    quest_type = models.CharField(
        max_length=20, choices=QUEST_TYPE_CHOICES, default='real_world'
    )
    verification_method = models.CharField(
        max_length=20, choices=QUEST_VERIFICATION_CHOICES, default='self'
    )
    moral_theme = models.ForeignKey(
        'session_moral_context.MoralTheme',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quests',
    )
    value = models.ForeignKey(
        'session_moral_context.Value',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quests',
    )
    session_report = models.ForeignKey(
        'reporting.SessionReport',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_quests',
    )
    is_ai_generated = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class ChildQuestProgress(models.Model):
    """Child's progress on a specific quest.

    Separated from Quest definition to maintain 3NF —
    quest data vs. progress data are independent concerns.
    """
    child = models.ForeignKey(
        'authentication.ChildProfile',
        on_delete=models.CASCADE,
        related_name='quest_progress',
    )
    quest = models.ForeignKey(
        Quest, on_delete=models.CASCADE, related_name='progress'
    )
    status = models.CharField(
        max_length=25, choices=QUEST_STATUS_CHOICES, default='not_started'
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    # What the child says they did (real-world quests awaiting parent review).
    proof_note = models.TextField(blank=True)
    # 'child' | 'companion' | 'parent' — who confirmed completion.
    verified_by = models.CharField(max_length=20, blank=True)

    class Meta:
        unique_together = ('child', 'quest')
        verbose_name_plural = 'Child quest progress'
        indexes = [
            models.Index(fields=['child']),
        ]

    def __str__(self):
        return f"{self.child.nickname} - {self.quest.title}: {self.status}"
