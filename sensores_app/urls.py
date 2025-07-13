from django.urls import path
from .views import home, ver_anomalias

urlpatterns = [
    path('', home, name='home'),
    path('anomalias/', ver_anomalias, name='anomalias'),
]