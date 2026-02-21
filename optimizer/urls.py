from django.urls import path
from optimizer.views import OptimizeRouteView

urlpatterns = [
    path("optimize/", OptimizeRouteView.as_view()),
]
