"""Child-facing gamification API views + parent quest verification."""
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import ParentChildLink
from authentication.permissions import IsChild, IsParent
from .models import Badge, ChildBadge, ChildQuestProgress
from .serializers import ChildBadgeSerializer, ChildLevelSerializer, ChildQuestSerializer
from .services import (
    _child_stat,
    complete_quest_progress,
    gamification_state,
)


class QuestListView(APIView):
    permission_classes = [IsAuthenticated, IsChild]

    def get(self, request):
        child = request.user.child_profile
        qs = (
            ChildQuestProgress.objects
            .filter(child=child)
            .select_related('quest', 'quest__moral_theme', 'quest__value')
            .order_by('-id')
        )
        return Response(ChildQuestSerializer(qs, many=True).data)


class QuestCompleteView(APIView):
    """Child marks a quest done. Behavior depends on quest verification:

    - self: completed immediately, points awarded, badges evaluated.
    - parent: moves to pending_verification (with optional proof_note)
      until a linked parent approves.
    - companion: rejected here — these are completed by Al-Sadiq during
      a conversation.
    """
    permission_classes = [IsAuthenticated, IsChild]

    def patch(self, request, progress_id):
        child = request.user.child_profile
        try:
            progress = ChildQuestProgress.objects.select_related(
                'quest', 'quest__moral_theme', 'quest__value',
            ).get(pk=progress_id, child=child)
        except ChildQuestProgress.DoesNotExist:
            return Response(
                {'detail': 'Quest not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if progress.status == 'completed':
            return Response(
                {'detail': 'Quest already completed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        method = progress.quest.verification_method

        if method == 'companion':
            return Response(
                {'detail': 'Finish this quest by talking it through with Al-Sadiq.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if method == 'parent':
            if progress.status == 'pending_verification':
                return Response(
                    {'detail': 'Already waiting for a parent to confirm.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            body = request.data
            proof_note = body.get('proof_note') if isinstance(body, dict) else None
            if not isinstance(body, dict) or not (proof_note is None or isinstance(proof_note, str)):
                return Response(
                    {'detail': 'proof_note must be text.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            progress.status = 'pending_verification'
            progress.proof_note = (proof_note or '')[:2000]
            if not progress.started_at:
                progress.started_at = timezone.now()
            progress.save(update_fields=['status', 'proof_note', 'started_at'])
            return Response({
                'quest': ChildQuestSerializer(progress).data,
                'points': None,
                'new_badges': [],
            })

        result = complete_quest_progress(progress, verified_by='child')
        if result['points'] is None:  # lost a race with a concurrent completion
            return Response(
                {'detail': 'Quest already completed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({
            'quest': ChildQuestSerializer(result['progress']).data,
            'points': result['points'],
            'new_badges': [
                {'id': b.id, 'name': b.name, 'icon': b.icon, 'category': b.category}
                for b in result['new_badges']
            ],
        })


class BadgeListView(APIView):
    permission_classes = [IsAuthenticated, IsChild]

    def get(self, request):
        child = request.user.child_profile
        earned_map = dict(
            ChildBadge.objects
            .filter(child=child)
            .values_list('badge_id', 'earned_at')
        )
        badges = Badge.objects.all().order_by('category', 'sort_order', 'name')
        stats_cache = {}
        result = []
        for b in badges:
            earned = b.id in earned_map
            row = {
                'id': b.id,
                'name': b.name,
                'description': b.description,
                'icon': b.icon,
                'category': b.category,
                'earned': earned,
                'earned_at': earned_map.get(b.id),
                'requirement_type': b.requirement_type,
                'requirement_value': b.requirement_value,
                'progress_current': None,
            }
            if not earned and b.requirement_type != 'manual':
                if b.requirement_type not in stats_cache:
                    stats_cache[b.requirement_type] = _child_stat(
                        child, b.requirement_type
                    )
                row['progress_current'] = min(
                    stats_cache[b.requirement_type], b.requirement_value
                )
            result.append(row)
        return Response(result)


class LevelView(APIView):
    permission_classes = [IsAuthenticated, IsChild]

    def get(self, request):
        child = request.user.child_profile
        data = gamification_state(child)
        return Response(ChildLevelSerializer(data).data)


# ============================================
# Parent quest verification
# ============================================

def _linked_child_or_none(parent, child_id):
    link = ParentChildLink.objects.filter(
        parent=parent, child_id=child_id, consent_status='approved',
    ).select_related('child').first()
    return link.child if link else None


class ParentChildQuestListView(APIView):
    """GET /api/gamification/parent/children/<child_id>/quests/

    Parent view of a linked child's quests; ?status=pending_verification
    narrows to ones awaiting approval.
    """
    permission_classes = [IsAuthenticated, IsParent]

    def get(self, request, child_id):
        child = _linked_child_or_none(request.user.parent_profile, child_id)
        if not child:
            return Response({'detail': 'Child not linked.'}, status=403)
        qs = (
            ChildQuestProgress.objects
            .filter(child=child)
            .select_related('quest', 'quest__moral_theme', 'quest__value')
            .order_by('-id')
        )
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return Response(ChildQuestSerializer(qs, many=True).data)


class ParentQuestVerifyView(APIView):
    """PATCH /api/gamification/parent/quests/<progress_id>/verify/

    Body: {"action": "approve" | "reject"}. Approving completes the quest
    (points + badges); rejecting sends it back to in_progress so the child
    can try again.
    """
    permission_classes = [IsAuthenticated, IsParent]

    def patch(self, request, progress_id):
        parent = request.user.parent_profile
        try:
            progress = ChildQuestProgress.objects.select_related(
                'quest', 'child',
            ).get(pk=progress_id)
        except ChildQuestProgress.DoesNotExist:
            return Response({'detail': 'Quest not found.'}, status=404)

        if not ParentChildLink.objects.filter(
            parent=parent, child=progress.child, consent_status='approved',
        ).exists():
            return Response({'detail': 'Child not linked.'}, status=403)

        if progress.status != 'pending_verification':
            return Response(
                {'detail': 'Quest is not awaiting verification.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        body = request.data
        action = body.get('action') if isinstance(body, dict) else None
        action = action.lower() if isinstance(action, str) else ''
        if action == 'approve':
            result = complete_quest_progress(progress, verified_by='parent')
            if result['points'] is None:  # lost a race with a concurrent completion
                return Response(
                    {'detail': 'Quest is not awaiting verification.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response({
                'quest': ChildQuestSerializer(result['progress']).data,
                'points': result['points'],
                'new_badges': [
                    {'id': b.id, 'name': b.name, 'icon': b.icon, 'category': b.category}
                    for b in result['new_badges']
                ],
            })
        if action == 'reject':
            # Conditional update: a reject that lands after an approve must not un-complete a paid quest.
            n = ChildQuestProgress.objects.filter(
                pk=progress.pk, status='pending_verification',
            ).update(status='in_progress')
            if n == 0:
                return Response(
                    {'detail': 'Quest is not awaiting verification.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            progress.status = 'in_progress'
            return Response({'quest': ChildQuestSerializer(progress).data})
        return Response(
            {'detail': "action must be 'approve' or 'reject'."},
            status=status.HTTP_400_BAD_REQUEST,
        )
