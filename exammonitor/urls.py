from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('exams/', include('exams.urls')),
    path('users/', include('users.urls')),
    path('monitor/', include('monitoring.urls')),  # ← add this
    path('', RedirectView.as_view(url='/exams/')),
]