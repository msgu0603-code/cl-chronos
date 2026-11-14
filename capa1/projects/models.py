"""CL-CHRONOS - Layer 1: Academic and Independent Personal Projects Model."""

from capa1.academics.models import Subject
from django.conf import settings
from django.db import models


class Project(models.Model):
  """Represents subject-linked or independent projects evaluated via piecewise workload inflation."""

  STATUS_CHOICES = [
      ("pending", "Pending"),
      ("in_progress", "In Progress"),
      ("completed", "Completed"),
  ]

  user = models.ForeignKey(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE,
      related_name="projects",
  )
  subject = models.ForeignKey(
      Subject, on_delete=models.CASCADE, null=True, blank=True
  )
  name = models.CharField(max_length=100)
  description = models.TextField(blank=True)
  due_date = models.DateField()
  priority = models.IntegerField(default=1)
  estimated_hours = models.FloatField(default=1.0)
  status = models.CharField(
      max_length=20, choices=STATUS_CHOICES, default="pending"
  )

  def __str__(self):
    return self.name