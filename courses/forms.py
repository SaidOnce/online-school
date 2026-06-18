from django.forms.models import inlineformset_factory
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Course, Module, Subject, Review, ContactMessage, Profile, Text, TextFigure

INPUT_CLASS = 'w-full px-4 py-2.5 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent'


class SignUpForm(UserCreationForm):
    """Простая регистрация: логин и пароль."""

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': INPUT_CLASS, 'autocomplete': 'username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Имя пользователя'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Повтор пароля'
        self.fields['password1'].widget.attrs.update({'class': INPUT_CLASS, 'autocomplete': 'new-password'})
        self.fields['password2'].widget.attrs.update({'class': INPUT_CLASS, 'autocomplete': 'new-password'})


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['subject', 'title', 'slug', 'overview']
        widgets = {
            'subject': forms.Select(attrs={'class': INPUT_CLASS}),
            'title': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'slug': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'python-basics'}),
            'overview': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 4}),
        }


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'description': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3}),
        }


ModuleFormSet = inlineformset_factory(
    Course,
    Module,
    form=ModuleForm,
    fields=['title', 'description'],
    extra=1,
    can_delete=True
)


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['title', 'slug']
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'slug': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'programming'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'rating': forms.Select(attrs={'class': INPUT_CLASS}),
            'text': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 4, 'placeholder': 'Расскажите о курсе...'}),
        }


class ProfileForm(forms.ModelForm):
    """Форма профиля: ник, почта, телефон, фото."""
    username = forms.CharField(
        label='Ник (логин)',
        max_length=150,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'readonly': 'readonly'})
    )
    email = forms.EmailField(
        label='Почта',
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'email@example.com'})
    )

    class Meta:
        model = Profile
        fields = ['phone', 'photo']
        widgets = {
            'phone': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '+7 (999) 123-45-67'}),
            'photo': forms.FileInput(attrs={'class': INPUT_CLASS, 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.user.email = self.cleaned_data.get('email', profile.user.email)
            profile.user.save()
            profile.save()
        return profile


class TextFigureForm(forms.ModelForm):
    """Форма рисунка. Пустые строки (extra) не требуют заполнения."""
    class Meta:
        model = TextFigure
        fields = ['key', 'caption', 'image']
        widgets = {
            'key': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '1.1'}),
            'caption': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Рисунок 1.1'}),
            'image': forms.FileInput(attrs={'class': INPUT_CLASS, 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Новая строка — поля не обязательны (пустая строка не мешает)
        if not self.instance.pk:
            for f in self.fields.values():
                f.required = False
        elif self.instance.image:
            self.fields['image'].required = False  # при редактировании можно не менять картинку

    def clean(self):
        data = super().clean()
        key, caption, image = data.get('key'), data.get('caption'), data.get('image')
        has_image = image or (self.instance.pk and self.instance.image)
        if any([key, caption, image]) and not all([key, caption, has_image]):
            raise forms.ValidationError('Заполните ключ, подпись и загрузите изображение.')
        return data


TextFigureFormSet = inlineformset_factory(
    Text,
    TextFigure,
    form=TextFigureForm,
    fields=['key', 'caption', 'image'],
    extra=1,
    can_delete=True,
    validate_min=False,  # допускаем 0 рисунков (пустая строка не мешает)
)


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ваше имя'}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ваш email'}),
            'message': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3, 'placeholder': 'Ваше сообщение'}),
        }