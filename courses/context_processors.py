from .forms import ContactForm
from .models import Profile, Course


def contact_form(request):
    """Добавляет форму обращений и флаги доступа в контекст всех шаблонов."""
    ctx = {'contact_form': ContactForm()}
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        ctx['user_profile'] = profile
        # Мои курсы: staff, админ или владелец хотя бы одного курса
        ctx['user_can_manage_courses'] = (
            request.user.is_staff or
            Course.objects.filter(owner=request.user).exists()
        )
    else:
        ctx['user_profile'] = None
        ctx['user_can_manage_courses'] = False
    return ctx
