from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('examiner', 'Examiner'),
    ]
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='student'
    )

    def is_examiner(self):
        return self.role == 'examiner'

    def is_student(self):
        return self.role == 'student'

    def __str__(self):
        return f"{self.username} ({self.role})"