"""CL-CHRONOS - Layer 3: Collision Resolution and Biological Friction.

Implements the sliding window collision detector, biological friction buffers
(beta in {l_br, l_dec}) for task-switching costs (Monsell, 2003; Pinedo, 2016),
hard circadian wind-down cutoff at 21:00 for logical-mathematical tasks
(Schmidt et al., 2007), and the Midnight Invariance Rule (minute 1439).
"""

import datetime
from capa1.academics.models import Subject
from capa1.projects.models import Project
from capa2.planner.models import StudyPlan, StudySession
from capa2.preferences.models import UserPreferences
from capa3.occupation.models import Occupation
from capa3.routine.models import DailyRoutine
from capa3.schedule.models import ClassSchedule


class Capa3:
  """Layer 3 sliding-window collision resolver and database persistence layer."""

  def __init__(self, user, bloques_preliminares):
    self.user = user
    self.bloques_preliminares = bloques_preliminares

    try:
      prefs = UserPreferences.objects.get(user=self.user)
      self.base_break_minutes = prefs.break_length
      self.decompression_minutes = prefs.decompression_buffer
    except UserPreferences.DoesNotExist:
      self.base_break_minutes = 15
      self.decompression_minutes = 30

  def generar_horario_final(self):
    """Positions preliminary blocks into domain T = {0, ..., 1439} without overlaps."""
    plan_estudio, _ = StudyPlan.objects.get_or_create(user=self.user)
    StudySession.objects.filter(study_plan=plan_estudio).delete()

    clases = ClassSchedule.objects.filter(user=self.user)
    rutinas_diarias = DailyRoutine.objects.filter(user=self.user)
    ocupaciones = Occupation.objects.filter(user=self.user)

    decompression_delta = datetime.timedelta(minutes=self.decompression_minutes)
    standard_break_delta = datetime.timedelta(minutes=self.base_break_minutes)

    bloques_aprobados = []
    bloques_aprobados_por_dia = {
        d: []
        for d in [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
    }
    horas_perdidas = 0.0

    def to_time(t_str):
      if isinstance(t_str, datetime.time):
        return t_str
      return datetime.datetime.strptime(t_str, "%H:%M").time()

    def sumar_tiempo_time(t_obj, delta):
      t_datetime = datetime.datetime.combine(datetime.date.today(), t_obj)
      t_final = t_datetime + delta
      if t_final.date() > t_datetime.date():
        return datetime.time(23, 59, 59)
      return t_final.time()

    def check_collision(s1, e1, s2, e2, current_start, buffer_delta):
      """Detects interval overlap and shifts start time to t_end^{collision} + beta."""
      e2_buffered = sumar_tiempo_time(e2, buffer_delta)

      if s2 >= e2:  # Event crosses midnight boundary
        overlap = (e1 > s2) or (s1 < e2)
      else:
        overlap = not (e1 <= s2 or s1 >= e2)

      if overlap:
        if e2_buffered <= current_start or e2_buffered < s2:
          return True, datetime.time(23, 59, 59)
        return True, e2_buffered
      return False, current_start

    for bloque in self.bloques_preliminares:
      if bloque.get("subject") == "Break":
        continue

      b_day = bloque["day"]
      b_start = to_time(bloque["start"])

      duracion_horas = (
          datetime.datetime.combine(datetime.date.min, to_time(bloque["end"]))
          - datetime.datetime.combine(datetime.date.min, b_start)
      ).total_seconds() / 3600.0

      duracion_delta = datetime.timedelta(hours=duracion_horas)
      cognitive_type = bloque.get("cognitive_type", "reading_memory")

      current_start = b_start
      placed = False

      while current_start.hour < 23 and current_start != datetime.time(
          23, 59, 59
      ):
        current_end = sumar_tiempo_time(current_start, duracion_delta)

        # Hard Circadian Protection Constraint (Wind-Down at 21:00 for logic_math)
        if (
            current_end > datetime.time(21, 0)
            and cognitive_type == "logic_math"
            and bloque.get("reason_code") != "AUTO_CRUNCH_CRAMMING"
        ):
          break

        colision_detectada = False

        # 1. Collisions with Fixed Occupations (beta = l_dec = 30 min)
        for o in ocupaciones.filter(day_of_week=b_day):
          colision_detectada, current_start = check_collision(
              current_start,
              current_end,
              o.start_time,
              o.end_time,
              current_start,
              decompression_delta,
          )
          if colision_detectada:
            break
        if colision_detectada:
          continue

        # 2. Collisions with Academic Classes (beta = l_dec = 30 min)
        for c in clases.filter(day_of_week=b_day):
          colision_detectada, current_start = check_collision(
              current_start,
              current_end,
              c.start_time,
              c.end_time,
              current_start,
              decompression_delta,
          )
          if colision_detectada:
            break
        if colision_detectada:
          continue

        # 3. Collisions with Biological Routines (beta = l_dec for passive, l_br for active/deep)
        for r in rutinas_diarias.filter(day_of_week=b_day):
          if r.recovery_type == "passive":
            friccion_delta = decompression_delta
          else:
            friccion_delta = standard_break_delta

          colision_detectada, current_start = check_collision(
              current_start,
              current_end,
              r.start_time,
              r.end_time,
              current_start,
              friccion_delta,
          )
          if colision_detectada:
            break
        if colision_detectada:
          continue

        # 4. Collisions with Previously Approved Study Blocks (beta = l_br = 15 min)
        for ap in bloques_aprobados_por_dia[b_day]:
          colision_detectada, current_start = check_collision(
              current_start,
              current_end,
              ap["start"],
              ap["end"],
              current_start,
              standard_break_delta,
          )
          if colision_detectada:
            break
        if colision_detectada:
          continue

        # Viable slot found: resolve Subject or independent personal Project
        subject_instance = Subject.objects.filter(
            name=bloque["subject"], user=self.user
        ).first()

        if not subject_instance:
          personal_proj = Project.objects.filter(
              name=bloque["subject"],
              user=self.user,
              subject__isnull=True,
          ).first()
          if personal_proj:
            subject_instance, _ = Subject.objects.get_or_create(
                name=bloque["subject"],
                user=self.user,
                defaults={
                    "cognitive_type": cognitive_type,
                    "requires_study": False,
                },
            )
          else:
            break

        StudySession.objects.create(
            study_plan=plan_estudio,
            subject=subject_instance,
            day_of_week=b_day,
            start_time=current_start,
            end_time=current_end,
            reason_code=bloque.get("reason_code", "STANDARD_ALLOCATION"),
        )

        nuevo_bloque_aprobado = {
            "day": b_day,
            "start": current_start,
            "end": current_end,
            "subject": bloque["subject"],
            "cognitive_type": cognitive_type,
            "reason_code": bloque.get("reason_code", "STANDARD_ALLOCATION"),
            "smart_label": bloque.get("smart_label"),
            "risk_level": bloque.get("risk_level"),
        }
        bloques_aprobados.append(nuevo_bloque_aprobado)
        bloques_aprobados_por_dia[b_day].append(nuevo_bloque_aprobado)
        placed = True
        break

      if not placed:
        horas_perdidas += duracion_horas

    status_capa3 = {
        "fulfilled": horas_perdidas == 0.0,
        "missing_hours": round(horas_perdidas, 2),
    }

    return bloques_aprobados, status_capa3