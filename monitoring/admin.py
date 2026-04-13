from django.contrib import admin
from .models import ExamSession, SuspiciousEvent, Answer

admin.site.register(ExamSession)
admin.site.register(SuspiciousEvent)
admin.site.register(Answer)