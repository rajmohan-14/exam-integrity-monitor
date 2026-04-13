from django.urls import path
from . import views

urlpatterns = [
    path('start/<uuid:exam_id>/', views.start_exam, name='start-exam'),
    path('take/<uuid:session_id>/', views.take_exam, name='take-exam'),
    path('submitted/', views.exam_submitted, name='exam-submitted'),
    path('dashboard/', views.examiner_dashboard, name='dashboard'),
]