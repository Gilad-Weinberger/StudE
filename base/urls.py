from django.urls import path
from . import views

app_name = 'base'

urlpatterns = [
    path('', views.Dashboard, name='dashboard'),
    path('classes/', views.Classes, name='classes'),
    path('classes/create/', views.create_class, name='create_class'),
    path('class/<int:class_id>/', views.Class_Page, name='class_page'),
    path('assignments/', views.Assignments, name='assignments'),
    path('assignments/create/', views.create_assignment, name='create_assignment'),
    path('assignments/<int:assignment_id>/update/', views.update_assignment, name='update_assignment'),
    path('exams/', views.Exams, name='exams'),
    path('exams/create/', views.create_exam, name='create_exam'),
    path('exams/<int:exam_id>/update/', views.update_exam, name='update_exam'),
    path('grades/', views.Grades, name='grades'),
]