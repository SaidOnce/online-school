"""
Проверка рисунков в текстах: python manage.py check_figures
"""
from django.core.management.base import BaseCommand
from courses.models import Text, TextFigure, Content
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Проверяет, какие тексты имеют рисунки и где они привязаны'

    def handle(self, *args, **options):
        text_ct = ContentType.objects.get(app_label='courses', model='text')
        contents = Content.objects.filter(content_type=text_ct).select_related('module', 'module__course')
        for c in contents:
            try:
                text = Text.objects.get(pk=c.object_id)
                figures = list(text.figures.all())
                self.stdout.write(f'\nТекст ID={text.id} "{text.title[:50]}..."')
                self.stdout.write(f'  Курс: {c.module.course.title}')
                self.stdout.write(f'  Content object_id={c.object_id}')
                self.stdout.write(f'  Рисунков: {len(figures)}')
                for f in figures:
                    has_img = bool(f.image)
                    self.stdout.write(f'    - key={f.key!r} caption={f.caption!r} image={"да" if has_img else "НЕТ"}')
                if '[рисунок' in (text.content or '') or '[рис.' in (text.content or ''):
                    self.stdout.write(self.style.WARNING(f'  В тексте есть плейсхолдер, но рисунков: {len(figures)}'))
            except Text.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Content {c.id}: Text {c.object_id} не найден!'))
