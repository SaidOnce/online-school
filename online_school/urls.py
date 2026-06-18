"""
URL configuration for online_school project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from courses.views import (
    LogoutView,
    HomeView,
    ContactView,
    AllReviewsListView,
    TeachersView,
    ProfileView,
    SignUpView,
)
from django.contrib.auth.views import LoginView
from django.urls import include, path

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path(
        'accounts/login/', LoginView.as_view(), name='login'
    ),
    path('accounts/signup/', SignUpView.as_view(), name='signup'),
    path(
        'accounts/logout/',
        LogoutView.as_view(),
        name='logout'
    ),
    path('admin/', admin.site.urls),
    path('contact/', ContactView.as_view(), name='contact'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('reviews/', AllReviewsListView.as_view(), name='all_reviews'),
    path('teachers/', TeachersView.as_view(), name='teachers'),
    path('course/', include('courses.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)

