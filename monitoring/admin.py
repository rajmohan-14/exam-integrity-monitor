from django.contrib import admin
from .models import ExamSession, SuspiciousEvent, Answer
from .models import ExamSession, SuspiciousEvent, Answer, ExamSnapshot
admin.site.register(ExamSession)
admin.site.register(SuspiciousEvent)
admin.site.register(Answer)
admin.site.register(ExamSnapshot)
