"""CL-CHRONOS - Layer 3: Fixed Occupational / Work Commitments Model."""

from capa2.planner.utils import DAYS_OF_WEEK_CHOICES
from django.conf import settings
from django.db import models


class Occupation(models.Model):
  """Fixed occupational or research event with hourly energy drain impact."""

  user = models.ForeignKey(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE,
      related_name="occupations",
  )
  description = models.CharField(max_length=100)
  day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK_CHOICES)
  start_time = models.TimeField(default="08:00")
  end_time = models.TimeField(default="14:00")
  energy_drain = models.IntegerField(
      default=-20, help_text="Energy impact (negative points)."
  )

  def __str__(self):
    return f"{self.user.username} - {self.description} ({self.day_of_week})"