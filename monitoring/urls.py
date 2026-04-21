from django.urls import path
from . import views

urlpatterns = [
    path('start/<uuid:exam_id>/', views.start_exam, name='start-exam'),
    path('take/<uuid:session_id>/', views.take_exam, name='take-exam'),
    path('result/<uuid:session_id>/', views.exam_result, name='exam-result'),
    path('submitted/', views.exam_submitted, name='exam-submitted'),
    path('dashboard/', views.examiner_dashboard, name='dashboard'),
    path('session/<uuid:session_id>/', views.session_detail, name='session-detail'),
    path('session/<uuid:session_id>/snapshot/', views.save_snapshot, name='save-snapshot'),
    path('session/<uuid:session_id>/report/', views.download_report, name='download-report'),
    path('leaderboard/<uuid:exam_id>/', views.leaderboard, name='leaderboard'),
]