from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from exams.models import Exam
from .models import ExamSession, Answer


@login_required(login_url='/users/login/')
def start_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    # Check if student already has an active session
    existing = ExamSession.objects.filter(
        student=request.user,
        exam=exam,
        status='active'
    ).first()

    if existing:
        return redirect('take-exam', session_id=existing.id)

    # Create new session
    session = ExamSession.objects.create(
        student=request.user,
        exam=exam
    )
    return redirect('take-exam', session_id=session.id)


@login_required(login_url='/users/login/')
def take_exam(request, session_id):
    session = get_object_or_404(
        ExamSession,
        id=session_id,
        student=request.user
    )
    exam = session.exam
    questions = list(exam.questions.all())

    if exam.shuffle_questions:
        import random
        random.shuffle(questions)

    if request.method == 'POST':
        for question in exam.questions.all():
            response = request.POST.get(f'question_{question.id}', '')
            Answer.objects.update_or_create(
                session=session,
                question=question,
                defaults={'response': response}
            )
        session.status = 'submitted'
        session.submitted_at = timezone.now()
        session.save()
        return redirect('exam-submitted')

    return render(request, 'monitoring/take_exam.html', {
        'session': session,
        'exam': exam,
        'questions': questions,
    })


@login_required(login_url='/users/login/')
def exam_submitted(request):
    return render(request, 'monitoring/submitted.html')


@login_required(login_url='/users/login/')
def examiner_dashboard(request):
    sessions = ExamSession.objects.filter(
        exam__created_by=request.user
    ).select_related('student', 'exam').order_by('-started_at')
    return render(request, 'monitoring/dashboard.html', {
        'sessions': sessions
    })