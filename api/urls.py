"""URL routing for the CL-CHRONOS REST API."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    AcademicPeriodViewSet,
    ClassScheduleViewSet,
    DailyRoutineViewSet,
    ExamViewSet,
    GenerateScheduleView,
    GradeViewSet,
    OccupationViewSet,
    ProjectViewSet,
    RegisterView,
    SubjectViewSet,
    UserPreferencesViewSet,
    UserProfileView,
)

router = DefaultRouter()
router.register(
    r'academic-periods', AcademicPeriodViewSet, basename='academic-period'
)
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'grades', GradeViewSet, basename='grade')
router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'preferences', UserPreferencesViewSet, basename='preference')
router.register(r'routines', DailyRoutineViewSet, basename='routine')
router.register(r'occupations', OccupationViewSet, basename='occupation')
router.register(
    r'class-schedule', ClassScheduleViewSet, basename='class-schedule'
)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path(
        'schedule/generate/<str:username>/',
        GenerateScheduleView.as_view(),
        name='engine_generate_schedule',
    ),
]