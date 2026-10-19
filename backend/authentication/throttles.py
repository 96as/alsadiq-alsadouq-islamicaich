"""Per-target-email throttle for password-reset requests."""
import hashlib
import hmac

from django.conf import settings

from rest_framework.throttling import SimpleRateThrottle

from config.throttling import SharedCacheThrottleMixin

from .services import canonical_email, find_reset_user


class PasswordResetEmailThrottle(SharedCacheThrottleMixin, SimpleRateThrottle):
    """At most 3 reset emails per hour to one account, whatever IP asks.

    The per-IP throttle alone lets a script that rotates IPs mail-bomb a parent. The bucket is
    chosen with the same lookup the view uses (find_reset_user), so every spelling that reaches
    one account shares one bucket, keyed on the account pk. An address no account matches is
    keyed on its NFKC/casefolded form. Either way the key is an HMAC-SHA256 under SECRET_KEY: no
    email or pk lands in Redis or a log, and it cannot be matched offline from a Redis dump. It
    counts whether or not the account exists, so a 429 reveals nothing.
    """
    scope = 'password_reset_email'

    def get_cache_key(self, request, view):
        data = request.data
        email = data.get('email') if hasattr(data, 'get') else None
        if not isinstance(email, str) or not email.strip():
            return None  # the serializer will answer 400
        canon = canonical_email(email)
        user = find_reset_user(email.strip()) or find_reset_user(canon)
        raw = f'user:{user.pk}' if user else f'email:{canon}'
        ident = hmac.new(settings.SECRET_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()
        return self.cache_format % {'scope': self.scope, 'ident': ident}
