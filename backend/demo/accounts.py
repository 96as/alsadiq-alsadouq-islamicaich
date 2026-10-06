"""Who is a demo account. No model imports, so any app can use this safely.

The demo pool owns every username that starts with ``demo-``, and the judge
accounts every one that starts with ``judge``. Registration and child creation
refuse both prefixes, so only ``seed_demo`` / ``seed_judges`` can make one: a
visitor can never end up holding a real family's account, and nobody can sign
up as a "judge" to get the judges' session caps.
"""
import re

from rest_framework.permissions import SAFE_METHODS, BasePermission

RESERVED_PREFIXES = ('demo-', 'judge')
_DEMO_USERNAME = re.compile(r'^demo-(?:child|parent)-([1-9][0-9]{0,2})$')
# Judge accounts (seed_judges): parent judgeN, children judgeN-ar and judgeN-en.
_JUDGE_USERNAME = re.compile(r'^judge([1-9][0-9]?)(?:-(ar|en))?$')


def demo_slot(username):
    """'demo-child-3' or 'demo-parent-3' -> 3, anything else -> None."""
    match = _DEMO_USERNAME.match(username or '')
    return int(match.group(1)) if match else None


def is_demo_user(user):
    return demo_slot(getattr(user, 'username', '')) is not None


def is_judge_user(user):
    """A persistent judge account: own session caps, never part of the demo pool.

    The marker email (set only by seed_judges) also guards against a judgeN
    username registered before the prefix was reserved.
    """
    return bool(_JUDGE_USERNAME.match(getattr(user, 'username', '') or '')) and (
        getattr(user, 'email', '') or '').endswith('@judges.invalid')


def is_reserved_username(username):
    return (username or '').strip().lower().startswith(RESERVED_PREFIXES)


class NotDemoAccount(BasePermission):
    """Read-only for demo accounts: they may look, but not change the account.

    Stops a visitor from giving a shared demo child a password (a way back in
    after the lease ends) or from adding children that the next visitor sees.
    """

    message = 'Demo accounts cannot change this.'

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or not is_demo_user(request.user)
