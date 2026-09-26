from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/ask", views.ask, name="ask"),
    path("api/analyze", views.analyze, name="analyze"),
]
