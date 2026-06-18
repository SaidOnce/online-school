from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),

    # Специфичные пути (до <pk>)
    path('mine/', views.ManageCourseListView.as_view(), name='manage_course_list'),
    path('create/', views.CourseCreateView.as_view(), name='course_create'),
    path('catalog/', views.CourseCatalogView.as_view(), name='course_catalog'),
    path('enrollments/', views.EnrollmentListView.as_view(), name='enrollment_list'),
    path('enrollments/<int:enrollment_id>/cancel/', views.EnrollmentDeleteView.as_view(), name='enrollment_cancel'),
    path('enroll/<int:course_id>/', views.EnrollmentCreateView.as_view(), name='enroll'),
    path('learn/<int:course_id>/', views.CourseStudentView.as_view(), name='learn_course'),
    path('learn/module/<int:module_id>/', views.ModuleStudentContentView.as_view(), name='learn_module'),
    path('learn/module/<int:module_id>/complete/', views.ModuleProgressCreateView.as_view(), name='learn_module_complete'),
    path('subjects/', views.SubjectListView.as_view(), name='subject_list'),
    path('subjects/create/', views.SubjectCreateView.as_view(), name='subject_create'),
    path('subjects/<int:pk>/edit/', views.SubjectUpdateView.as_view(), name='subject_edit'),
    path('subjects/<int:pk>/delete/', views.SubjectDeleteView.as_view(), name='subject_delete'),
    path('review/<int:pk>/edit/', views.ReviewUpdateView.as_view(), name='review_edit'),
    path('review/<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='review_delete'),

    # Контент модулей
    path('module/<int:module_id>/content/<model_name>/create/', views.ContentCreateUpdateView.as_view(), name='module_content_create'),
    path('module/<int:module_id>/content/<model_name>/<id>/', views.ContentCreateUpdateView.as_view(), name='module_content_update'),
    path('content/<int:id>/delete/', views.ContentDeleteView.as_view(), name='module_content_delete'),
    path('module/<int:module_id>/', views.ModuleContentListView.as_view(), name='module_content_list'),
    path('module/order/', views.ModuleOrderView.as_view(), name='module_order'),
    path('content/order/', views.ContentOrderView.as_view(), name='content_order'),

    # Курсы по pk
    path('<int:pk>/edit/', views.CourseUpdateView.as_view(), name='course_edit'),
    path('<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    path('<int:pk>/module/', views.CourseModuleUpdateView.as_view(), name='course_module_update'),
    path('<int:pk>/enrollments/', views.CourseEnrollmentListView.as_view(), name='course_enrollment_list'),
    path('<int:course_id>/enrollments/<int:enrollment_id>/remove/', views.CourseEnrollmentRemoveView.as_view(), name='course_enrollment_remove'),

    # Отзывы по course_id
    path('<int:course_id>/reviews/', views.CourseReviewListView.as_view(), name='course_review_list'),
    path('<int:course_id>/review/create/', views.ReviewCreateView.as_view(), name='review_create'),
]