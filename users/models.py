"""User domain model for the CL-CHRONOS scheduling engine."""

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class User(AbstractUser):
  """Custom user profile storing academic scale and occupational typology."""

  age = models.IntegerField(
      validators=[MinValueValidator(12), MaxValueValidator(99)],
      null=True,
      blank=True,
  )
  school_year = models.CharField(max_length=50, blank=True, default='')
  grading_scale = models.FloatField(default=10.0)

  USER_TYPES = [
      ('student', 'Student'),
      ('worker', 'Worker'),
  ]
  user_type = models.CharField(
      max_length=20, choices=USER_TYPES, default='student'
  )

  def __str__(self):
    return self.username