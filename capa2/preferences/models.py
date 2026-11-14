"""CL-CHRONOS - Layer 2: Base Thermodynamic and Ultradian User Parameters."""

from django.conf import settings
from django.db import models


class UserPreferences(models.Model):
  """Calibratable base parameters: L=100, l_b=60 min, l_br=15 min, l_dec=30 min."""

  STUDY_TIMES = [
      ("morning", "Morning (07:30 - 22:00)"),
      ("afternoon", "Afternoon (14:30 - 22:00)"),
      ("night", "Night (18:00 - 23:00)"),
  ]

  COGNITIVE_MODES = [
      ("balanced", "Balanced"),
      ("crunch_time", "Crunch Time"),
      ("recovery", "Recovery"),
  ]

  user = models.OneToOneField(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE,
      related_name="preferences",
  )
  preferred_study_time = models.CharField(
      max_length=20, choices=STUDY_TIMES, default="afternoon"
  )
  block_length = models.IntegerField(default=60)  # l_b = 60 min
  break_length = models.IntegerField(default=15)  # l_br = 15 min
  daily_energy_limit = models.IntegerField(default=100)  # L = 100 pts
  decompression_buffer = models.IntegerField(default=30)  # l_dec = 30 min
  cognitive_mode = models.CharField(
      max_length=20, choices=COGNITIVE_MODES, default="balanced"
  )

  def __str__(self):
    return f"{self.user.username} Preferences"