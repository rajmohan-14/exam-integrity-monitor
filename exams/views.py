from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Exam, Question
from .forms import ExamForm, QuestionForm
from django.contrib import messages as django_messages


def examiner_required(view_func):
    """Custom decorator — only examiners can access this view."""
    @login_required(login_url='/users/login/')
    def wrapper(request, *args, **kwargs):
        if not request.user.is_examiner():
            messages.error(request, 'Only examiners can access this page.')
            return redirect('exam-list')
        return view_func(request, *args, **kwargs)
    return wrapper


def student_required(view_func):
    """Custom decorator — only students can access this view."""
    @login_required(login_url='/users/login/')
    def wrapper(request, *args, **kwargs):
        if not request.user.is_student():
            messages.error(request, 'Only students can access this page.')
            return redirect('exam-list')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required(login_url='/users/login/')
def exam_list(request):
    exams = Exam.objects.all().order_by('starts_at')
    return render(request, 'exams/exam_list.html', {'exams': exams})


@login_required(login_url='/users/login/')
def exam_detail(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all()
    return render(request, 'exams/exam_detail.html', {
        'exam': exam,
        'questions': questions
    })


@examiner_required
def create_exam(request):
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            messages.success(request, 'Exam created successfully!')
            return redirect('add-question', exam_id=exam.id)
    else:
        form = ExamForm()
    return render(request, 'exams/create_exam.html', {'form': form})


@examiner_required
def add_question(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.exam = exam
            question.save()
            messages.success(request, 'Question added!')
            if 'add_another' in request.POST:
                return redirect('add-question', exam_id=exam.id)
            return redirect('exam-detail', exam_id=exam.id)
    else:
        form = QuestionForm()
    return render(request, 'exams/add_question.html', {
        'form': form,
        'exam': exam
    })
@examiner_required
def edit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exam updated successfully.')
            return redirect('exam-detail', exam_id=exam.id)
    else:
        form = ExamForm(instance=exam)
    return render(request, 'exams/create_exam.html', {
        'form': form,
        'exam': exam,
        'editing': True
    })


@examiner_required
def delete_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'Exam deleted.')
        return redirect('exam-list')
    return render(request, 'exams/confirm_delete.html', {'exam': exam})


@examiner_required
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id, exam__created_by=request.user)
    exam_id = question.exam.id
    question.delete()
    messages.success(request, 'Question deleted.')
    return redirect('exam-detail', exam_id=exam_id)