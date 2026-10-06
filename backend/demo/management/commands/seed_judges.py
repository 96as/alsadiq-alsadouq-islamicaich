"""Persistent judge accounts: judgeN (parent) with judgeN-ar and judgeN-en (children).

Not part of the demo pool: the pool only ever touches ``demo-`` usernames, so
leases, resets and demo cleanup never see these accounts. Session caps come from
JUDGE_DAILY_SESSIONS / JUDGE_SESSION_START_PER_HOUR (conversation.demo_guards).

Every run wipes and re-seeds each child's synthetic week (demo.services.seed_week),
so re-running is the reset. Passwords live only in --password-file (mode 600):
existing entries there are reused, missing ones are generated, and nothing secret
is ever printed. See docs/hackathon/JUDGE-ACCOUNTS.md.
"""
import os
import secrets
import tempfile

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from authentication.models import ChildProfile, ParentChildLink, ParentProfile
from demo import content, services
from gamification.services import evaluate_badges

User = get_user_model()

PARENT = 'judge{n}'
CHILD = 'judge{n}-{lang}'
EMAIL = '{username}@judges.invalid'
# No look-alikes (0/O, 1/l/I): judges type these by hand.
ALPHABET = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789'
MAX_JUDGES = 99  # demo.accounts._JUDGE_USERNAME allows judge1..judge99


def new_password():
    """16 characters in four groups, about 92 bits."""
    return '-'.join(''.join(secrets.choice(ALPHABET) for _ in range(4)) for _ in range(4))


def read_passwords(path):
    """username -> password from an earlier run's file ({} when there is none)."""
    try:
        with open(path, encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return {}
    found = {}
    for line in lines:
        parts = line.split()
        if len(parts) >= 2 and not line.startswith('#'):
            found[parts[0]] = parts[1]
    return found


def write_passwords(path, rows):
    """Write atomically, mode 600 from the first byte (mkstemp), then rename."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)), prefix='.judges-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write('# Al-Sadiq judge accounts. PRIVATE: give each judge only their own lines.\n')
            f.write(f'# Written {timezone.now():%Y-%m-%d %H:%M} UTC by manage.py seed_judges.\n')
            f.write('# username\tpassword\trole\n')
            for username, password, role in rows:
                f.write(f'{username}\t{password}\t{role}\n')
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _judge_user(username, role, fields, password):
    """Get or create one judge user, put its fields back and set its password.

    Refuses an existing account that is not ours (wrong role or no judge email),
    so seeding can never take over a real person's account.
    """
    user, created = User.objects.get_or_create(username=username, defaults={**fields, role: True})
    if not created and (not getattr(user, role) or user.email != fields['email']):
        raise CommandError(f'{username} exists and is not a judge account; refusing to take it over.')
    for key, value in fields.items():
        setattr(user, key, value)
    user.is_active = True
    user.set_password(password)
    user.save()
    return user


@transaction.atomic
def seed_judge(n, passwords):
    """Create or reset judge n and both children. Returns the users touched."""
    year = timezone.now().year
    username = PARENT.format(n=n)
    parent_user = _judge_user(
        username, 'is_parent',
        {'email': EMAIL.format(username=username), 'first_name': 'Judge', 'last_name': str(n)},
        passwords[username],
    )
    parent, _ = ParentProfile.objects.update_or_create(
        user=parent_user, defaults={'name': f'Judge {n}', 'phone': '', 'birth_year': None})

    users, kept = [parent_user], []
    for lang, name, age, gender, icon, theme_key in content.JUDGE_CHILDREN:
        username = CHILD.format(n=n, lang=lang)
        child_user = _judge_user(
            username, 'is_child',
            {'email': EMAIL.format(username=username), 'first_name': name, 'last_name': ''},
            passwords[username],
        )
        child, _ = ChildProfile.objects.update_or_create(
            user=child_user,
            defaults={
                'nickname': name, 'gender': gender, 'birth_year': year - age,
                'language_preference': lang, 'profile_icon': icon, 'avatar_visible': True,
                'last_seen_at': None,
            },
        )
        ParentChildLink.objects.filter(child=child).exclude(parent=parent).delete()
        link, _ = ParentChildLink.objects.update_or_create(
            parent=parent, child=child, defaults={'consent_status': 'approved'})
        services._wipe_child(child)
        services.seed_week(
            parent, child, link, name=name, age=age, gender=gender,
            theme=content.THEME_EN if theme_key == 'en' else content.THEMES[theme_key],
            room_prefix=f'judge-{n}-{lang}', rotate=n if lang == 'ar' else n + 3, lang=lang,
        )
        evaluate_badges(child)
        users.append(child_user)
        kept.append(child.pk)
    # Exactly these two children: drop any a judge added by hand.
    ParentChildLink.objects.filter(parent=parent).exclude(child__in=kept).delete()
    return users


class Command(BaseCommand):
    help = (
        'Create or reset the persistent judge accounts (judgeN + judgeN-ar + judgeN-en), each '
        'with a synthetic week of history. Idempotent: every run re-seeds the history. '
        'Passwords go only to --password-file (mode 600); nothing secret is printed.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=5, help='Number of judges (default 5).')
        parser.add_argument('--password-file', required=True,
                            help='Where to read/write the passwords. Keep it outside the repo.')
        parser.add_argument('--rotate-passwords', action='store_true',
                            help='New passwords for everyone, and sign out every judge session.')

    def handle(self, *args, **options):
        count, path = options['count'], options['password_file']
        if not 1 <= count <= MAX_JUDGES:
            raise CommandError(f'--count must be between 1 and {MAX_JUDGES}.')
        if not os.path.isdir(os.path.dirname(os.path.abspath(path))):
            raise CommandError('The folder for --password-file does not exist.')

        old = read_passwords(path)
        rows, passwords = [], {}
        for n in range(1, count + 1):
            for username, role in [(PARENT.format(n=n), 'parent')] + [
                (CHILD.format(n=n, lang=c[0]), f'child ({c[1]}, {c[2]}, {c[0]})')
                for c in content.JUDGE_CHILDREN
            ]:
                passwords[username] = (
                    None if options['rotate_passwords'] else old.get(username)) or new_password()
                rows.append((username, passwords[username], role))
        # A lower --count keeps the other judges' lines: those accounts still exist.
        rows += [(u, p, 'kept (above --count)') for u, p in old.items() if u not in passwords]
        # The file first: if seeding fails half way, the passwords already set are not lost.
        write_passwords(path, rows)

        for n in range(1, count + 1):
            users = seed_judge(n, passwords)
            if options['rotate_passwords']:
                services._blacklist_tokens(users)

        self.stdout.write(self.style.SUCCESS(
            f'Judge accounts ready: judge1..judge{count}, each with '
            f'{len(content.JUDGE_CHILDREN)} children. Passwords are in the password file (mode 600).'
        ))
