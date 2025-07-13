from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('sensores_app.urls')),  # incluir urls de tu app sensores_app
]
