from django.urls import path
from . import views

urlpatterns = [
    path('', views.exam_list, name='exam-list'),
    path('create/', views.create_exam, name='create-exam'),
    path('<uuid:exam_id>/', views.exam_detail, name='exam-detail'),
    path('<uuid:exam_id>/edit/', views.edit_exam, name='edit-exam'),
    path('<uuid:exam_id>/delete/', views.delete_exam, name='delete-exam'),
    path('<uuid:exam_id>/add-question/', views.add_question, name='add-question'),
    path('question/<uuid:question_id>/delete/', views.delete_question, name='delete-question'),
]