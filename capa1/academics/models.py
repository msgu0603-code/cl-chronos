"""CL-CHRONOS - Layer 1: Academic Domain Models (AcademicPeriod, Subject, Grade, Exam)."""

from django.conf import settings
from django.db import models


class AcademicPeriod(models.Model):
  """Represents an active or historical academic term/semester for grade filtering."""

  user = models.ForeignKey(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE,
      related_name="academic_periods",
  )
  name = models.CharField(max_length=100, default="Periodo Actual")
  start_date = models.DateField(auto_now_add=True)
  end_date = models.DateField(null=True, blank=True)
  is_active = models.BooleanField(default=True)

  def __str__(self):
    status = "Active" if self.is_active else "Closed"
    return f"{self.name} - {self.user.username} ({status})"


class Subject(models.Model):
  """Schedulable academic subject classified by cognitive profile and core/supplementary status."""

  COGNITIVE_TYPES = [
      ("logic_math", "Logical-Mathematical (High Executive Demand: 35 pts/h)"),
      ("creative", "Creative / Synthesis (Divergent Processing: 25 pts/h)"),
      (
          "reading_memory",
          "Reading / Memory (Encoding & Assimilation: 20 pts/h)",
      ),
      ("passive", "Passive / Light Review (Low Demand: 10 pts/h)"),
  ]

  user = models.ForeignKey(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE,
      related_name="subjects",
  )
  name = models.CharField(max_length=100)
  cognitive_type = models.CharField(
      max_length=20, choices=COGNITIVE_TYPES, default="reading_memory"
  )
  # Layer 1 Filter: True = Core subject (requires autonomous study), False = Supplementary (0.0 h base)
  requires_study = models.BooleanField(default=True)

  def __str__(self):
    return f"{self.name} ({self.user.username})"


class Grade(models.Model):
  """Recorded academic grade used to compute normalized historical performance a_s in [0, 1]."""

  subject = models.ForeignKey(
      Subject, on_delete=models.CASCADE, related_name="grades"
  )
  period = models.ForeignKey(
      AcademicPeriod,
      on_delete=models.CASCADE,
      related_name="grades",
      null=True,
      blank=True,
  )
  score = models.FloatField()
  max_score = models.FloatField(default=10.0)
  date = models.DateField()

  def save(self, *args, **kwargs):
    if not self.max_score:
      self.max_score = self.subject.user.grading_scale
    super().save(*args, **kwargs)

  def __str__(self):
    return f"{self.subject.name} - {self.score}/{self.max_score}"


class Exam(models.Model):
  """Scheduled academic assessment used to compute hybrid urgency u_s by remaining days (delta)."""

  EXAM_TYPES = [
      ("oral", "Oral"),
      ("written", "Written"),
      ("practical", "Practical"),
  ]

  subject = models.ForeignKey(
      Subject, on_delete=models.CASCADE, related_name="exams"
  )
  date = models.DateField()
  weight = models.FloatField(default=1.0)
  exam_type = models.CharField(
      max_length=20, choices=EXAM_TYPES, default="written"
  )

  def __str__(self):
    return f"{self.subject.name} - {self.date} ({self.exam_type})"