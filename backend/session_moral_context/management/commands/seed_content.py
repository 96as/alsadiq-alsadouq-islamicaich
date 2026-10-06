"""
Seed the knowledge bank from content/values.json and content/items/*.json.

Usage:
    python manage.py seed_content [--dry-run] [--dir PATH]

Idempotent. Each item runs in its own savepoint, so one bad item never aborts
the rest. Format: see content/README.md.
"""
import json
from datetime import datetime
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, transaction
from django.utils import timezone

from gamification.backfill import backfill_quest_values
from session_moral_context.models import (
    DEFAULT_CONTENT_LEVEL, ContentItem, Value, ValueItem)
from session_moral_context.utils.review import STATUS_KEYS, item_hash, natural_key

DEFAULT_DIR = Path(__file__).resolve().parents[2] / 'content'
SKIP_FIELDS = {'id', 'search_text_norm', 'reviewed_by', 'reviewed_at'}
ITEM_KEYS = {
    f.name for f in ContentItem._meta.concrete_fields if f.name not in SKIP_FIELDS
} | {'values'}
FILE_KEYS = ITEM_KEYS | {'reviewed_by', 'reviewed_at', 'related'}
VALUE_KEYS = {f.name for f in Value._meta.concrete_fields if f.name != 'id'}


def err_text(e):
    return '; '.join(e.messages) if not hasattr(e, 'message_dict') else '; '.join(
        f"{k}: {' '.join(v)}" for k, v in e.message_dict.items())


class Command(BaseCommand):
    help = 'Seed Value and ContentItem rows from JSON files (idempotent).'

    def add_arguments(self, parser):
        parser.add_argument('--dir', default=str(DEFAULT_DIR))
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **opts):
        base = Path(opts['dir'])
        counts = dict(created=0, updated=0, unchanged=0, skipped_reviewed=0, reviewed=0)
        rejected = []
        self.notes = []
        rfile = base / 'reviewed.json'
        self.ledger = {e['key']: e for e in self.load(rfile)} if rfile.exists() else {}
        self.seen = {}
        self.pending_related = []
        with transaction.atomic():
            vfile = base / 'values.json'
            if vfile.exists():
                for i, data in enumerate(self.load(vfile)):
                    self.do_value(data, f'{vfile.name}:{i}', counts, rejected)
            for f in sorted((base / 'items').glob('*.json')):
                for i, data in enumerate(self.load(f)):
                    self.do_item(data, f'{f.name}:{i}', counts, rejected)
            self.do_related(rejected)
            for k in sorted(self.ledger):
                if ('item', k) not in self.seen:
                    self.notes.append(f'  UNKNOWN REVIEW KEY {k}')
            # Legacy quests created before the Values existed (see gamification 0005).
            quests_mapped = backfill_quest_values()
            if opts['dry_run']:
                transaction.set_rollback(True)

        self.stdout.write(
            f"{'[dry-run] ' if opts['dry_run'] else ''}created {counts['created']}, "
            f"updated {counts['updated']}, unchanged {counts['unchanged']}, "
            f"skipped (reviewed) {counts['skipped_reviewed']}, reviewed {counts['reviewed']}, "
            f"rejected {len(rejected)}, legacy quests mapped to values {quests_mapped}")
        for where, key, reason in rejected:
            self.stdout.write(f"  REJECTED {where} {key} - {reason}")
        for n in self.notes:
            self.stdout.write(n)

    def load(self, path):
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except ValueError as e:
            raise CommandError(f'{path}: invalid JSON ({e})')
        if not isinstance(data, list):
            raise CommandError(f'{path}: top level must be a list')
        return data

    def do_value(self, data, where, counts, rejected):
        key = data.get('slug', '?') if isinstance(data, dict) else '?'
        try:
            with transaction.atomic():
                if not isinstance(data, dict):
                    raise ValueError('item must be an object')
                self.check_seen(('value', key), where)
                unknown = set(data) - VALUE_KEYS
                if unknown:
                    raise ValueError(f'unknown keys: {sorted(unknown)}')
                obj = Value.objects.filter(slug=data.get('slug')).first() or Value()
                new = obj.pk is None
                before = {k: getattr(obj, k) for k in data}
                for k, v in data.items():
                    setattr(obj, k, v)
                obj.full_clean()
                if new:
                    obj.save()
                    counts['created'] += 1
                elif before != {k: getattr(obj, k) for k in data}:
                    obj.save()
                    counts['updated'] += 1
                else:
                    counts['unchanged'] += 1
        except (ValueError, ValidationError, DatabaseError) as e:
            rejected.append((where, key, err_text(e) if isinstance(e, ValidationError) else e))

    def do_item(self, data, where, counts, rejected):
        key = '?'
        try:
            with transaction.atomic():
                if not isinstance(data, dict):
                    raise ValueError('item must be an object')
                unknown = set(data) - FILE_KEYS
                if unknown:
                    raise ValueError(f'unknown keys: {sorted(unknown)}')
                holes = sorted(k for k, v in data.items() if '⟦' in json.dumps(v, ensure_ascii=False))
                if holes:  # extractor placeholders (e.g. ⟦VERSE_HOLE⟧) never reach the bank
                    raise ValueError(f'placeholder ⟦…⟧ in {holes}')
                lookup, key = natural_key(data)
                self.check_seen(('item', key), where)
                at = data.get('reviewed_at')
                if at is not None:
                    at = timezone.make_aware(datetime.strptime(str(at), '%Y-%m-%d'))
                slugs = data.get('values', [])
                if not isinstance(slugs, list) or len(set(slugs)) != len(slugs):
                    raise ValueError('values must be a list without duplicate slugs')
                vals = list(Value.objects.filter(slug__in=slugs))
                missing = set(slugs) - {v.slug for v in vals}
                if missing:
                    raise ValueError(f'unknown value slug(s): {sorted(missing)}')
                by_slug = {v.slug: v for v in vals}

                entry = self.ledger.get(key)
                fresh = bool(entry) and entry.get('sha256') == item_hash(data)
                says = data.get('verification_status') == 'reviewed'
                if says and not fresh:
                    self.notes.append(
                        f'  STALE REVIEW {key} - file says reviewed but content changed '
                        'since review (or no ledger entry)')
                elif fresh and not says:
                    self.notes.append(
                        f'  NOTE {key} reviewed in ledger; run mark_reviewed to write it into the file')

                obj = ContentItem.objects.filter(**lookup).first()
                fields = {k: v for k, v in data.items()
                          if k not in STATUS_KEYS and k not in ('values', 'related')}
                if not fields.get('content_level'):  # default after hashing: hash is file-only
                    fields['content_level'] = DEFAULT_CONTENT_LEVEL.get(data['type'], 'A')
                labels = data.get('related', [])
                if not isinstance(labels, list) or not all(isinstance(x, str) for x in labels):
                    raise ValueError('related must be a list of strings')
                if obj and obj.verification_status == 'reviewed' and not fresh and not (
                        any(getattr(obj, k) != v for k, v in fields.items())
                        or [v.slug for v in obj.values.order_by('valueitem__order')] != slugs
                        or sorted(self.label(o) for o in obj.related.all()) != sorted(labels)):
                    counts['skipped_reviewed'] += 1  # content unchanged: keep DB review
                    return
                new = obj is None
                obj = obj or ContentItem()
                before = None if new else self.snapshot(obj)
                for k, v in fields.items():
                    setattr(obj, k, v)
                if fresh:
                    by = data.get('reviewed_by') or entry.get('by', '')
                    users = get_user_model().objects
                    obj.verification_status = 'reviewed'
                    obj.reviewed_at = at or timezone.make_aware(
                        datetime.strptime(entry['at'], '%Y-%m-%d'))
                    obj.reviewed_by = users.filter(username=by).first() or next(
                        (u for u in users.all() if u.get_full_name() == by), None)
                else:  # a review that is not proven by the ledger is never stored
                    status = data.get('verification_status', obj.verification_status)
                    obj.verification_status = 'seeded' if status == 'reviewed' else status
                    obj.reviewed_by = obj.reviewed_at = None
                obj.full_clean()
                obj.save()
                obj.valueitem_set.all().delete()
                ValueItem.objects.bulk_create(
                    ValueItem(value=by_slug[s], item=obj, order=n) for n, s in enumerate(slugs))
                obj.save()  # again, so search_text_norm includes value keywords
                self.pending_related.append((where, key, labels))  # only after a successful save
                if fresh:
                    counts['reviewed'] += 1
                if new:
                    counts['created'] += 1
                elif before != self.snapshot(obj):
                    counts['updated'] += 1
                else:
                    counts['unchanged'] += 1
        except (ValueError, ValidationError, DatabaseError) as e:
            rejected.append((where, key, err_text(e) if isinstance(e, ValidationError) else e))

    @staticmethod
    def label(o):
        return natural_key({f: getattr(o, f) for f in (
            'type', 'surah', 'ayah', 'book', 'number', 'source_url')})[1]

    def do_related(self, rejected):
        """Second pass: resolve natural-key labels (e.g. verse:2:153) to rows."""
        index = {}
        for o in ContentItem.objects.all():
            try:
                index[natural_key(
                    {f: getattr(o, f) for f in ('type', 'surah', 'ayah', 'book', 'number', 'source_url')}
                )[1]] = o
            except ValueError:
                pass
        for where, key, labels in self.pending_related:
            obj = index.get(key)
            if obj is None:
                continue
            unknown = [x for x in labels if x not in index]
            if unknown:
                rejected.append((where, key, f'related: unknown label(s) {unknown}'))
                continue
            obj.related.set([index[x] for x in labels])

    def check_seen(self, k, where):
        if k in self.seen:
            raise ValueError(f'duplicate natural key, first at {self.seen[k]}')
        self.seen[k] = where

    @staticmethod
    def snapshot(obj):
        return (
            [getattr(obj, k) for k in sorted(ITEM_KEYS - {'values'})],
            obj.search_text_norm,
            list(obj.valueitem_set.values_list('value__slug', flat=True)),
        )
