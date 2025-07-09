from django.urls import path
from .views import AnalyzeSpendView

urlpatterns = [
    path('analyze/', AnalyzeSpendView.as_view(), name='analyze-spend'),
]