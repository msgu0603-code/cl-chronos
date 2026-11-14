"""CL-CHRONOS - Layer 2: Preliminary Allocation Under Energy and Chronobiological Constraints.

Implements daily capacity protection (C_d), weekly ego-depletion decay
(alpha_d), upper homeostatic saturation E_d(t) <- min(E_d(t), L * alpha_d),
intraday fatigue scaling E_cost(f_c) = delta_t * k_s * (1 + 0.15 * f_c),
two-level microblock degradation, Snap-to-Grid rounding, and interleaved greedy
selection s(b_k) != s(b_{k-1}).
"""

import datetime
from capa2.preferences.models import UserPreferences
from capa3.occupation.models import Occupation
from capa3.routine.models import DailyRoutine
from capa3.schedule.models import ClassSchedule


class Capa2:
    """Layer 2 thermodynamic and chronobiological scheduler."""

    def __init__(self, user, recomendaciones):
        self.user = user
        self.recomendaciones = recomendaciones
        self.peak_energy_debt = 0.0
        self.survival_mode_activations = 0

        try:
            prefs = UserPreferences.objects.get(user=user)
            self.base_block_length = prefs.block_length
            self.break_length = prefs.break_length
            self.daily_energy_limit = prefs.daily_energy_limit
            self.cognitive_mode = prefs.cognitive_mode
            self.preferred_study_time = prefs.preferred_study_time
        except UserPreferences.DoesNotExist:
            self.base_block_length = 60
            self.break_length = 15
            self.daily_energy_limit = 100
            self.cognitive_mode = "balanced"
            self.preferred_study_time = "afternoon"

        if self.cognitive_mode == "crunch_time":
            self.reserva_minima = -50.0
        elif self.cognitive_mode == "recovery":
            self.reserva_minima = self.daily_energy_limit * 0.40
        else:
            self.reserva_minima = 0.0

    def _calc_duration_hours(self, start_t, end_t):
        dt1 = datetime.datetime.combine(datetime.date.min, start_t)
        dt2 = datetime.datetime.combine(datetime.date.min, end_t)
        if end_t < start_t:
            dt2 += datetime.timedelta(days=1)
        return (dt2 - dt1).total_seconds() / 3600.0

    def get_dynamic_block_hours(
        self, cognitive_type, hours_left, degradation_level=0
    ):
        """Adjusts block duration (delta_t) by cognitive profile and degradation level."""
        PISO_MINIMO_HORAS = 0.334  # Minimum operational floor (~20 minutes)

        if 0 < hours_left < PISO_MINIMO_HORAS:
            hours_left = PISO_MINIMO_HORAS

        base_hours = self.base_block_length / 60.0

        if degradation_level == 1:
            return min(0.66, hours_left)
        elif degradation_level == 2:
            return min(0.5, hours_left)

        if cognitive_type == "creative":
            return min(max(1.5, base_hours), hours_left)
        if cognitive_type == "passive":
            return min(max(PISO_MINIMO_HORAS, 0.75), hours_left)

        return min(max(base_hours, PISO_MINIMO_HORAS), hours_left)

    def _compilar_linea_tiempo_fija(self, day_name):
        """Compiles fixed events (classes, occupations, routines) and their energy impacts."""
        timeline = []
        for c in ClassSchedule.objects.filter(
            user=self.user, day_of_week=day_name
        ):
            duracion = self._calc_duration_hours(c.start_time, c.end_time)
            timeline.append({
                "end_time": c.end_time.strftime("%H:%M"),
                "impact": -(duracion * 15.0),
            })

        for o in Occupation.objects.filter(
            user=self.user, day_of_week=day_name
        ):
            timeline.append({
                "end_time": o.end_time.strftime("%H:%M"),
                "impact": -abs(float(o.energy_drain)),
            })

        for r in DailyRoutine.objects.filter(
            user=self.user, day_of_week=day_name
        ):
            factor_recarga = (
                1.5
                if r.recovery_type == "deep"
                else 1.0
                if r.recovery_type == "active"
                else 0.0
            )
            timeline.append({
                "end_time": r.end_time.strftime("%H:%M"),
                "impact": float(r.energy_impact) * factor_recarga,
            })

        timeline.sort(key=lambda x: x["end_time"])
        return timeline

    def generar_bloques(self):
        """Executes greedy interleaved preliminary block allocation across the week."""
        materias_pendientes = []
        horas_totales_semana = 0.0

        for rec in self.recomendaciones:
            if rec.get("recommended_hours", 0) > 0:
                h = float(rec["recommended_hours"])
                horas_totales_semana += h
                materias_pendientes.append({
                    "name": rec["name"],
                    "hours_left": h,
                    "priority": rec.get("priority", 1),
                    "cognitive_type": rec.get(
                        "cognitive_type", "reading_memory"
                    ),
                    "energy_cost_per_hour": rec.get(
                        "energy_cost_per_hour", 20.0
                    ),
                    "smart_label": rec.get("smart_label", ""),
                    "risk_level": rec.get("risk_level", "low"),
                })

        materias_pendientes.sort(key=lambda x: x["priority"], reverse=True)

        dias_semana = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        decay_factors = {
            "Monday": 1.0,
            "Tuesday": 0.95,
            "Wednesday": 0.85,
            "Thursday": 0.80,
            "Friday": 0.70,
            "Saturday": 1.0,
            "Sunday": 1.0,
        }

        avail_data = {}
        for day in dias_semana:
            if day in ["Saturday", "Sunday"]:
                avail_data[day] = [{"start": "08:00", "end": "22:00"}]
            else:
                if self.preferred_study_time == "afternoon":
                    avail_data[day] = [{"start": "14:30", "end": "22:00"}]
                elif self.preferred_study_time == "night":
                    avail_data[day] = [{"start": "18:00", "end": "23:00"}]
                else:
                    avail_data[day] = [{"start": "07:30", "end": "22:00"}]

        bateria_dia = {
            day: self.daily_energy_limit * decay_factors[day]
            for day in dias_semana
        }
        fixed_events_timeline = {
            day: self._compilar_linea_tiempo_fija(day) for day in dias_semana
        }
        ultimo_bloque_dia = {day: None for day in dias_semana}
        fatiga_acumulada_dia = {
            day: {
                "logic_math": 0,
                "reading_memory": 0,
                "creative": 0,
                "passive": 0,
            }
            for day in dias_semana
        }

        horas_estudiadas_dia = {day: 0.0 for day in dias_semana}
        bloques_preliminares = []
        break_hours = self.break_length / 60.0

        def sumar_tiempo(time_str, horas_a_sumar):
            t = datetime.datetime.strptime(time_str, "%H:%M")
            return (t + datetime.timedelta(hours=horas_a_sumar)).strftime(
                "%H:%M"
            )

        def aplicar_fluctuaciones_energia(day_name, hora_limite):
            """Updates E_d(t) and enforces upper saturation E_d(t) <- min(E_d(t), L * alpha_d)."""
            eventos_procesados = []
            for ev in fixed_events_timeline[day_name]:
                if ev["end_time"] <= hora_limite:
                    bateria_dia[day_name] += ev["impact"]
                    if bateria_dia[day_name] < self.peak_energy_debt:
                        self.peak_energy_debt = bateria_dia[day_name]
                    max_cap = self.daily_energy_limit * decay_factors[day_name]
                    if bateria_dia[day_name] > max_cap:
                        bateria_dia[day_name] = max_cap
                    eventos_procesados.append(ev)
            for ev in eventos_procesados:
                fixed_events_timeline[day_name].remove(ev)

        for day in dias_semana:
            carga_externa_hoy = sum(
                self._calc_duration_hours(o.start_time, o.end_time)
                for o in Occupation.objects.filter(
                    user=self.user, day_of_week=day
                )
            ) + sum(
                self._calc_duration_hours(c.start_time, c.end_time)
                for c in ClassSchedule.objects.filter(
                    user=self.user, day_of_week=day
                )
            )

            daily_cap = (horas_totales_semana / 5.0) * 1.2
            if carga_externa_hoy > 5.0:
                daily_cap = 2.0
            if day in ["Saturday", "Sunday"]:
                daily_cap = horas_totales_semana / 3.0

            for slot in avail_data[day]:
                current_time = slot["start"]
                end_limit = slot["end"]

                cambio_en_slot = True
                while cambio_en_slot and any(
                    m["hours_left"] > 0 for m in materias_pendientes
                ):
                    cambio_en_slot = False

                    tiene_criticos = any(
                        mat["priority"] >= 5 and mat["hours_left"] > 0
                        for mat in materias_pendientes
                    )
                    if (
                        horas_estudiadas_dia[day] >= daily_cap
                        and not tiene_criticos
                    ):
                        break

                    candidato = None
                    for m_temp in materias_pendientes:
                        if m_temp["hours_left"] <= 0:
                            continue

                        es_critico_temp = m_temp["priority"] >= 5
                        if (
                            tiene_criticos
                            and not es_critico_temp
                            and m_temp["priority"] < 4
                        ):
                            continue

                        if (
                            ultimo_bloque_dia[day] == m_temp["name"]
                            and not es_critico_temp
                        ):
                            otras_viables = any(
                                other["hours_left"] > 0
                                and other["name"] != m_temp["name"]
                                for other in materias_pendientes
                            )
                            if otras_viables:
                                continue

                        candidato = m_temp
                        break

                    if not candidato:
                        for m_temp in materias_pendientes:
                            if m_temp["hours_left"] > 0:
                                candidato = m_temp
                                break

                    if not candidato:
                        break

                    m = candidato
                    es_critico = m["priority"] >= 5
                    es_alta_prioridad = m["priority"] >= 3
                    reason_code = "STANDARD_ALLOCATION"
                    degradation_level = 0

                    if ultimo_bloque_dia[day] == m["name"]:
                        reason_code = "AUTO_CRUNCH_CRAMMING"

                    aplicar_fluctuaciones_energia(day, current_time)

                    reserva_actual = (
                        -300.0
                        if es_critico
                        else (-150.0 if es_alta_prioridad else -50.0)
                    )

                    actual_block_hours = self.get_dynamic_block_hours(
                        m["cognitive_type"], m["hours_left"], degradation_level
                    )

                    if (
                        horas_estudiadas_dia[day] + actual_block_hours
                        > daily_cap
                    ) and not es_critico:
                        actual_block_hours = (
                            daily_cap - horas_estudiadas_dia[day]
                        )

                    minutos_asignados = round(actual_block_hours * 60)
                    if minutos_asignados < 20:
                        if es_critico:
                            minutos_asignados = 20
                        else:
                            break

                    minutos_asignados = round(minutos_asignados / 10.0) * 10
                    actual_block_hours = minutos_asignados / 60.0

                    multiplicador_fatiga = 1.0 + (
                        0.15 * fatiga_acumulada_dia[day][m["cognitive_type"]]
                    )
                    costo_bloque = (
                        actual_block_hours
                        * m["energy_cost_per_hour"]
                        * multiplicador_fatiga
                    )

                    if (bateria_dia[day] - costo_bloque) < reserva_actual:
                        degradation_level = 1
                        actual_block_hours = self.get_dynamic_block_hours(
                            m["cognitive_type"],
                            m["hours_left"],
                            degradation_level,
                        )

                        minutos_asignados = round(actual_block_hours * 60)
                        if minutos_asignados < 20:
                            if es_critico:
                                minutos_asignados = 20
                            else:
                                continue
                        minutos_asignados = (
                            round(minutos_asignados / 10.0) * 10
                        )
                        actual_block_hours = minutos_asignados / 60.0

                        costo_bloque = (
                            actual_block_hours
                            * m["energy_cost_per_hour"]
                            * multiplicador_fatiga
                        )
                        reason_code = "ENERGY_SAVING_MICROBLOCK"

                        if (
                            bateria_dia[day] - costo_bloque
                        ) < reserva_actual and es_critico:
                            degradation_level = 2
                            actual_block_hours = self.get_dynamic_block_hours(
                                m["cognitive_type"],
                                m["hours_left"],
                                degradation_level,
                            )

                            minutos_asignados = round(actual_block_hours * 60)
                            if minutos_asignados < 20:
                                minutos_asignados = 20
                            minutos_asignados = (
                                round(minutos_asignados / 10.0) * 10
                            )
                            actual_block_hours = minutos_asignados / 60.0

                            costo_bloque = (
                                actual_block_hours
                                * m["energy_cost_per_hour"]
                                * multiplicador_fatiga
                            )
                            reason_code = "CRITICAL_SURVIVAL_CRAM"
                        elif (bateria_dia[day] - costo_bloque) < reserva_actual:
                            continue

                    end_time = sumar_tiempo(current_time, actual_block_hours)

                    if not es_critico and not es_alta_prioridad:
                        if current_time >= "22:00" or (
                            end_time > "21:00"
                            and m["cognitive_type"] == "logic_math"
                        ):
                            continue

                    if end_time <= end_limit:
                        bloques_preliminares.append({
                            "day": day,
                            "start": current_time,
                            "end": end_time,
                            "subject": m["name"],
                            "cognitive_type": m["cognitive_type"],
                            "reason_code": reason_code,
                            "smart_label": m.get("smart_label"),
                            "risk_level": m.get("risk_level"),
                        })

                        start_break = end_time
                        break_duration = (
                            5.0 / 60.0
                            if reason_code == "CRITICAL_SURVIVAL_CRAM"
                            else break_hours
                        )
                        end_break = sumar_tiempo(start_break, break_duration)

                        if end_break <= end_limit:
                            bloques_preliminares.append({
                                "day": day,
                                "start": start_break,
                                "end": end_break,
                                "subject": "Break",
                            })
                            current_time = end_break
                        else:
                            current_time = end_limit

                        m["hours_left"] -= actual_block_hours
                        horas_estudiadas_dia[day] += actual_block_hours
                        ultimo_bloque_dia[day] = m["name"]
                        bateria_dia[day] -= costo_bloque
                        fatiga_acumulada_dia[day][m["cognitive_type"]] += 1

                        if bateria_dia[day] < self.peak_energy_debt:
                            self.peak_energy_debt = bateria_dia[day]
                        if reason_code in [
                            "AUTO_CRUNCH_CRAMMING",
                            "ENERGY_SAVING_MICROBLOCK",
                            "CRITICAL_SURVIVAL_CRAM",
                        ]:
                            self.survival_mode_activations += 1

                        cambio_en_slot = True
                    else:
                        break

        horas_restantes = sum(
            max(0.0, m["hours_left"]) for m in materias_pendientes
        )
        status_capa2 = {
            "fulfilled": horas_restantes <= 0,
            "missing_hours": round(horas_restantes, 2),
            "final_battery_status": {
                day: round(bateria, 2) for day, bateria in bateria_dia.items()
            },
            "peak_energy_debt": round(self.peak_energy_debt, 2),
            "survival_mode_activations": self.survival_mode_activations,
            "crisis_mode": horas_restantes > 0 or self.peak_energy_debt < -80.0,
        }

        return bloques_preliminares, status_capa2