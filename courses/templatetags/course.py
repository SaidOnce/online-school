import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def model_name(obj):
    try:
        return obj._meta.model_name
    except AttributeError:
        return None


@register.filter
def text_with_figures(text_obj):
    """
    Рендерит текст с вставками рисунков. В тексте: [рис. 1], [рисунок 1.1], [Рисунок 1].
    Заменяет на изображение с подписью в указанном месте.
    """
    if not text_obj or not hasattr(text_obj, 'content'):
        return ''
    content = text_obj.content or ''
    figures_list = list(text_obj.figures.all())
    if not figures_list:
        return content

    # Словарь по ключу (нормализуем: запятая -> точка) + fallback по подписи
    def norm_key(k):
        return str(k).strip().replace(',', '.')
    figures_by_key = {norm_key(f.key): f for f in figures_list}
    figures_by_key.update({str(f.key).strip(): f for f in figures_list})  # и без нормализации
    figures_by_caption = {f.caption.strip().lower(): f for f in figures_list if f.caption}

    def find_figure(key, caption_hint=None):
        """Ищем рисунок по ключу или по подписи."""
        fig = figures_by_key.get(key)
        if fig:
            return fig
        if caption_hint:
            return figures_by_caption.get(caption_hint.lower())
        return None

    # Паттерн: [рис. 1], [рисунок 1.1], [Рисунок 1], [drawing 1], [картинка 1.1]
    # Используем \s* перед ] на случай пробелов
    pattern = re.compile(
        r'\[(?:рис\.?|рисунок|drawing|figure|picture|картинка|изображение)\s*([\d.]+)\s*\]',
        re.IGNORECASE | re.UNICODE
    )
    parts = []
    last_end = 0
    for match in pattern.finditer(content):
        parts.append(content[last_end:match.start()])
        key = match.group(1).strip()
        full_match = match.group(0)  # например [Рисунок 1.1]
        fig = find_figure(key) or find_figure(key, f'Рисунок {key}')
        if fig and fig.image:
            try:
                html = f'<figure class="my-6"><img src="{fig.image.url}" alt="{fig.caption}" class="max-w-full rounded-lg mx-auto"><figcaption class="text-center text-gray-400 mt-2">{fig.caption}</figcaption></figure>'
                parts.append(html)
            except (ValueError, AttributeError):
                parts.append(f'<span class="text-amber-400 text-sm">[Изображение не загружено]</span>')
        else:
            parts.append(f'<span class="text-amber-400 text-sm" title="Добавьте рисунок при редактировании контента">[рисунок {key} — загрузите в разделе «Редактировать»]</span>')
        last_end = match.end()
    parts.append(content[last_end:])
    return mark_safe(''.join(parts))