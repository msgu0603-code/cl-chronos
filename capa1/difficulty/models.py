"""CL-CHRONOS - Layer 1: Intrinsic Structural Difficulty Model (d_s in {1, 2, 3, 4, 5})."""

from capa1.academics.models import Subject
from django.db import models


class SubjectDifficulty(models.Model):
  """Stores structural subject complexity; defaults to neutral constant d_s = 3."""

  DIFFICULTY_LEVELS = [
      (1, "Very Easy"),
      (2, "Easy"),
      (3, "Medium"),
      (4, "Hard"),
      (5, "Very Hard"),
  ]

  subject = models.OneToOneField(
      Subject, on_delete=models.CASCADE, related_name="difficulty"
  )
  difficulty_level = models.IntegerField(choices=DIFFICULTY_LEVELS, default=3)

  def __str__(self):
    return f"{self.subject.name} - Difficulty: {self.difficulty_level}"