from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TechnicianViewSet, CustomerViewSet, StyleTagViewSet, NailDesignViewSet,
    AppointmentViewSet, NailWorkViewSet, CustomerPreferenceViewSet, StatisticsViewSet,
    ContactRecordViewSet, CustomerOpsViewSet, TryOnTaskViewSet, DesignClickLogViewSet,
    TryOnStatisticsViewSet
)

router = DefaultRouter()
router.register(r'technicians', TechnicianViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'style-tags', StyleTagViewSet)
router.register(r'designs', NailDesignViewSet)
router.register(r'appointments', AppointmentViewSet)
router.register(r'works', NailWorkViewSet)
router.register(r'preferences', CustomerPreferenceViewSet)
router.register(r'contact-records', ContactRecordViewSet)
router.register(r'customer-ops', CustomerOpsViewSet, basename='customer_ops')
router.register(r'statistics', StatisticsViewSet, basename='statistics')
router.register(r'try-on-tasks', TryOnTaskViewSet)
router.register(r'design-clicks', DesignClickLogViewSet)
router.register(r'try-on-statistics', TryOnStatisticsViewSet, basename='try_on_statistics')

urlpatterns = [
    path('', include(router.urls)),
]
