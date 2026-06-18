from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from .models import Course, Subject, Module, Content, Enrollment, Review, ContactMessage, Profile, ModuleProgress
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin
)
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateResponseMixin, View
from .forms import (
    ModuleFormSet,
    SubjectForm,
    ReviewForm,
    CourseForm,
    ContactForm,
    ProfileForm,
    TextFigureFormSet,
    SignUpForm,
)
from django.apps import apps
from django.forms.models import modelform_factory
from braces.views import CsrfExemptMixin, JsonRequestResponseMixin
from django.db.models import Prefetch
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

class CourseModuleUpdateView(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'courses/manage/module/formset.html'
    course = None

    def get_formset(self, data=None):
        return ModuleFormSet(instance=self.course, data=data)

    def dispatch(self, request, *args, **kwargs):
        # получаем pk из kwargs и проверяем, что курс принадлежит текущему пользователю
        pk = kwargs.get('pk') or (args[0] if args else None)
        self.course = get_object_or_404(Course, id=pk, owner=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        formset = self.get_formset()
        return self.render_to_response({'course': self.course, 'formset': formset})

    def post(self, request, *args, **kwargs):
        formset = self.get_formset(data=request.POST)
        if formset.is_valid():
            formset.save()
            return redirect('manage_course_list')
        return self.render_to_response({'course': self.course, 'formset': formset})

class HomeView(TemplateView):
    template_name = 'home.html'


class TeachersView(TemplateView):
    template_name = 'courses/teachers.html'

class TeacherAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Доступ для преподавателей: staff или владелец хотя бы одного курса."""
    def test_func(self):
        return (
            self.request.user.is_staff or
            Course.objects.filter(owner=self.request.user).exists()
        )


class OwnerMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)

class OwnerEditMixin:
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

class OwnerCourseMixin(OwnerMixin, TeacherAccessMixin):
    model = Course
    form_class = CourseForm
    success_url = reverse_lazy('manage_course_list')

class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    template_name = 'courses/manage/course/form.html'

class ManageCourseListView(TeacherAccessMixin, ListView):
    model = Course
    template_name = 'courses/manage/course/list.html'

    def get_queryset(self):
        return Course.objects.filter(owner=self.request.user).prefetch_related('modules')

class CourseCreateView(OwnerCourseEditMixin, CreateView):
    pass  # OwnerCourseEditMixin уже проверяет через TeacherAccessMixin-логику; add_course даём через OwnerCourseMixin

class CourseUpdateView(OwnerCourseEditMixin, UpdateView):
    pass

class CourseDeleteView(OwnerCourseMixin, DeleteView):
    template_name = 'courses/manage/course/delete.html'

class LogoutView(DjangoLogoutView):
    http_method_names = ['get', 'post', 'head', 'options', 'trace']


class SignUpView(CreateView):
    """Регистрация нового пользователя на сайте."""
    form_class = SignUpForm
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(self.request, 'Регистрация прошла успешно. Добро пожаловать!')
        return redirect('home')


class ProfileView(LoginRequiredMixin, UpdateView):
    """Профиль пользователя: ник, почта, телефон, фото."""
    model = Profile
    form_class = ProfileForm
    template_name = 'courses/profile/view.html'

    def get_object(self, queryset=None):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def form_valid(self, form):
        messages.success(self.request, 'Профиль обновлён')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('profile')
    
class ContentCreateUpdateView(TemplateResponseMixin, View):
    module = None
    model = None
    obj = None
    template_name = 'courses/manage/content/form.html'
    
    def get_model(self, model_name):
        if model_name in ['text', 'video', 'image', 'file']:
            return apps.get_model(
                app_label='courses', model_name=model_name
            )
        return None
    
    def get_form(self, model, *args, **kwargs):
        Form = modelform_factory(
            model,
            exclude=['owner', 'order', 'created', 'updated']
        )
        return Form(*args, **kwargs)
    
    def dispatch(self, request, module_id, model_name, id=None):
        self.module = get_object_or_404(
            Module, id=module_id, course__owner=request.user
        )
        self.model = self.get_model(model_name)
        if self.model is None:
            # Неподдерживаемый тип контента
            from django.http import Http404
            raise Http404("Неподдерживаемый тип контента")
        if id:
            self.obj = get_object_or_404(
                self.model, id=id, owner=request.user
            )
        return super().dispatch(request, module_id, model_name, id)
    
    def get(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model, instance=self.obj)
        context = {'form': form, 'object': self.obj}
        if self.model.__name__ == 'Text' and self.obj:
            context['figure_formset'] = TextFigureFormSet(instance=self.obj)
        return self.render_to_response(context)

    def post(self, request, module_id, model_name, id=None):
        form = self.get_form(
            self.model,
            instance=self.obj,
            data=request.POST,
            files=request.FILES
        )
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            if not id:
                Content.objects.create(
                    module=self.module, item=obj
                )
            if self.model.__name__ == 'Text' and obj:
                figure_formset = TextFigureFormSet(
                    request.POST, request.FILES, instance=obj
                )
                if not request.FILES and any('-0-' in k or '-1-' in k for k in request.POST):
                    messages.info(request, 'Файл не получен. Выберите изображение (макс. 10 МБ) и нажмите «Сохранить».')
                if figure_formset.is_valid():
                    saved = figure_formset.save()
                    if saved:
                        messages.success(request, f'Рисунки сохранены: {len(saved)} шт.')
                    else:
                        messages.info(request, 'Текст сохранён. Добавьте рисунок (ключ, подпись, файл) и нажмите «Сохранить» ещё раз.')
                else:
                    err_list = []
                    for f in figure_formset.forms:
                        for field, errs in f.errors.items():
                            err_list.extend(errs)
                    err_msg = '; '.join(str(e) for e in err_list)[:150] if err_list else 'заполните ключ, подпись и загрузите файл'
                    messages.warning(request, f'Текст сохранён. Рисунки: {err_msg}')
                    return self.render_to_response({
                        'form': form,
                        'object': obj,
                        'figure_formset': figure_formset,
                    })
            return redirect('module_content_list', self.module.id)
        context = {'form': form, 'object': self.obj}
        if self.model.__name__ == 'Text' and self.obj:
            context['figure_formset'] = TextFigureFormSet(
                request.POST, request.FILES, instance=self.obj
            )
        else:
            context['figure_formset'] = None
        return self.render_to_response(context)
        
class ContentDeleteView(View):
    def post(self, request, id):
        content = get_object_or_404(
            Content,
            id=id,
            module__course__owner=request.user
        )
        module = content.module
        # Удаляем связанный объект только если он существует
        if content.item:
            content.item.delete()
        # Удаляем сам контент
        content.delete()
        return redirect('module_content_list', module.id)
    
class ModuleContentListView(TemplateResponseMixin, View):
    template_name = 'courses/manage/module/content_list.html'
    
    def get(self, request, module_id):
        module = get_object_or_404(
            Module.objects.select_related('course'),
            id=module_id,
            course__owner=request.user
        )
        # Загружаем курс и все его модули
        course = module.course
        # Явно загружаем все модули курса с правильной сортировкой
        all_modules = list(Module.objects.filter(course=course).order_by('order'))
        
        return self.render_to_response({
            'module': module,
            'course': course,
            'all_modules': all_modules
        })
    
class ModuleOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):
    def post(self, request):
        if self.request_json:
            for module_id, order in self.request_json.items():
                # Преобразуем ID в число, так как из JSON приходит строка
                try:
                    module_id_int = int(module_id)
                    Module.objects.filter(
                        id=module_id_int, course__owner=request.user
                    ).update(order=order)
                except (ValueError, TypeError):
                    continue
        return self.render_json_response({'saved': 'OK'})
    
class ContentOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):
    def post(self, request):
        for id, order in self.request_json.items():
            Content.objects.filter(
                id=id, module__course__owner=request.user
            ).update(order=order)
        return self.render_json_response({'saved': 'OK'})


# ============ Subject CRUD ============
class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class SubjectListView(StaffRequiredMixin, ListView):
    model = Subject
    template_name = 'courses/manage/subject/list.html'
    context_object_name = 'subjects'


class SubjectCreateView(StaffRequiredMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'courses/manage/subject/form.html'
    success_url = reverse_lazy('subject_list')


class SubjectUpdateView(StaffRequiredMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'courses/manage/subject/form.html'
    success_url = reverse_lazy('subject_list')
    context_object_name = 'subject'


class SubjectDeleteView(StaffRequiredMixin, DeleteView):
    model = Subject
    template_name = 'courses/manage/subject/delete.html'
    success_url = reverse_lazy('subject_list')
    context_object_name = 'subject'


# ============ Enrollment ============
class CourseCatalogView(ListView):
    """Каталог курсов для студентов."""
    model = Course
    template_name = 'courses/catalog.html'
    context_object_name = 'courses'

    def get_queryset(self):
        return Course.objects.prefetch_related('modules', 'subject', 'reviews').all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            ctx['enrolled_course_ids'] = set(
                Enrollment.objects.filter(user=self.request.user).values_list('course_id', flat=True)
            )
        else:
            ctx['enrolled_course_ids'] = set()
        return ctx


class EnrollmentListView(LoginRequiredMixin, ListView):
    """Мои записи на курсы."""
    model = Enrollment
    template_name = 'courses/enrollments/list.html'
    context_object_name = 'enrollments'

    def get_queryset(self):
        return Enrollment.objects.filter(
            user=self.request.user
        ).select_related('course', 'course__subject')


class EnrollmentCreateView(LoginRequiredMixin, View):
    """Записаться на курс."""
    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        enrollment, created = Enrollment.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={'status': 'active'}
        )
        if created:
            messages.success(request, f'Вы записаны на курс «{course.title}»')
            return redirect('enrollment_list')
        else:
            messages.info(request, 'Вы уже записаны на этот курс')
            return redirect('course_catalog')


class EnrollmentDeleteView(LoginRequiredMixin, View):
    """Отменить запись."""
    def post(self, request, enrollment_id):
        enrollment = get_object_or_404(
            Enrollment,
            id=enrollment_id,
            user=request.user
        )
        course_title = enrollment.course.title
        enrollment.delete()
        messages.success(request, f'Запись на курс «{course_title}» отменена')
        return redirect('enrollment_list')


class CourseEnrollmentListView(LoginRequiredMixin, View):
    """Список записанных на курс (для владельца)."""
    template_name = 'courses/enrollments/course_list.html'

    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, owner=request.user)
        enrollments = course.enrollments.select_related('user').all()
        return render(request, self.template_name, {
            'course': course,
            'enrollments': enrollments
        })


class CourseEnrollmentRemoveView(LoginRequiredMixin, View):
    """Удалить запись (владелец курса)."""
    def post(self, request, course_id, enrollment_id):
        course = get_object_or_404(Course, id=course_id, owner=request.user)
        enrollment = get_object_or_404(Enrollment, id=enrollment_id, course=course)
        enrollment.delete()
        messages.success(request, 'Запись удалена')
        return redirect('course_enrollment_list', course_id)


# ============ Студенты: просмотр контента ============
def _student_enrolled(user, course):
    """Проверяет, записан ли пользователь на курс."""
    return Enrollment.objects.filter(user=user, course=course).exists()


class CourseStudentView(LoginRequiredMixin, View):
    """Курс для студента: список модулей с прогрессом."""
    template_name = 'courses/learn/course.html'

    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        if not _student_enrolled(request.user, course):
            messages.error(request, 'Вы не записаны на этот курс')
            return redirect('enrollment_list')
        modules = course.modules.order_by('order').all()
        completed_ids = set(
            ModuleProgress.objects.filter(
                user=request.user, module__course=course
            ).values_list('module_id', flat=True)
        )
        return render(request, self.template_name, {
            'course': course,
            'modules': modules,
            'completed_module_ids': completed_ids,
        })


class ModuleStudentContentView(LoginRequiredMixin, View):
    """Модуль для студента: контент (только чтение) + отметка «Пройдено»."""
    template_name = 'courses/learn/module.html'

    def get(self, request, module_id):
        module = get_object_or_404(Module.objects.select_related('course'), id=module_id)
        if not _student_enrolled(request.user, module.course):
            messages.error(request, 'Вы не записаны на этот курс')
            return redirect('enrollment_list')
        all_modules = list(module.course.modules.order_by('order'))
        completed_ids = set(
            ModuleProgress.objects.filter(
                user=request.user, module__course=module.course
            ).values_list('module_id', flat=True)
        )
        return render(request, self.template_name, {
            'module': module,
            'course': module.course,
            'all_modules': all_modules,
            'is_completed': module.id in completed_ids,
            'completed_module_ids': completed_ids,
        })


class ModuleProgressCreateView(LoginRequiredMixin, View):
    """Отметить модуль как пройденный."""
    def post(self, request, module_id):
        module = get_object_or_404(Module, id=module_id)
        if not _student_enrolled(request.user, module.course):
            messages.error(request, 'Вы не записаны на этот курс')
            return redirect('enrollment_list')
        ModuleProgress.objects.get_or_create(user=request.user, module=module)
        messages.success(request, f'Модуль «{module.title}» отмечен как пройденный')
        return redirect('learn_module', module_id=module_id)


# ============ Review ============
class CourseReviewListView(ListView):
    """Отзывы о курсе."""
    template_name = 'courses/reviews/list.html'
    context_object_name = 'reviews'

    def get_queryset(self):
        self.course = get_object_or_404(Course, id=self.kwargs['course_id'])
        return self.course.reviews.select_related('user').all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['course'] = self.course
        return ctx


class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'courses/reviews/form.html'

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course, id=kwargs['course_id'])
        existing = Review.objects.filter(course=self.course, user=request.user).first()
        if existing:
            messages.info(request, 'Вы уже оставили отзыв на этот курс')
            return redirect('course_review_list', course_id=self.course.id)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.course = self.course
        messages.success(self.request, 'Отзыв добавлен')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('course_review_list', kwargs={'course_id': self.course.id})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['course'] = self.course
        return ctx


class ReviewUpdateView(LoginRequiredMixin, UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = 'courses/reviews/form.html'
    context_object_name = 'review'

    def dispatch(self, request, *args, **kwargs):
        self.review = get_object_or_404(Review, id=kwargs['pk'], user=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.review

    def form_valid(self, form):
        messages.success(self.request, 'Отзыв обновлён')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('course_review_list', kwargs={'course_id': self.review.course.id})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['course'] = self.review.course
        return ctx


class AllReviewsListView(ListView):
    """Все отзывы студентов — страница с карточками."""
    model = Review
    template_name = 'courses/reviews/all.html'
    context_object_name = 'reviews'

    def get_queryset(self):
        return Review.objects.select_related('user', 'course').order_by('-created_at')[:8]


class ReviewDeleteView(LoginRequiredMixin, DeleteView):
    model = Review
    template_name = 'courses/reviews/delete.html'
    context_object_name = 'review'

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse_lazy('course_review_list', kwargs={'course_id': self.object.course.id})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['course'] = self.object.course
        return ctx


class ContactView(View):
    """Обработка формы обращений из футера: сохранение в БД и опциональная отправка почты."""

    def get(self, request):
        return redirect('home')

    def post(self, request):
        form = ContactForm(request.POST)
        if form.is_valid():
            msg: ContactMessage = form.save()
            self._notify_by_email(msg)
            messages.success(request, 'Сообщение отправлено. Мы свяжемся с вами в ближайшее время.')
        else:
            messages.error(request, 'Проверьте правильность заполнения полей.')
        next_url = request.META.get('HTTP_REFERER') or '/'
        return redirect(next_url)

    def _notify_by_email(self, msg: ContactMessage) -> None:
        """Письмо администратору и подтверждение на указанный в форме email (если настроен SMTP)."""
        from_addr = settings.DEFAULT_FROM_EMAIL
        try:
            if getattr(settings, 'CONTACT_TO_EMAIL', ''):
                body = (
                    f'Имя: {msg.name}\n'
                    f'Email: {msg.email}\n\n'
                    f'{msg.message}'
                )
                send_mail(
                    subject=f'[Online School] Обращение от {msg.name}',
                    message=body,
                    from_email=from_addr,
                    recipient_list=[settings.CONTACT_TO_EMAIL],
                    fail_silently=True,
                )
            if getattr(settings, 'CONTACT_SEND_CONFIRMATION', True) and msg.email:
                send_mail(
                    subject='Online School — мы получили ваше обращение',
                    message=(
                        f'Здравствуйте, {msg.name}!\n\n'
                        'Мы получили ваше сообщение и свяжемся с вами при необходимости.\n\n'
                        f'Текст обращения:\n{msg.message}'
                    ),
                    from_email=from_addr,
                    recipient_list=[msg.email],
                    fail_silently=True,
                )
        except Exception:
            logger.exception('Не удалось отправить почту по обращению id=%s', msg.pk)
