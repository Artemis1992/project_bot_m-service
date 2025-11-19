from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ApprovalChainViewSet

router = DefaultRouter()
router.register("approvals", ApprovalChainViewSet, basename="approval")

urlpatterns = [
    path("", include(router.urls)),
]

