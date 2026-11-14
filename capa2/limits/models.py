"""CL-CHRONOS - Layer 2: Session Limit Configuration Model."""

from django.conf import settings
from django.db import models


class SessionLimit(models.Model):
  """Defines upper bounds on daily and per-session study durations."""

  user = models.OneToOneField(
      settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="limits"
  )
  max_hours_per_day = models.FloatField(default=4.0)
  max_hours_per_session = models.FloatField(default=2.0)

  def __str__(self):
    return f"{self.user.username} Limits"