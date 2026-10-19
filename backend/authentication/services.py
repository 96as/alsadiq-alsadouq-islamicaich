import logging
import unicodedata

from django.db import transaction

from .models import User, ParentProfile, ChildProfile, ParentChildLink

logger = logging.getLogger(__name__)


def find_reset_user(email):
    """The parent a password-reset request for `email` goes to. One lookup for view and throttle."""
    return User.objects.filter(email__iexact=email, is_parent=True).order_by('pk').first()


def canonical_email(raw):
    """NFKC, strip, casefold: the form used to bucket an address no account matches."""
    return unicodedata.normalize('NFKC', raw).strip().casefold()


@transaction.atomic
def create_parent(validated_data):
    """Create a User (is_parent=True) + ParentProfile in one transaction."""
    user = User.objects.create_user(
        username=validated_data['username'],
        password=validated_data['password'],
        email=validated_data['email'],
        first_name=validated_data['first_name'],
        last_name=validated_data['last_name'],
        is_parent=True,
    )
    ParentProfile.objects.create(
        user=user,
        name=f"{validated_data['first_name']} {validated_data['last_name']}",
        phone=validated_data.get('phone', ''),
        birth_year=validated_data.get('birth_year'),
    )
    logger.info("Parent registered: user_id=%s", user.id)
    return user


@transaction.atomic
def create_child_for_parent(parent_profile, validated_data):
    """Create a User (is_child=True) + ChildProfile + approved ParentChildLink."""
    user = User.objects.create_user(
        username=validated_data['username'],
        password=validated_data['password'],
        is_child=True,
    )
    child_profile = ChildProfile.objects.create(
        user=user,
        nickname=validated_data['nickname'],
        gender=validated_data.get('gender', ''),
        birth_year=validated_data.get('birth_year'),
        language_preference=validated_data.get('language_preference', 'en'),
    )
    ParentChildLink.objects.create(
        parent=parent_profile,
        child=child_profile,
        consent_status='approved',
    )
    logger.info(
        "Child created: child_id=%s, by parent_id=%s",
        child_profile.id, parent_profile.id,
    )
    return child_profile
