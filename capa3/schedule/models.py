"""CL-CHRONOS - Layer 3: Fixed Academic Class Schedule Model (I_e = -15.0 pts/h)."""

from capa1.academics.models import Subject
from capa2.planner.utils import DAYS_OF_WEEK_CHOICES
from django.conf import settings
from django.db import models


class ClassSchedule(models.Model):
  """Fixed curricular class interval draining user energy at I_e = -15.0 pts/h."""

  user = models.ForeignKey(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE,
      related_name="class_schedule",
  )
  subject = models.ForeignKey(
      Subject, on_delete=models.CASCADE, null=True, blank=True
  )
  day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK_CHOICES)
  start_time = models.TimeField(default="08:00")
  end_time = models.TimeField(default="10:00")

  def __str__(self):
    return f"{self.user.username} - {self.day_of_week} ({self.start_time}-{self.end_time})"