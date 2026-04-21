from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from exams.models import Exam
from .models import ExamSession, SuspiciousEvent, Answer, ExamSnapshot
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.units import cm
import io
import json


@login_required(login_url='/users/login/')
def start_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if not request.user.is_student():
        return redirect('exam-list')
    existing = ExamSession.objects.filter(
        student=request.user, exam=exam, status='active'
    ).first()
    if existing:
        return redirect('take-exam', session_id=existing.id)
    session = ExamSession.objects.create(student=request.user, exam=exam)
    return redirect('take-exam', session_id=session.id)


@login_required(login_url='/users/login/')
def take_exam(request, session_id):
    session = get_object_or_404(ExamSession, id=session_id, student=request.user)
    if session.status == 'submitted':
        return redirect('exam-result', session_id=session.id)
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
        'session': session, 'exam': exam, 'questions': questions,
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
    return render(request, 'monitoring/dashboard.html', {
        'sessions': sessions,
        'total_sessions': sessions.count(),
        'active_sessions': sessions.filter(status='active').count(),
        'flagged_sessions': sessions.filter(status='flagged').count(),
        'submitted_sessions': sessions.filter(status='submitted').count(),
        'exams': exams,
    })


@login_required(login_url='/users/login/')
def session_detail(request, session_id):
    if not request.user.is_examiner():
        return redirect('exam-list')
    session = get_object_or_404(
        ExamSession, id=session_id, exam__created_by=request.user
    )
    events = session.events.all().order_by('occurred_at')
    answers = session.answers.all().select_related('question')
    snapshots = session.snapshots.all().order_by('taken_at')  # ← fixed
    return render(request, 'monitoring/session_detail.html', {
        'session': session,
        'events': events,
        'answers': answers,
        'snapshots': snapshots,  # ← fixed
    })


@login_required(login_url='/users/login/')
def download_report(request, session_id):
    if not request.user.is_examiner():
        return redirect('exam-list')
    session = get_object_or_404(
        ExamSession, id=session_id, exam__created_by=request.user
    )
    events = session.events.all().order_by('occurred_at')
    answers = session.answers.all().select_related('question')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'],
        fontSize=20, textColor=colors.HexColor('#1a1a1a'), spaceAfter=6)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
        fontSize=11, textColor=colors.HexColor('#666666'), spaceAfter=20)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'],
        fontSize=13, textColor=colors.HexColor('#1a1a1a'), spaceBefore=16, spaceAfter=8)
    normal_style = ParagraphStyle('Custom', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#1a1a1a'), spaceAfter=4)

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
        ['Snapshots Taken', str(session.snapshots.count())],
    ]
    info_table = Table(info_data, colWidths=[4*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f9f9f9'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e5e5')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (1, 6), (1, 6),
            colors.HexColor('#dc2626') if session.trust_score < 0.5
            else colors.HexColor('#16a34a')),
        ('FONTNAME', (1, 6), (1, 6), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 5), (1, 5),
            colors.HexColor('#dc2626') if session.status == 'flagged'
            else colors.HexColor('#1a1a1a')),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.4*cm))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e5e5')))
    story.append(Paragraph("Suspicious Events Log", heading_style))

    if events.count() > 0:
        event_data = [['#', 'Event Type', 'Severity', 'Time']]
        for i, event in enumerate(events, 1):
            event_data.append([
                str(i),
                event.get_event_type_display(),
                event.severity.upper(),
                event.occurred_at.strftime('%I:%M:%S %p'),
            ])
        event_table = Table(event_data, colWidths=[1*cm, 6*cm, 4*cm, 5*cm])
        event_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a1a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e5e5')),
            ('PADDING', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(event_table)
    else:
        story.append(Paragraph("No suspicious events recorded.", normal_style))

    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e5e5')))
    story.append(Paragraph("Student Answers", heading_style))

    if answers.count() > 0:
        for i, answer in enumerate(answers, 1):
            story.append(Paragraph(
                f"<b>Q{i}.</b> {answer.question.body}", normal_style
            ))
            story.append(Paragraph(
                f"<b>Answer:</b> {answer.response or '(no answer)'}",
                ParagraphStyle('Answer', parent=normal_style,
                    leftIndent=20, textColor=colors.HexColor('#444444'), spaceAfter=10)
            ))
    else:
        story.append(Paragraph("No answers recorded.", normal_style))

    doc.build(story)
    buffer.seek(0)
    filename = f"report_{session.student.username}_{session.exam.title}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required(login_url='/users/login/')
def exam_result(request, session_id):
    session = get_object_or_404(
        ExamSession, id=session_id,
        student=request.user, status='submitted'
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
        exam=exam, status='submitted'
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
        'exam': exam, 'rankings': rankings,
    })


@login_required(login_url='/users/login/')
@require_POST
def save_snapshot(request, session_id):
    session = get_object_or_404(
        ExamSession, id=session_id,
        student=request.user, status='active'
    )
    try:
        data = json.loads(request.body)
        image_data = data.get('image', '')
        if image_data:
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            ExamSnapshot.objects.create(session=session, image=image_data)
            return JsonResponse({'status': 'saved'})
        return JsonResponse({'status': 'no image'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)