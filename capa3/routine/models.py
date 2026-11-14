"""CL-CHRONOS - Layer 3: Biological Routines Model (Active, Deep, and Passive Recovery)."""

from capa2.planner.utils import DAYS_OF_WEEK_CHOICES
from django.conf import settings
from django.db import models


class DailyRoutine(models.Model):
  """Fixed biological routine modulating energy via active (1.0x), deep (1.5x), or passive (0.0x) recovery."""

  ACTIVITY_TYPES = [
      ("meal", "Meal"),
      ("exercise", "Exercise"),
      ("sleep", "Sleep"),
      ("meditation", "Meditation"),
      ("leisure", "Leisure / Screen Time"),
      ("other", "Other"),
  ]

  RECOVERY_TYPES = [
      ("deep", "Deep Cognitive Reset (Sleep / Meditation - 1.5x)"),
      ("active", "Active Recovery (Exercise / Walk - 1.0x)"),
      ("passive", "Passive / Dopaminergic Overstimulation (0.0x)"),
      ("none", "Non-restorative Routine"),
  ]

  user = models.ForeignKey(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE,
      related_name="routines",
  )
  activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
  day_of_week = models.CharField(
      max_length=10, choices=DAYS_OF_WEEK_CHOICES, default="Monday"
  )
  start_time = models.TimeField(default="16:00")
  end_time = models.TimeField(default="17:00")
  recovery_type = models.CharField(
      max_length=20, choices=RECOVERY_TYPES, default="active"
  )
  energy_impact = models.FloatField(default=5.0)

  def __str__(self):
    return f"{self.user.username} - {self.activity_type} ({self.day_of_week})"