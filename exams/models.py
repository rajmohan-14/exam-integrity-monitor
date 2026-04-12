from django.db import models
import uuid

class Exam(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    duration_mins = models.IntegerField()
    starts_at = models.DateTimeField()
    shuffle_questions = models.BooleanField(default=True)
    trust_threshold = models.FloatField(default=0.5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('short', 'Short Answer'),
        ('long', 'Long Answer'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    body = models.TextField()
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES)
    options = models.JSONField(blank=True, null=True)  # for MCQ only
    correct_answer = models.CharField(max_length=500, blank=True)
    marks = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.exam.title} — Q{self.marks}"