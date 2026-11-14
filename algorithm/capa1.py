"""CL-CHRONOS - Layer 1: Priority Model and Calculation of Recommended Hours.

Implements normalized academic performance evaluation (a_s), hybrid urgency
(u_s) under the Earliest Deadline First (EDF) principle (Liu & Layland, 1973),
asymmetric multi-criteria Weighted Sum Model (Fishburn, 1967), and piecewise
project workload inflation.
"""

from datetime import date
from capa1.academics.models import Exam, Grade, Subject
from capa1.difficulty.models import SubjectDifficulty
from capa1.projects.models import Project
from capa2.preferences.models import UserPreferences


class Capa1:
    """Layer 1 academic filter: computes discrete priorities p_s in [1, 5]
    and weekly autonomous study demand h_s for core subjects and projects.
    """

    def __init__(self, user):
        self.user = user

        try:
            prefs = UserPreferences.objects.get(user=self.user)
            self.daily_energy_limit = prefs.daily_energy_limit
        except UserPreferences.DoesNotExist:
            self.daily_energy_limit = 100

        self.cognitive_costs = {
            "logic_math": 35.0,
            "creative": 25.0,
            "reading_memory": 20.0,
            "passive": 10.0,
        }

    def calcular_peso_materia(self, subject):
        """Computes discrete priority p_s = min(5, max(1, round(w_s)))
        where w_s = 0.2 * r_s + 0.5 * u_s + 0.3 * d_s.
        """
        grades = Grade.objects.filter(subject=subject, period__is_active=True)
        if grades.exists():
            avg_score = sum(g.score / g.max_score for g in grades) / grades.count()
        else:
            avg_score = 1.0

        if avg_score >= 0.8:
            rendimiento_factor = 1
        elif avg_score >= 0.6:
            rendimiento_factor = 3
        else:
            rendimiento_factor = 5

        urgency_factor = 0

        exams = Exam.objects.filter(subject=subject, date__gte=date.today())
        for exam in exams:
            days_left = (exam.date - date.today()).days
            if days_left <= 3:
                urgency_factor = max(urgency_factor, 5)
            elif days_left <= 7:
                urgency_factor = max(urgency_factor, 3)
            elif days_left <= 14:
                urgency_factor = max(urgency_factor, 1)

        projects = Project.objects.filter(
            subject=subject, status__in=["pending", "in_progress"]
        )
        for p in projects:
            days_left = (p.due_date - date.today()).days
            if days_left < 0:
                continue
            if days_left <= 3:
                urgency_factor = max(
                    urgency_factor, p.priority if p.priority else 5
                )
            elif days_left <= 7:
                urgency_factor = max(urgency_factor, 3)
            elif days_left <= 14:
                urgency_factor = max(urgency_factor, 1)

        try:
            difficulty = subject.difficulty.difficulty_level
        except Exception:
            difficulty = 3

        if avg_score < 0.6:
            urgency_factor = max(urgency_factor, 3)

        peso = (
            (rendimiento_factor * 0.2)
            + (urgency_factor * 0.5)
            + (difficulty * 0.3)
        )
        peso_normalizado = min(max(round(peso), 1), 5)

        return peso_normalizado

    def generar_recomendaciones(self):
        """Generates sorted subject and project study recommendations (subject_analytics)."""
        recomendaciones = []

        subjects = Subject.objects.filter(user=self.user)
        for subject in subjects:
            peso_materia = self.calcular_peso_materia(subject)

            if getattr(subject, "requires_study", True):
                horas_base = peso_materia * 1.5
                horas_proyectos = 1.0
            else:
                horas_base = 0.0
                horas_proyectos = 0.0

            costo_cognitivo = self.cognitive_costs.get(
                subject.cognitive_type, 20.0
            )

            try:
                difficulty = subject.difficulty.difficulty_level
            except Exception:
                difficulty = 3

            min_days = 999
            deadline_type = ""

            exams = Exam.objects.filter(subject=subject, date__gte=date.today())
            for e in exams:
                d = (e.date - date.today()).days
                if d < min_days:
                    min_days = d
                    deadline_type = "Examen"
                horas_proyectos = max(horas_proyectos, 2.0)

            projects = Project.objects.filter(
                subject=subject, status__in=["pending", "in_progress"]
            )
            for p in projects:
                d = (p.due_date - date.today()).days
                if d < min_days and d >= 0:
                    min_days = d
                    deadline_type = "Proyecto"

                if d < 0:
                    continue

                carga_base_proyecto = 1.0 + (difficulty * 0.5)

                if d <= 3:
                    horas_proyectos += carga_base_proyecto * 1.5
                elif d <= 7:
                    horas_proyectos += carga_base_proyecto
                else:
                    horas_proyectos += (carga_base_proyecto / d) * 7

            grades = Grade.objects.filter(
                subject=subject, period__is_active=True
            )
            avg_score = (
                (sum(g.score / g.max_score for g in grades) / grades.count())
                if grades.exists()
                else 1.0
            )

            smart_label = "Bajo Control 🌿"
            risk_level = "low"

            if avg_score < 0.6:
                risk_level = "high"
                smart_label = "Riesgo de Suspenso ⚠️"
            elif min_days <= 3:
                risk_level = "high"
                smart_label = f"{deadline_type} en {min_days} días ⏰"
            elif min_days <= 7:
                risk_level = "medium"
                smart_label = f"{deadline_type} en {min_days} días 📅"
            elif subject.cognitive_type == "logic_math":
                risk_level = "medium"
                smart_label = "Carga Alta 🔥"
            elif subject.cognitive_type == "creative":
                risk_level = "low"
                smart_label = "Fluido 🎨"
            else:
                risk_level = "low"
                smart_label = "Mantenimiento 📚"

            total_horas = round(horas_base + horas_proyectos, 2)

            if total_horas > 0:
                recomendaciones.append({
                    "type": "subject",
                    "id": subject.id,
                    "name": subject.name,
                    "priority": peso_materia,
                    "cognitive_type": subject.cognitive_type,
                    "energy_cost_per_hour": costo_cognitivo,
                    "recommended_hours": total_horas,
                    "smart_label": smart_label,
                    "risk_level": risk_level,
                    "current_average": round(avg_score * 100, 1),
                    "days_until_deadline": min_days if min_days != 999 else None,
                })

        personal_projects = Project.objects.filter(
            user=self.user,
            subject__isnull=True,
            status__in=["pending", "in_progress"],
        )
        for p in personal_projects:
            dias_restantes = (p.due_date - date.today()).days
            if dias_restantes < 0:
                continue

            carga_base_personal = 1.0 + (3 * 0.5)

            if dias_restantes <= 3:
                horas_semanales = carga_base_personal * 1.5
            elif dias_restantes <= 7:
                horas_semanales = carga_base_personal
            else:
                horas_semanales = (carga_base_personal / dias_restantes) * 7

            if dias_restantes <= 3:
                risk_level = "high"
                smart_label = f"Entrega en {dias_restantes} días ⏰"
            elif dias_restantes <= 7:
                risk_level = "medium"
                smart_label = "Semana de Entrega 📅"
            else:
                risk_level = "low"
                smart_label = "Proyecto Activo"

            if horas_semanales > 0:
                recomendaciones.append({
                    "type": "project",
                    "id": p.id,
                    "name": p.name,
                    "priority": p.priority if p.priority else 3,
                    "cognitive_type": "creative",
                    "energy_cost_per_hour": self.cognitive_costs["creative"],
                    "recommended_hours": round(horas_semanales, 2),
                    "smart_label": smart_label,
                    "risk_level": risk_level,
                    "current_average": 100.0,
                    "days_until_deadline": dias_restantes,
                })

        recomendaciones.sort(key=lambda x: x["priority"], reverse=True)
        return recomendaciones