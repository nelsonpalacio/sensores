from django.urls import path, include

urlpatterns = [
    path('', include('sensores_app.urls')),
    # otras rutas...
]
