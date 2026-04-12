from django.shortcuts import render
from .models import Exam

def exam_list(request):
    exams = Exam.objects.all().order_by('starts_at')
    return render(request, 'exams/exam_list.html', {'exams': exams})