from django.db import models


# ============================================
# Models
# ============================================

class SessionReport(models.Model):
    """System-internal report generated after each session ends.

    Used by:
    - AI agent: to know where to continue from
    - Gamification: to decide quests and award badges
    - Content safety: to track patterns
    - WeeklySummary: aggregated for parents

    NOT sent directly to parents.
    """
    session = models.OneToOneField(
        'conversation.Session',
        on_delete=models.CASCADE,
        related_name='report',
    )
    # Legacy (plan s11 decision 8): the child's honesty is no longer graded. Never written
    # or read; kept only so no migration is needed. Use raw_llm_output['values_to_revisit'].
    honesty_score = models.FloatField(null=True, blank=True)
    insight_summary = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    raw_llm_output = models.JSONField(default=dict, blank=True)
    # Snapshots of the ContentItems served in the session, read from
    # ServedReference by the pipeline. Never written by the LLM.
    sources_used = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Report for Session {self.session_id}"


class ChildSessionMemory(models.Model):
    """Rolling summary of past sessions for one child (agent context)."""

    child = models.OneToOneField(
        "authentication.ChildProfile",
        on_delete=models.CASCADE,
        related_name="session_memory",
    )
    rolling_summary = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self):
        return f"Session memory for {self.child.nickname}"


class WeeklySummary(models.Model):
    """Parent-facing weekly summary.

    Aggregates one or more SessionReports into a summary
    that is sent to the parent. The parent FK is here because
    this is the parent-facing report.
    """
    child = models.ForeignKey(
        'authentication.ChildProfile',
        on_delete=models.CASCADE,
        related_name='weekly_summaries',
    )
    parent = models.ForeignKey(
        'authentication.ParentProfile',
        on_delete=models.CASCADE,
        related_name='weekly_summaries',
    )
    week_start = models.DateField()
    summary = models.TextField()
    suggested_topics = models.JSONField(default=list, blank=True)
    sessions = models.ManyToManyField(
        SessionReport, related_name='weekly_summaries', blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('child', 'parent', 'week_start')

    def __str__(self):
        return f"Week of {self.week_start} - {self.child.nickname}"
