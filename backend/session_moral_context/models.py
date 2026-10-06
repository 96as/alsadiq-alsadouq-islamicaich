from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from .utils.arabic import normalize_ar


# ============================================
# Choices
# ============================================

REFERENCE_TYPE_CHOICES = [
    ('hadith', 'Hadith'),
    ('quran', 'Quran'),
]


# ============================================
# Models
# ============================================

class MoralTheme(models.Model):
    """Moral theme definitions.

    Normalized from MoralData.moral_focus — avoids string
    duplication when the same theme appears across messages.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class IslamicReference(models.Model):
    """Hadith and Quran reference catalog.

    Normalized from MoralData.hadith_reference / quran_reference —
    each reference is stored once and linked via M2M to avoid
    duplication (2NF compliance).
    """
    reference_type = models.CharField(
        max_length=10, choices=REFERENCE_TYPE_CHOICES
    )
    text = models.TextField()
    source = models.CharField(
        max_length=255, blank=True,
        help_text='e.g. "Sahih Bukhari", "Surah Al-Baqarah 2:177"'
    )
    themes = models.ManyToManyField(
        MoralTheme, blank=True, related_name='references',
        help_text='Moral themes this reference addresses'
    )
    is_verified = models.BooleanField(
        default=False,
        help_text='Only verified references are served to the agent'
    )

    class Meta:
        unique_together = ('reference_type', 'text')

    def __str__(self):
        return f"[{self.reference_type}] {self.text[:60]}"


class MoralContext(models.Model):
    """Moral context for a message (schema.sql: MoralData — normalized).

    Links a message to its moral themes and Islamic references
    using M2M relationships instead of VARCHAR fields (3NF).
    """
    message = models.ForeignKey(
        'conversation.Message',
        on_delete=models.CASCADE,
        related_name='moral_contexts',
    )
    themes = models.ManyToManyField(
        MoralTheme, blank=True, related_name='contexts'
    )
    references = models.ManyToManyField(
        IslamicReference, blank=True, related_name='contexts'
    )
    story_source = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"MoralContext for Message {self.message_id}"


# ============================================
# Knowledge bank (task 01)
# ============================================

ITEM_TYPE_CHOICES = [
    ('verse', 'Verse'), ('hadith', 'Hadith'), ('tafsir', 'Tafsir'),
    ('aqidah', 'Aqidah'), ('fiqh', 'Fiqh'), ('sirah', 'Sirah'),
    ('faq', 'FAQ'), ('term', 'Term'), ('story', 'Story'),
]
AGE_BAND_CHOICES = [('all', 'All'), ('6-9', '6-9'), ('10-13', '10-13')]
SOURCE_SITE_CHOICES = [
    ('quranpedia.net', 'quranpedia.net'),
    ('qurancomplex.gov.sa', 'qurancomplex.gov.sa'),
    ('dorar.net', 'dorar.net'),
    ('shamela.ws', 'shamela.ws'),
    ('dawa.center', 'dawa.center'),
    ('islamic-content.com', 'islamic-content.com'),
    ('hadeethenc.com', 'hadeethenc.com'),
    ('quranenc.com', 'quranenc.com'),
    ('islamenc.com', 'islamenc.com'),
    ('terminologyenc.com', 'terminologyenc.com'),
    ('mp3quran.net', 'mp3quran.net'),
]
CONTENT_LEVEL_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C')]
DEFAULT_CONTENT_LEVEL = {
    'verse': 'A', 'hadith': 'A', 'term': 'A', 'story': 'A', 'sirah': 'A',
    'aqidah': 'A', 'tafsir': 'B', 'faq': 'B', 'fiqh': 'B',
}
VERIFICATION_CHOICES = [
    ('unverified', 'Unverified'), ('seeded', 'Seeded'), ('reviewed', 'Reviewed'),
]
VERSE_SITES = ('quranpedia.net', 'qurancomplex.gov.sa')
# add hadeethenc.com only after organiser approval, plan §12 Q1
HADITH_SITES = ('dorar.net', 'shamela.ws')
# Selectable but rejected as source_site for every type until approved.
PENDING_APPROVAL_SITES = (
    'hadeethenc.com', 'quranenc.com', 'islamenc.com', 'terminologyenc.com')
# Allowed source_site per type for seeded/reviewed items (plan §8).
ALLOWED_SITES = {
    'verse': VERSE_SITES,
    'hadith': HADITH_SITES,
    'tafsir': ('dorar.net', 'quranpedia.net', 'shamela.ws'),
    'aqidah': ('dorar.net', 'shamela.ws'),
    'fiqh': ('dorar.net', 'shamela.ws'),
    'sirah': ('dorar.net', 'shamela.ws'),
    'faq': ('dawa.center',),
    'term': ('islamic-content.com',),
    'story': ('quranpedia.net',),
}
HADITH_REQUIRED_GRADE = 'صحيح'
_GRADE_STRIP = ' \t\r\n[](){}<>«»\u200f\u200e'


def clean_grade(grade):
    return (grade or '').strip(_GRADE_STRIP)


class Value(models.Model):
    slug = models.SlugField(unique=True)
    name_ar = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    keywords_ar = models.JSONField(default=list, blank=True)
    keywords_en = models.JSONField(default=list, blank=True)
    child_description_ar = models.TextField(blank=True)
    child_description_en = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'slug']

    def __str__(self):
        return self.slug

    def clean(self):
        errors = {}
        for f in ('keywords_ar', 'keywords_en'):
            v = getattr(self, f)
            if not isinstance(v, list) or not all(isinstance(k, str) for k in v):
                errors[f] = 'Must be a list of strings.'
        if errors:
            raise ValidationError(errors)


class ContentItemQuerySet(models.QuerySet):
    def servable(self):
        """Items the agent may serve (plan §8): verses that are seeded or
        reviewed; every other type reviewed only; hadith also graded sahih."""
        return self.filter(
            Q(type='verse', verification_status__in=['seeded', 'reviewed'])
            | (~Q(type='verse') & ~Q(type='hadith') & Q(verification_status='reviewed'))
            | Q(type='hadith', verification_status='reviewed', grade=HADITH_REQUIRED_GRADE)
        )


class ContentItem(models.Model):
    type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES)
    title_ar = models.CharField(max_length=200, blank=True)
    title_en = models.CharField(max_length=200, blank=True)
    keywords_ar = models.JSONField(default=list, blank=True)
    keywords_en = models.JSONField(default=list, blank=True)
    arabic_text = models.TextField(
        blank=True,
        help_text='Verses: exact Uthmani text from an approved source; never hand-typed')
    arabic_text_search = models.TextField(
        blank=True, help_text='Verses: plain-script text used only for search')
    text_edition = models.CharField(max_length=200, blank=True)
    english_text = models.TextField(blank=True)
    child_explanation_ar = models.TextField(blank=True)
    child_explanation_en = models.TextField(blank=True)
    child_explanation_older_ar = models.TextField(
        blank=True, help_text='Deeper explanation for ages 10-13')
    child_explanation_older_en = models.TextField(blank=True)
    girls_note_ar = models.TextField(
        blank=True, help_text='Extra line shown only to girls (e.g. modesty)')
    girls_note_en = models.TextField(blank=True)
    age_band = models.CharField(max_length=5, choices=AGE_BAND_CHOICES, default='all')
    content_level = models.CharField(
        max_length=1, choices=CONTENT_LEVEL_CHOICES, blank=True,
        help_text='A/B/C; blank is filled per type by seed_content')
    disagreement_note_ar = models.TextField(blank=True)
    disagreement_note_en = models.TextField(blank=True)
    related = models.ManyToManyField(
        'self', symmetrical=False, blank=True, related_name='cited_by')
    search_text_norm = models.TextField(blank=True, editable=False)
    # verse
    surah = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(114)])
    ayah = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)])
    audio_url = models.URLField(max_length=500, blank=True)
    # hadith
    book = models.CharField(max_length=100, blank=True)
    number = models.CharField(max_length=30, blank=True)
    narrator = models.CharField(max_length=200, blank=True)
    grade = models.CharField(max_length=100, blank=True)
    grader = models.CharField(max_length=100, blank=True)
    # provenance
    translation_name = models.CharField(max_length=200, blank=True)
    source_site = models.CharField(
        max_length=30, choices=SOURCE_SITE_CHOICES, blank=True)
    source_url = models.URLField(max_length=500, blank=True)
    translation_source_url = models.URLField(max_length=500, blank=True)
    verification_status = models.CharField(
        max_length=10, choices=VERIFICATION_CHOICES, default='unverified')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    values = models.ManyToManyField(
        Value, through='ValueItem', blank=True, related_name='items')

    objects = ContentItemQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['type', 'surah', 'ayah'], condition=Q(type='verse'),
                name='uniq_verse_surah_ayah'),
            models.UniqueConstraint(
                fields=['type', 'book', 'number'], condition=Q(type='hadith') & ~Q(book='') & ~Q(number=''),
                name='uniq_hadith_book_number'),
        ]

    def __str__(self):
        return f"[{self.type}] {(self.english_text or self.arabic_text)[:60]}"

    def clean(self):
        errors = {}
        if self.type == 'hadith':
            self.grade = clean_grade(self.grade)
        for f in ('keywords_ar', 'keywords_en'):
            v = getattr(self, f)
            if not isinstance(v, list) or not all(isinstance(k, str) for k in v):
                errors[f] = 'Must be a list of strings.'
        if self.verification_status != 'unverified':
            if not self.source_site:
                errors['source_site'] = 'Required unless unverified.'
            if not self.source_url:
                errors['source_url'] = 'Required unless unverified.'
            if self.type == 'hadith':
                for f in ('book', 'number', 'grade', 'grader'):
                    if not getattr(self, f):
                        errors[f] = 'Required for a seeded/reviewed hadith.'
                if self.grade and self.grade != HADITH_REQUIRED_GRADE:
                    errors['grade'] = 'Only hadith graded sahih may be seeded.'
            if self.type == 'verse':
                for f in ('surah', 'ayah', 'arabic_text'):
                    if not getattr(self, f):
                        errors[f] = 'Required for a seeded/reviewed verse.'
            if self.source_site:
                allowed = ALLOWED_SITES.get(self.type, ())
                if self.source_site in PENDING_APPROVAL_SITES:
                    errors['source_site'] = f'{self.source_site} is not yet approved as a source.'
                elif self.source_site not in allowed:
                    errors['source_site'] = (
                        f'{self.type} must come from: {", ".join(allowed)}.')
            if self.type == 'story':
                if self.arabic_text:
                    errors['arabic_text'] = 'Stories must not carry arabic_text.'
            elif self.type != 'verse' and not self.arabic_text:
                errors['arabic_text'] = 'Required for a seeded/reviewed item.'
            if self.english_text and not self.translation_name:
                errors['translation_name'] = 'Required when english_text is set.'
            if self.content_level == 'C' and not (
                    self.disagreement_note_ar or self.disagreement_note_en):
                errors['disagreement_note_ar'] = 'Level C needs a disagreement note.'
        if self.source_url and self.source_site and 'source_url' not in errors:
            host = urlparse(self.source_url).hostname or ''
            if host != self.source_site and not host.endswith('.' + self.source_site):
                errors['source_url'] = 'URL host must match source_site.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        ar = self.arabic_text_search if self.type == 'verse' and self.arabic_text_search \
            else self.arabic_text
        kw_ar = self.keywords_ar if isinstance(self.keywords_ar, list) else []
        kw_en = self.keywords_en if isinstance(self.keywords_en, list) else []
        parts = [normalize_ar(ar), self.english_text,
                 normalize_ar(self.title_ar), self.title_en,
                 *[normalize_ar(k) for k in kw_ar], *kw_en,
                 normalize_ar(self.child_explanation_ar), self.child_explanation_en,
                 normalize_ar(self.child_explanation_older_ar), self.child_explanation_older_en,
                 normalize_ar(self.girls_note_ar), self.girls_note_en]
        if self.pk:
            for v in self.values.all():
                parts += [normalize_ar(k) for k in v.keywords_ar] + list(v.keywords_en)
        self.search_text_norm = ' '.join(p for p in parts if p).lower()
        super().save(*args, **kwargs)


class ValueItem(models.Model):
    value = models.ForeignKey(Value, on_delete=models.CASCADE)
    item = models.ForeignKey(ContentItem, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ('value', 'item')


class ServedReference(models.Model):
    """Hangs off the session, so it survives message cleanup."""
    session = models.ForeignKey(
        'conversation.Session', on_delete=models.CASCADE,
        related_name='served_references')
    item = models.ForeignKey(
        ContentItem, on_delete=models.CASCADE, related_name='served')
    served_at = models.DateTimeField(auto_now_add=True)
    via = models.CharField(
        max_length=10, choices=[('inject', 'Inject'), ('tool', 'Tool')])
