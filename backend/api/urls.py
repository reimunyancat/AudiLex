from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'processings', views.ProcessingViewSet, basename='processing')

urlpatterns = [
    path('', include(router.urls)),
]
