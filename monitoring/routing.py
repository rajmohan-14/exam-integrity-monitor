from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/exam/(?P<session_id>[0-9a-f-]+)/$',
        consumers.ExamConsumer.as_asgi()
    ),
    re_path(
        r'ws/dashboard/(?P<session_id>[0-9a-f-]+)/$',
        consumers.DashboardConsumer.as_asgi()
    ),
]