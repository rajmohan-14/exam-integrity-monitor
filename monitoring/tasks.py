from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone


@shared_task
def send_flag_alert(session_id, student_username, exam_title, trust_score):
    """Send email to examiner when a student gets flagged."""
    from .models import ExamSession

    try:
        session = ExamSession.objects.select_related(
            'exam__created_by'
        ).get(id=session_id)

        examiner_email = session.exam.created_by.email

        if not examiner_email:
            print(f"No email for examiner — skipping alert")
            return

        send_mail(
            subject=f'[Exam Monitor] Student flagged — {exam_title}',
            message=f'''
Hello,

A student has been flagged during an exam.

Student: {student_username}
Exam: {exam_title}
Trust Score: {trust_score}
Time: {timezone.now().strftime("%d %b %Y, %I:%M %p")}

Please review their session in the dashboard.

— Exam Monitor
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[examiner_email],
            fail_silently=False,
        )
        print(f"Alert sent to {examiner_email}")

    except ExamSession.DoesNotExist:
        print(f"Session {session_id} not found")


@shared_task
def auto_submit_expired_exams():
    """Periodically check for expired active sessions and auto-submit them."""
    from .models import ExamSession

    now = timezone.now()
    active_sessions = ExamSession.objects.filter(
        status='active'
    ).select_related('exam')

    submitted_count = 0
    for session in active_sessions:
        exam_end_time = session.started_at + timezone.timedelta(
            minutes=session.exam.duration_mins
        )
        if now >= exam_end_time:
            session.status = 'submitted'
            session.submitted_at = now
            session.save()
            submitted_count += 1
            print(f"Auto-submitted session {session.id}")

    return f"Auto-submitted {submitted_count} expired sessions"