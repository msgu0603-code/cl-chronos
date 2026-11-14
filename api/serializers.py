"""REST API Serializers for the CL-CHRONOS 4-Layer Scheduling Architecture."""

from capa1.academics.models import AcademicPeriod, Exam, Grade, Subject
from capa1.difficulty.models import SubjectDifficulty
from capa1.projects.models import Project
from capa2.preferences.models import UserPreferences
from capa3.occupation.models import Occupation
from capa3.routine.models import DailyRoutine
from capa3.schedule.models import ClassSchedule
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserPreferencesSerializer(serializers.ModelSerializer):

  class Meta:
    model = UserPreferences
    fields = '__all__'
    read_only_fields = ['user']


class AcademicPeriodSerializer(serializers.ModelSerializer):

  class Meta:
    model = AcademicPeriod
    fields = '__all__'
    read_only_fields = ['user', 'start_date', 'end_date']


class SubjectDifficultySerializer(serializers.ModelSerializer):

  class Meta:
    model = SubjectDifficulty
    fields = '__all__'


class SubjectSerializer(serializers.ModelSerializer):
  difficulty = SubjectDifficultySerializer(read_only=True)

  class Meta:
    model = Subject
    fields = '__all__'
    read_only_fields = ['user']


class GradeSerializer(serializers.ModelSerializer):

  class Meta:
    model = Grade
    fields = '__all__'


class ExamSerializer(serializers.ModelSerializer):

  class Meta:
    model = Exam
    fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):

  class Meta:
    model = Project
    fields = '__all__'
    read_only_fields = ['user']


class OccupationSerializer(serializers.ModelSerializer):

  class Meta:
    model = Occupation
    fields = '__all__'
    read_only_fields = ['user']


class DailyRoutineSerializer(serializers.ModelSerializer):

  class Meta:
    model = DailyRoutine
    fields = '__all__'
    read_only_fields = ['user']


class ClassScheduleSerializer(serializers.ModelSerializer):

  class Meta:
    model = ClassSchedule
    fields = '__all__'
    read_only_fields = ['user']


class RegisterSerializer(serializers.ModelSerializer):
  first_name = serializers.CharField(required=True)
  last_name = serializers.CharField(required=True)
  email = serializers.EmailField(required=True)
  age = serializers.IntegerField(required=True, min_value=12, max_value=99)
  school_year = serializers.CharField(required=True)
  grading_scale = serializers.FloatField(required=True, min_value=1)

  class Meta:
    model = User
    fields = (
        'first_name',
        'last_name',
        'username',
        'email',
        'password',
        'age',
        'school_year',
        'grading_scale',
        'user_type',
    )
    extra_kwargs = {
        'password': {'write_only': True, 'required': True},
        'username': {'required': True},
    }

  def create(self, validated_data):
    return User.objects.create_user(**validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

  def validate(self, attrs):
    data = super().validate(attrs)
    data['first_name'] = self.user.first_name
    return data


class UserProfileSerializer(serializers.ModelSerializer):

  class Meta:
    model = User
    fields = [
        'id',
        'first_name',
        'last_name',
        'email',
        'age',
        'school_year',
        'grading_scale',
        'user_type',
    ]