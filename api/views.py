"""REST API Views for the CL-CHRONOS Scheduling Engine."""

from algorithm.engine import CLChronosEngine
from capa1.academics.models import AcademicPeriod, Exam, Grade, Subject
from capa1.projects.models import Project
from capa2.preferences.models import UserPreferences
from capa3.occupation.models import Occupation
from capa3.routine.models import DailyRoutine
from capa3.schedule.models import ClassSchedule
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    AcademicPeriodSerializer,
    ClassScheduleSerializer,
    CustomTokenObtainPairSerializer,
    DailyRoutineSerializer,
    ExamSerializer,
    GradeSerializer,
    OccupationSerializer,
    ProjectSerializer,
    RegisterSerializer,
    SubjectSerializer,
    UserPreferencesSerializer,
    UserProfileSerializer,
)

User = get_user_model()


class RegisterView(APIView):
  permission_classes = [AllowAny]
  throttle_scope = 'anon'

  def post(self, request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
      serializer.save()
      return Response(
          {'message': 'User successfully registered in CL-CHRONOS.'},
          status=status.HTTP_201_CREATED,
      )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
  serializer_class = CustomTokenObtainPairSerializer


class UserProfileView(APIView):
  permission_classes = [IsAuthenticated]

  def get(self, request):
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)

  def patch(self, request):
    serializer = UserProfileSerializer(
        request.user, data=request.data, partial=True
    )
    if serializer.is_valid():
      serializer.save()
      return Response(
          {'success': True, 'message': 'Profile updated.'},
          status=status.HTTP_200_OK,
      )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- Layer 1, 2, and 3 Domain ViewSets ---
class SubjectViewSet(viewsets.ModelViewSet):
  serializer_class = SubjectSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    return Subject.objects.select_related('difficulty').filter(
        user=self.request.user
    )

  def perform_create(self, serializer):
    serializer.save(user=self.request.user)


class GradeViewSet(viewsets.ModelViewSet):
  serializer_class = GradeSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    return Grade.objects.select_related('subject').filter(
        subject__user=self.request.user
    )


class ExamViewSet(viewsets.ModelViewSet):
  serializer_class = ExamSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    queryset = Exam.objects.select_related('subject').filter(
        subject__user=self.request.user
    )
    subject_id = self.request.query_params.get('subject')
    if subject_id:
      return queryset.filter(subject_id=subject_id)
    return queryset


class ProjectViewSet(viewsets.ModelViewSet):
  serializer_class = ProjectSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    queryset = Project.objects.select_related('subject').filter(
        user=self.request.user
    )
    subject_id = self.request.query_params.get('subject')
    if subject_id:
      return queryset.filter(subject_id=subject_id)
    return queryset

  def perform_create(self, serializer):
    serializer.save(user=self.request.user)


class UserPreferencesViewSet(viewsets.ModelViewSet):
  serializer_class = UserPreferencesSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    return UserPreferences.objects.filter(user=self.request.user)

  def perform_create(self, serializer):
    serializer.save(user=self.request.user)


class DailyRoutineViewSet(viewsets.ModelViewSet):
  serializer_class = DailyRoutineSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    return DailyRoutine.objects.filter(user=self.request.user)

  def perform_create(self, serializer):
    serializer.save(user=self.request.user)


class OccupationViewSet(viewsets.ModelViewSet):
  serializer_class = OccupationSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    return Occupation.objects.filter(user=self.request.user)

  def perform_create(self, serializer):
    serializer.save(user=self.request.user)


class ClassScheduleViewSet(viewsets.ModelViewSet):
  serializer_class = ClassScheduleSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    return ClassSchedule.objects.select_related('subject').filter(
        user=self.request.user
    )

  def perform_create(self, serializer):
    serializer.save(user=self.request.user)


class AcademicPeriodViewSet(viewsets.ModelViewSet):
  serializer_class = AcademicPeriodSerializer
  permission_classes = [IsAuthenticated]

  def get_queryset(self):
    return AcademicPeriod.objects.filter(user=self.request.user).order_by(
        '-start_date'
    )

  def perform_create(self, serializer):
    if serializer.validated_data.get('is_active', True):
      AcademicPeriod.objects.filter(user=self.request.user).update(
          is_active=False
      )
    serializer.save(user=self.request.user)

  @action(detail=True, methods=['post'])
  def clausurar(self, request, pk=None):
    period = self.get_object()
    period.is_active = False
    period.end_date = timezone.now().date()
    period.save()
    return Response(
        {'status': 'Academic period closed.'}, status=status.HTTP_200_OK
    )

  @action(detail=True, methods=['post'])
  def activar(self, request, pk=None):
    AcademicPeriod.objects.filter(user=self.request.user).update(
        is_active=False
    )
    period = self.get_object()
    period.is_active = True
    period.end_date = None
    period.save()
    return Response(
        {'status': 'Academic period activated.'}, status=status.HTTP_200_OK
    )


# --- CL-CHRONOS 4-Layer Algorithmic Execution Endpoint ---
class GenerateScheduleView(APIView):
  permission_classes = [IsAuthenticated]

  def get(self, request, username):
    try:
      user = User.objects.get(username=username)
      if request.user != user:
        return Response(
            {'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN
        )

      motor = CLChronosEngine(user)
      return Response(motor.generate_full_schedule(), status=status.HTTP_200_OK)

    except User.DoesNotExist:
      return Response(
          {'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND
      )
    except Exception as e:
      return Response(
          {'error': 'Internal engine error', 'details': str(e)},
          status=status.HTTP_500_INTERNAL_SERVER_ERROR,
      )