from django.contrib.auth.models import AbstractUser
from django.db import models


# ============================================
# Choices
# ============================================

GENDER_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
]

CHILD_LANGUAGE_PREF_CHOICES = [
    ('en', 'English'),
    ('ar', 'Arabic'),
]

CHILD_PROFILE_ICON_CHOICES = [
    ('sparkles', 'Sparkles'),
    ('star', 'Star'),
    ('heart', 'Heart'),
    ('smile', 'Smile'),
    ('cat', 'Cat'),
    ('rainbow', 'Rainbow'),
]

CONSENT_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('revoked', 'Revoked'),
]

EMOTION_CHOICES = [
    ('neutral', 'Neutral'),
    ('happy', 'Happy'),
    ('sad', 'Sad'),
    ('excited', 'Excited'),
    ('curious', 'Curious'),
    ('confused', 'Confused'),
]

LIP_SYNC_CHOICES = [
    ('idle', 'Idle'),
    ('speaking', 'Speaking'),
    ('listening', 'Listening'),
]


# ============================================
# Models
# ============================================

class User(AbstractUser):
    """Django's built-in auth extended with role flags."""
    is_parent = models.BooleanField(default=False)
    is_child = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(is_parent=True, is_child=True),
                name='user_not_both_parent_and_child',
            ),
        ]

    def __str__(self):
        return self.username


class ParentProfile(models.Model):
    """Parent-specific data (schema.sql: Parent).

    Authentication is handled by the linked User model.
    This model stores parent-specific profile information only.
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='parent_profile'
    )
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    birth_year = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return self.name


class ChildProfile(models.Model):
    """Child-specific data (schema.sql: Child).

    current_level is NOT stored here (3NF).
    It is computed dynamically from gamification.Points + Level.
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='child_profile'
    )
    nickname = models.CharField(max_length=50)
    gender = models.CharField(
        max_length=20, blank=True, choices=GENDER_CHOICES
    )
    birth_year = models.IntegerField(null=True, blank=True)
    avatar_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Updated when the child uses the app (authenticated API activity).',
    )
    language_preference = models.CharField(
        max_length=10,
        choices=CHILD_LANGUAGE_PREF_CHOICES,
        default='en',
    )
    profile_icon = models.CharField(
        max_length=20,
        choices=CHILD_PROFILE_ICON_CHOICES,
        default='sparkles',
    )

    class Meta:
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return self.nickname


class ParentChildLink(models.Model):
    """Parent-Child relationship (schema.sql: Linkage).

    Supports many-to-many: one parent can have multiple children,
    and one child can have multiple parents (guardians).
    """
    parent = models.ForeignKey(
        ParentProfile, on_delete=models.CASCADE, related_name='children'
    )
    child = models.ForeignKey(
        ChildProfile, on_delete=models.CASCADE, related_name='parents'
    )
    consent_status = models.CharField(
        max_length=50, default='pending', choices=CONSENT_CHOICES
    )
    date_linked = models.DateTimeField(auto_now_add=True)
    memory = models.TextField(blank=True)

    class Meta:
        unique_together = ('parent', 'child')
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['child']),
        ]

    def __str__(self):
        return f"{self.parent.name} → {self.child.nickname}"


class Avatar(models.Model):
    """Avatar state for a child (schema.sql: Avatar)."""
    child = models.ForeignKey(
        ChildProfile, on_delete=models.CASCADE, related_name='avatars'
    )
    emotion_state = models.CharField(
        max_length=50, default='neutral', choices=EMOTION_CHOICES
    )
    lip_sync_status = models.CharField(
        max_length=50, default='idle', choices=LIP_SYNC_CHOICES
    )

    class Meta:
        indexes = [
            models.Index(fields=['child']),
        ]

    def __str__(self):
        return f"{self.child.nickname} - {self.emotion_state}"
