from django.contrib.auth.models import User
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from .fields import OrderField

class Subject(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    
    class Meta:
        ordering = ['title']
        
    def __str__(self):
        return self.title
    
class Course(models.Model):
    owner = models.ForeignKey(
        User,
        related_name='courses_created',
        on_delete=models.CASCADE
    )
    subject = models.ForeignKey(
        Subject,
        related_name='courses',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    overview = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created']
        
    def __str__(self):
        return self.title
    
class Module(models.Model):
    course = models.ForeignKey(
        Course, related_name='modules',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = OrderField(blank=True, for_fields=['course'])
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f'{self.order}. {self.title}' # Создаем модель здесь.
    
class Content(models.Model):
    module = models.ForeignKey(
        Module,
        related_name='contents',
        on_delete=models.CASCADE
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={
            'model__in':('text', 'video', 'image', 'file')
        }
    )
    
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    order = OrderField(blank=True, for_fields=['module'])
    
    class Meta:
        ordering = ['order']

class ItemBase(models.Model):
    owner = models.ForeignKey(
        User,
        related_name='%(class)s_related',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
    
    def __str__(self):
        return self.title

class Text(ItemBase):
    content = models.TextField()


class TextFigure(models.Model):
    """Рисунок, встраиваемый в текстовый контент. В тексте: [рис. 1] или [рисунок 1]."""
    text = models.ForeignKey(
        Text,
        on_delete=models.CASCADE,
        related_name='figures'
    )
    key = models.CharField('Ключ (номер)', max_length=20, help_text='Число для вставки: в тексте пишите [рис. 1]')
    caption = models.CharField('Подпись', max_length=200, help_text='Например: Рисунок 1')
    image = models.ImageField('Изображение', upload_to='text_figures/')

    class Meta:
        ordering = ['key']
        unique_together = ['text', 'key']
        verbose_name = 'Рисунок в тексте'
        verbose_name_plural = 'Рисунки в тексте'

    def __str__(self):
        return f'{self.text.title} — {self.caption}'


class File(ItemBase):
    file = models.FileField(upload_to='files')
    
class Image(ItemBase):
    file = models.FileField(upload_to='images')
    
class Video(ItemBase):
    url = models.URLField()


class ModuleProgress(models.Model):
    """Пройденный модуль — студент отметил модуль как изученный."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='module_progress'
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='progress'
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']
        unique_together = ['user', 'module']
        verbose_name = 'Пройденный модуль'
        verbose_name_plural = 'Пройденные модули'

    def __str__(self):
        return f'{self.user.username} — {self.module.title}'


class Enrollment(models.Model):
    """Запись студента на курс."""
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('completed', 'Завершена'),
    ]
    user = models.ForeignKey(
        User,
        related_name='enrollments',
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course,
        related_name='enrollments',
        on_delete=models.CASCADE
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    class Meta:
        ordering = ['-enrolled_at']
        unique_together = ['user', 'course']

    def __str__(self):
        return f'{self.user.username} — {self.course.title}'


class Review(models.Model):
    """Отзыв о курсе."""
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    user = models.ForeignKey(
        User,
        related_name='reviews',
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(
        Course,
        related_name='reviews',
        on_delete=models.CASCADE
    )
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'course']

    def __str__(self):
        return f'{self.user.username}: {self.rating}★ — {self.course.title}'


class Profile(models.Model):
    """Профиль пользователя или преподавателя."""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone = models.CharField('Телефон', max_length=20, blank=True)
    photo = models.ImageField('Фото', upload_to='profiles/', blank=True, null=True)

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'Профиль {self.user.username}'


class ContactMessage(models.Model):
    """Обращение пользователя через форму в футере."""
    name = models.CharField('Имя', max_length=100)
    email = models.EmailField('Email')
    message = models.TextField('Сообщение')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Обращение'
        verbose_name_plural = 'Обращения'

    def __str__(self):
        return f'{self.name} ({self.email})'
