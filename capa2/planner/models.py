"""CL-CHRONOS - Layer 2 & 3: Study Plan and Approved Study Session Persistence Models."""

from capa1.academics.models import Subject
from capa2.planner.utils import DAYS_OF_WEEK_CHOICES
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class StudyPlan(models.Model):
  """Container for a user's generated weekly study schedule."""

  user = models.ForeignKey(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE,
      related_name="study_plans",
  )
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f"Plan for {self.user.username} - {self.created_at}"


class StudySession(models.Model):
  """Individual study block [t_start, t_end) subset of T approved after Layer 3 collision resolution."""

  study_plan = models.ForeignKey(
      StudyPlan, on_delete=models.CASCADE, related_name="sessions"
  )
  subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
  day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK_CHOICES)
  start_time = models.TimeField()
  end_time = models.TimeField()
  completed = models.BooleanField(default=False)
  reason_code = models.CharField(max_length=50, default="STANDARD_ALLOCATION")

  @property
  def hours(self):
    start = self.start_time.hour + self.start_time.minute / 60.0
    end = self.end_time.hour + self.end_time.minute / 60.0
    return round(end - start, 2)

  def clean(self):
    if self.start_time >= self.end_time:
      raise ValidationError("Start time must be strictly earlier than end time.")
    super().clean()

  def save(self, *args, **kwargs):
    self.full_clean()
    super().save(*args, **kwargs)

  def __str__(self):
    return f"{self.subject.name} - {self.day_of_week} ({self.start_time}-{self.end_time})"