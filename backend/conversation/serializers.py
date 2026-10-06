from rest_framework import serializers

from .models import Message, Session


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'sender', 'content', 'input_type', 'language', 'created_at']
        read_only_fields = fields


class ParentSessionSummarySerializer(serializers.ModelSerializer):
    """Session row for parent-facing conversation summary."""

    message_count = serializers.SerializerMethodField()
    last_message_at = serializers.SerializerMethodField()
    preview = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = [
            'id',
            'started_at',
            'ended_at',
            'status',
            'mood_state',
            'message_count',
            'last_message_at',
            'preview',
        ]

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message_at(self, obj):
        last = obj.messages.order_by('-created_at').first()
        return last.created_at if last else None

    def get_preview(self, obj):
        # Privacy (r5 H6): parents must not see raw child message text.
        # Field kept for frontend compatibility; returns a neutral value.
        return ''
