from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponse
from exams.models import Exam
from .models import ExamSession, SuspiciousEvent, Answer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.units import cm
import io


@login_required(login_url='/users/login/')
def start_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if not request.user.is_student():
        return redirect('exam-list')

    existing = ExamSession.objects.filter(
        student=request.user,
        exam=exam,
        status='active'
    ).first()

    if existing:
        return redirect('take-exam', session_id=existing.id)

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

    if session.status == 'submitted':
        return redirect('exam-submitted')

    exam = session.exam
    questions = list(exam.questions.all())

    if exam.shuffle_questions:
        import random
        random.seed(str(session.id))
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

        return redirect('exam-result', session_id=session.id)

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
    if not request.user.is_examiner():
        return redirect('exam-list')

    exams = Exam.objects.filter(created_by=request.user).prefetch_related('sessions')

    sessions = ExamSession.objects.filter(
        exam__created_by=request.user
    ).select_related('student', 'exam').prefetch_related('events').order_by('-started_at')

    total_sessions = sessions.count()
    active_sessions = sessions.filter(status='active').count()
    flagged_sessions = sessions.filter(status='flagged').count()
    submitted_sessions = sessions.filter(status='submitted').count()

    return render(request, 'monitoring/dashboard.html', {
        'sessions': sessions,
        'total_sessions': total_sessions,
        'active_sessions': active_sessions,
        'flagged_sessions': flagged_sessions,
        'submitted_sessions': submitted_sessions,
        'exams': exams,
    })


@login_required(login_url='/users/login/')
def session_detail(request, session_id):
    if not request.user.is_examiner():
        return redirect('exam-list')

    session = get_object_or_404(
        ExamSession,
        id=session_id,
        exam__created_by=request.user
    )
    events = session.events.all().order_by('occurred_at')
    answers = session.answers.all().select_related('question')

    return render(request, 'monitoring/session_detail.html', {
        'session': session,
        'events': events,
        'answers': answers,
    })


@login_required(login_url='/users/login/')
def download_report(request, session_id):
    if not request.user.is_examiner():
        return redirect('exam-list')

    session = get_object_or_404(
        ExamSession,
        id=session_id,
        exam__created_by=request.user
    )
    events = session.events.all().order_by('occurred_at')
    answers = session.answers.all().select_related('question')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#666666'),
        spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#1a1a1a'),
        spaceBefore=16,
        spaceAfter=8,
    )
    normal_style = ParagraphStyle(
        'Custom',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=4,
    )

    story.append(Paragraph("Exam Integrity Report", title_style))
    story.append(Paragraph(
        f"Generated on {timezone.now().strftime('%d %B %Y, %I:%M %p')}",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e5e5')))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("Session Information", heading_style))
    info_data = [
        ['Student', session.student.username],
        ['Email', session.student.email or '—'],
        ['Exam', session.exam.title],
        ['Started', session.started_at.strftime('%d %b %Y, %I:%M %p')],
        ['Submitted', session.submitted_at.strftime('%d %b %Y, %I:%M %p') if session.submitted_at else 'Not submitted'],
        ['Status', session.status.upper()],
        ['Trust Score', f"{session.trust_score:.2f} / 1.00"],
        ['Suspicious Events', str(events.count())],
    ]
    info_table = Table(info_data, colWidths=[4*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f9f9f9'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e5e5')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(info_table)

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report.pdf"'
    return response


@login_required(login_url='/users/login/')
def exam_result(request, session_id):
    session = get_object_or_404(
        ExamSession,
        id=session_id,
        student=request.user,
        status='submitted'
    )
    answers = session.answers.all().select_related('question')

    total_marks = 0
    obtained_marks = 0
    results = []

    for answer in answers:
        question = answer.question
        total_marks += question.marks
        is_correct = False

        if question.question_type == 'mcq':
            is_correct = answer.response.strip().lower() == question.correct_answer.strip().lower()
            if is_correct:
                obtained_marks += question.marks
        else:
            is_correct = None

        results.append({
            'question': question,
            'response': answer.response,
            'is_correct': is_correct,
            'marks': question.marks,
        })

    percentage = round((obtained_marks / total_marks * 100), 1) if total_marks > 0 else 0

    return render(request, 'monitoring/result.html', {
        'session': session,
        'results': results,
        'total_marks': total_marks,
        'obtained_marks': obtained_marks,
        'percentage': percentage,
    })


@login_required(login_url='/users/login/')
def leaderboard(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    sessions = ExamSession.objects.filter(
        exam=exam,
        status='submitted'
    ).select_related('student').prefetch_related('answers__question').order_by('-trust_score')

    rankings = []
    for session in sessions:
        answers = session.answers.all().select_related('question')
        obtained = sum(
            a.question.marks for a in answers
            if a.question.question_type == 'mcq'
            and a.response.strip().lower() == a.question.correct_answer.strip().lower()
        )
        total = sum(a.question.marks for a in answers)
        percentage = round((obtained / total * 100), 1) if total > 0 else 0
        rankings.append({
            'session': session,
            'obtained': obtained,
            'total': total,
            'percentage': percentage,
        })

    rankings.sort(key=lambda x: x['percentage'], reverse=True)

    return render(request, 'monitoring/leaderboard.html', {
        'exam': exam,
        'rankings': rankings,
    })
    