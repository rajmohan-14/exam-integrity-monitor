from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Exam

@login_required(login_url='/users/login/')
def exam_list(request):
    exams = Exam.objects.all().order_by('starts_at')
    return render(request, 'exams/exam_list.html', {'exams': exams})