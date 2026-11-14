"""CL-CHRONOS - Layer 4: Semantic Rendering and Temporal Carryover.

Implements midnight carryover for transitional events (t_end < t_start),
semantic gap interpolation (Rest & Sleep, Morning Routine / Prep, Break /
Decompression, Adaptive Slot / Flex Time), monotonic time pointer advancing
for simultaneous nested events, and proactive circadian closure.
"""

import datetime
from capa2.planner.models import StudyPlan, StudySession
from capa3.occupation.models import Occupation
from capa3.routine.models import DailyRoutine
from capa3.schedule.models import ClassSchedule


class Capa4:
  """Layer 4 semantic translation and chronological consolidation engine."""

  def __init__(self, user, crisis_mode=False, subject_analytics=None):
    self.user = user
    self.crisis_mode = crisis_mode
    self.subject_analytics = subject_analytics or []
    self.dias_semana = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    self.cognitive_costs = {
        "logic_math": -35.0,
        "creative": -25.0,
        "reading_memory": -20.0,
        "passive": -10.0,
    }

  def generar_horario_semanal(self):
    """Consolidates all fixed and scheduled blocks into a continuous 24h timeline per day."""
    horario_completo = {dia: [] for dia in self.dias_semana}

    try:
      plan_estudio = StudyPlan.objects.get(user=self.user)
      sesiones = StudySession.objects.select_related("subject").filter(
          study_plan=plan_estudio
      )
    except StudyPlan.DoesNotExist:
      sesiones = []

    clases = ClassSchedule.objects.select_related("subject").filter(
        user=self.user
    )
    rutinas_diarias = DailyRoutine.objects.filter(user=self.user)
    ocupaciones = Occupation.objects.filter(user=self.user)

    for dia in self.dias_semana:
      eventos_del_dia = []

      # 1. Midnight Carryover from the preceding day (t_end < t_start)
      idx = self.dias_semana.index(dia)
      dia_anterior = self.dias_semana[idx - 1]

      for c in clases.filter(day_of_week=dia_anterior):
        if c.end_time < c.start_time:
          nombre_clase = c.subject.name if c.subject else "Clase General"
          eventos_del_dia.append({
              "type": "class",
              "title": f"Clase: {nombre_clase}",
              "start": datetime.time(0, 0),
              "end": c.end_time,
              "cognitive_type": "passive",
              "energy_impact_per_hour": -15.0,
              "reason_code": "FIXED_SCHEDULE",
          })

      for r in rutinas_diarias.filter(day_of_week=dia_anterior):
        if r.end_time < r.start_time:
          if r.recovery_type == "passive":
            cog_type = "draining"
            titulo = f"Overstimulation: {r.get_activity_type_display()}"
            impacto = 0.0
            reason = "DOPAMINE_SATURATION_DETECTED"
          elif r.recovery_type == "deep":
            cog_type = "recovery"
            titulo = f"Deep Reset: {r.get_activity_type_display()}"
            impacto = float(r.energy_impact) * 1.5
            reason = "DEEP_COGNITIVE_RESET"
          else:
            cog_type = "recovery"
            titulo = r.get_activity_type_display().capitalize()
            impacto = float(r.energy_impact)
            reason = "ACTIVE_RECOVERY"

          eventos_del_dia.append({
              "type": "routine",
              "title": titulo,
              "start": datetime.time(0, 0),
              "end": r.end_time,
              "cognitive_type": cog_type,
              "energy_impact_per_hour": impacto,
              "reason_code": reason,
          })

      for o in ocupaciones.filter(day_of_week=dia_anterior):
        if o.end_time < o.start_time:
          eventos_del_dia.append({
              "type": "occupation",
              "title": o.description,
              "start": datetime.time(0, 0),
              "end": o.end_time,
              "cognitive_type": "draining",
              "energy_impact_per_hour": -abs(float(o.energy_drain)),
              "reason_code": "FIXED_OCCUPATION",
          })

      # 2. Current Day Events (Study Sessions, Classes, Routines, Occupations)
      if sesiones:
        for s in sesiones.filter(day_of_week=dia):
          cog_type = (
              s.subject.cognitive_type if s.subject else "reading_memory"
          )
          s_analytics = next(
              (
                  item
                  for item in self.subject_analytics
                  if item["name"] == s.subject.name
              ),
              {},
          )
          smart_label = s_analytics.get("smart_label", "")
          risk_level = s_analytics.get("risk_level", "low")

          eventos_del_dia.append({
              "type": "study",
              "title": f"Estudio: {s.subject.name}",
              "start": s.start_time,
              "end": s.end_time,
              "cognitive_type": cog_type,
              "energy_impact_per_hour": self.cognitive_costs.get(
                  cog_type, -20.0
              ),
              "reason_code": getattr(s, "reason_code", "STANDARD_ALLOCATION"),
              "smart_label": smart_label,
              "risk_level": risk_level,
          })

      for c in clases.filter(day_of_week=dia):
        nombre_clase = c.subject.name if c.subject else "Clase General"
        eventos_del_dia.append({
            "type": "class",
            "title": f"Clase: {nombre_clase}",
            "start": c.start_time,
            "end": c.end_time,
            "cognitive_type": "passive",
            "energy_impact_per_hour": -15.0,
            "reason_code": "FIXED_SCHEDULE",
        })

      for r in rutinas_diarias.filter(day_of_week=dia):
        if r.recovery_type == "passive":
          cog_type = "draining"
          titulo = f"Overstimulation: {r.get_activity_type_display()}"
          impacto = 0.0
          reason = "DOPAMINE_SATURATION_DETECTED"
        elif r.recovery_type == "deep":
          cog_type = "recovery"
          titulo = f"Deep Reset: {r.get_activity_type_display()}"
          impacto = float(r.energy_impact) * 1.5
          reason = "DEEP_COGNITIVE_RESET"
        else:
          cog_type = "recovery"
          titulo = r.get_activity_type_display().capitalize()
          impacto = float(r.energy_impact)
          reason = "ACTIVE_RECOVERY"

        eventos_del_dia.append({
            "type": "routine",
            "title": titulo,
            "start": r.start_time,
            "end": r.end_time,
            "cognitive_type": cog_type,
            "energy_impact_per_hour": impacto,
            "reason_code": reason,
        })

      for o in ocupaciones.filter(day_of_week=dia):
        eventos_del_dia.append({
            "type": "occupation",
            "title": o.description,
            "start": o.start_time,
            "end": o.end_time,
            "cognitive_type": "draining",
            "energy_impact_per_hour": -abs(float(o.energy_drain)),
            "reason_code": "FIXED_OCCUPATION",
        })

      tuple_events = [tuple(e.items()) for e in eventos_del_dia]
      unique_tuple_events = list(dict.fromkeys(tuple_events))
      eventos_del_dia = [dict(t) for t in unique_tuple_events]
      eventos_del_dia.sort(key=lambda x: x["start"])

      # 3. Semantic Interpolation and Intelligent Gap Filling
      horario_final_dia = []
      tiempo_actual = datetime.time(0, 0)
      dia_iniciado_productivamente = False

      for evento in eventos_del_dia:
        if tiempo_actual < evento["start"]:
          dt_actual = datetime.datetime.combine(
              datetime.date.today(), tiempo_actual
          )
          dt_evento = datetime.datetime.combine(
              datetime.date.today(), evento["start"]
          )
          duracion_minutos = (dt_evento - dt_actual).total_seconds() / 60.0

          if tiempo_actual.hour < 6:
            titulo_bloque = "Rest & Sleep"
            tipo = "sleep"
            recarga_hora = 15.0
            reason = "CIRCADIAN_REST"
          elif (
              tiempo_actual.hour < 10
              and duracion_minutos <= 90
              and not dia_iniciado_productivamente
          ):
            titulo_bloque = "Morning Routine / Prep"
            tipo = "routine"
            recarga_hora = 5.0
            reason = "MORNING_PREP"
          else:
            if duracion_minutos <= 45:
              titulo_bloque = "Break / Decompression"
              tipo = "recovery"
              recarga_hora = 10.0
              reason = "BUFFER_MAINTENANCE"
            else:
              titulo_bloque = "Adaptive Slot / Flex Time"
              tipo = "adaptive_slot"
              recarga_hora = 5.0
              reason = "AVAILABLE_FOR_GAMIFICATION"

          horario_final_dia.append({
              "type": tipo,
              "title": titulo_bloque,
              "start": tiempo_actual.strftime("%H:%M"),
              "end": evento["start"].strftime("%H:%M"),
              "cognitive_type": (
                  "recovery" if tipo in ["sleep", "recovery"] else "passive"
              ),
              "energy_impact_per_hour": recarga_hora,
              "reason_code": reason,
          })

        evento_json = evento.copy()
        evento_json["start"] = evento["start"].strftime("%H:%M")

        if evento["end"] < evento["start"]:
          evento_json["end"] = "24:00"
          tiempo_actual = datetime.time(23, 59, 59)
        else:
          evento_json["end"] = evento["end"].strftime("%H:%M")
          # Monotonic pointer update: prevents nested simultaneous events (e.g., Meal inside Paper)
          # from moving the timeline cursor backward.
          tiempo_actual = max(tiempo_actual, evento["end"])

        horario_final_dia.append(evento_json)

        if evento["type"] in ["study", "class", "occupation"]:
          dia_iniciado_productivamente = True

      # 4. Circadian Closure and Nighttime Cognitive Wind-Down
      if tiempo_actual < datetime.time(23, 59):
        hora_dormir = datetime.time(22, 30)
        hora_winddown = datetime.time(21, 45)

        if tiempo_actual < hora_winddown:
          horario_final_dia.append({
              "type": "adaptive_slot",
              "title": "Evening Flex / Decompression",
              "start": tiempo_actual.strftime("%H:%M"),
              "end": hora_winddown.strftime("%H:%M"),
              "cognitive_type": "passive",
              "energy_impact_per_hour": 10.0,
              "reason_code": "AVAILABLE_FOR_GAMIFICATION",
          })
          horario_final_dia.append({
              "type": "recovery",
              "title": "Wind-down / Sleep Prep",
              "start": hora_winddown.strftime("%H:%M"),
              "end": hora_dormir.strftime("%H:%M"),
              "cognitive_type": "recovery",
              "energy_impact_per_hour": 10.0,
              "reason_code": "CIRCADIAN_WIND_DOWN",
          })
          horario_final_dia.append({
              "type": "sleep",
              "title": "Rest & Sleep",
              "start": hora_dormir.strftime("%H:%M"),
              "end": "24:00",
              "cognitive_type": "recovery",
              "energy_impact_per_hour": 15.0,
              "reason_code": "CIRCADIAN_REST",
          })
        elif tiempo_actual < hora_dormir:
          horario_final_dia.append({
              "type": "recovery",
              "title": "Wind-down / Sleep Prep",
              "start": tiempo_actual.strftime("%H:%M"),
              "end": hora_dormir.strftime("%H:%M"),
              "cognitive_type": "recovery",
              "energy_impact_per_hour": 10.0,
              "reason_code": "CIRCADIAN_WIND_DOWN",
          })
          horario_final_dia.append({
              "type": "sleep",
              "title": "Rest & Sleep",
              "start": hora_dormir.strftime("%H:%M"),
              "end": "24:00",
              "cognitive_type": "recovery",
              "energy_impact_per_hour": 15.0,
              "reason_code": "CIRCADIAN_REST",
          })
        else:
          dt_actual = datetime.datetime.combine(
              datetime.date.today(), tiempo_actual
          )
          dt_winddown_express = dt_actual + datetime.timedelta(minutes=15)

          if dt_winddown_express.time() < datetime.time(23, 59):
            horario_final_dia.append({
                "type": "recovery",
                "title": "Quick Wind-down",
                "start": tiempo_actual.strftime("%H:%M"),
                "end": dt_winddown_express.time().strftime("%H:%M"),
                "cognitive_type": "recovery",
                "energy_impact_per_hour": 10.0,
                "reason_code": "EXPRESS_WIND_DOWN",
            })
            horario_final_dia.append({
                "type": "sleep",
                "title": "Rest & Sleep",
                "start": dt_winddown_express.time().strftime("%H:%M"),
                "end": "24:00",
                "cognitive_type": "recovery",
                "energy_impact_per_hour": 15.0,
                "reason_code": "CIRCADIAN_REST",
            })
          else:
            horario_final_dia.append({
                "type": "sleep",
                "title": "Rest & Sleep",
                "start": tiempo_actual.strftime("%H:%M"),
                "end": "24:00",
                "cognitive_type": "recovery",
                "energy_impact_per_hour": 15.0,
                "reason_code": "CIRCADIAN_REST",
            })

      horario_completo[dia] = horario_final_dia

    return horario_completo