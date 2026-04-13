from django.db import models
from django.conf import settings
from exams.models import Exam, Question
import uuid


class ExamSession(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('submitted', 'Submitted'),
        ('flagged', 'Flagged'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_sessions'
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    trust_score = models.FloatField(default=1.0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"{self.student.username} — {self.exam.title}"


class SuspiciousEvent(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('med', 'Medium'),
        ('high', 'High'),
    ]
    EVENT_TYPES = [
        ('tab_switch', 'Tab Switch'),
        ('copy', 'Copy'),
        ('paste', 'Paste'),
        ('focus_loss', 'Focus Loss'),
        ('fast_answer', 'Fast Answer'),
        ('right_click', 'Right Click'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ExamSession,
        on_delete=models.CASCADE,
        related_name='events'
    )
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    occurred_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)
    severity = models.CharField(max_length=5, choices=SEVERITY_CHOICES, default='low')

    def __str__(self):
        return f"{self.session.student.username} — {self.event_type}"


class Answer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ExamSession,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    response = models.TextField(blank=True)
    time_taken_sec = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.session.student.username} — Q{self.question.id}"