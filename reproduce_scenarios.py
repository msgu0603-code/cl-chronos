#!/usr/bin/env python
"""CL-CHRONOS: In Silico Benchmark Verification Script.

Inserts only the raw student input profiles (grades, assessment dates, sleep
routines, and fixed class/work schedules) into the database and executes
CLChronosEngine to compute all priorities, study blocks, friction buffers, and
thermodynamic metrics from scratch.
"""

from datetime import date, timedelta
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cl_chronos.settings")
django.setup()

from django.contrib.auth import get_user_model
from capa1.academics.models import AcademicPeriod, Subject, Grade, Exam
from capa1.projects.models import Project
from capa2.preferences.models import UserPreferences
from capa3.schedule.models import ClassSchedule
from capa3.occupation.models import Occupation
from capa3.routine.models import DailyRoutine
from algorithm.engine import CLChronosEngine

User = get_user_model()
TODAY = date.today()
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
ALL_DAYS = WEEKDAYS + ["Saturday", "Sunday"]


def create_base_student(username, age, user_type="student"):
    """Creates a clean student user and default Layer 2 base preferences."""
    User.objects.filter(username=username).delete()
    user = User.objects.create_user(
        username=username,
        email=f"{username}@cl-chronos.org",
        password="benchmark_pass_123",
        first_name=username.capitalize(),
        last_name="Student",
        age=age,
        school_year="University",
        grading_scale=10.0,
        user_type=user_type,
    )
    UserPreferences.objects.create(user=user)
    period = AcademicPeriod.objects.create(
        user=user, name="Active Term", is_active=True
    )
    return user, period


def setup_scenario_a():
    """Inputs for Scenario A: 19yo student, 2 subjects, light class load."""
    user, period = create_base_student("scenario_a", age=19)

    for d in ALL_DAYS:
        DailyRoutine.objects.create(
            user=user,
            activity_type="sleep",
            day_of_week=d,
            start_time="23:00",
            end_time="07:00",
            recovery_type="deep",
            energy_impact=7.5,
        )

    s1 = Subject.objects.create(
        user=user,
        name="Cálculo Vectorial",
        cognitive_type="logic_math",
        requires_study=True,
    )
    Grade.objects.create(
        subject=s1, period=period, score=9.0, max_score=10.0, date=TODAY
    )
    Exam.objects.create(subject=s1, date=TODAY + timedelta(days=30))

    for d in ["Monday", "Wednesday"]:
        ClassSchedule.objects.create(
            user=user,
            subject=s1,
            day_of_week=d,
            start_time="09:00",
            end_time="11:00",
        )

    s2 = Subject.objects.create(
        user=user,
        name="Historia de la Ciencia",
        cognitive_type="reading_memory",
        requires_study=True,
    )
    Grade.objects.create(
        subject=s2, period=period, score=8.5, max_score=10.0, date=TODAY
    )
    Exam.objects.create(subject=s2, date=TODAY + timedelta(days=21))

    return user


def setup_scenario_b():
    """Inputs for Scenario B: 23yo working student, 6h daily work + 2h daily classes."""
    user, period = create_base_student("scenario_b", age=23, user_type="worker")

    for d in ALL_DAYS:
        DailyRoutine.objects.create(
            user=user,
            activity_type="sleep",
            day_of_week=d,
            start_time="23:00",
            end_time="06:30",
            recovery_type="deep",
            energy_impact=7.5,
        )

    s1 = Subject.objects.create(
        user=user,
        name="Arquitectura de Software",
        cognitive_type="logic_math",
        requires_study=True,
    )
    Grade.objects.create(
        subject=s1, period=period, score=7.2, max_score=10.0, date=TODAY
    )
    Project.objects.create(
        user=user,
        subject=s1,
        name="Entrega Arquitectura",
        due_date=TODAY + timedelta(days=3),
        priority=3,
        status="in_progress",
    )

    s2 = Subject.objects.create(
        user=user,
        name="Diseño de Interfaces (UI/UX)",
        cognitive_type="creative",
        requires_study=True,
    )
    Grade.objects.create(
        subject=s2, period=period, score=7.8, max_score=10.0, date=TODAY
    )
    Exam.objects.create(subject=s2, date=TODAY + timedelta(days=9))

    for d in WEEKDAYS:
        Occupation.objects.create(
            user=user,
            description="Desarrollador Junior (Medio Tiempo)",
            day_of_week=d,
            start_time="08:00",
            end_time="14:00",
            energy_drain=-15,
        )
    for d in ["Monday", "Wednesday", "Friday"]:
        ClassSchedule.objects.create(
            user=user,
            subject=s1,
            day_of_week=d,
            start_time="15:00",
            end_time="17:00",
        )
    for d in ["Tuesday", "Thursday"]:
        ClassSchedule.objects.create(
            user=user,
            subject=s2,
            day_of_week=d,
            start_time="15:00",
            end_time="17:00",
        )

    return user


def setup_scenario_c():
    """Inputs for Scenario C: 21yo student in finals week (delta = 0) with failing grades (< 6.0)."""
    user, period = create_base_student("scenario_c", age=21)

    for d in ALL_DAYS:
        DailyRoutine.objects.create(
            user=user,
            activity_type="sleep",
            day_of_week=d,
            start_time="22:30",
            end_time="06:30",
            recovery_type="deep",
            energy_impact=7.5,
        )

    s1 = Subject.objects.create(
        user=user,
        name="Física Cuántica",
        cognitive_type="logic_math",
        requires_study=True,
    )
    Grade.objects.create(
        subject=s1, period=period, score=4.5, max_score=10.0, date=TODAY
    )
    Exam.objects.create(subject=s1, date=TODAY)
    for i in range(2):
        Project.objects.create(
            user=user,
            subject=s1,
            name=f"Proyecto Cuántica {i+1}",
            due_date=TODAY,
            priority=5,
            status="in_progress",
        )

    s2 = Subject.objects.create(
        user=user,
        name="Ecuaciones Diferenciales",
        cognitive_type="logic_math",
        requires_study=True,
    )
    Grade.objects.create(
        subject=s2, period=period, score=5.0, max_score=10.0, date=TODAY
    )
    Exam.objects.create(subject=s2, date=TODAY)
    Project.objects.create(
        user=user,
        subject=s2,
        name="Proyecto EDO",
        due_date=TODAY,
        priority=5,
        status="in_progress",
    )

    s3 = Subject.objects.create(
        user=user,
        name="Modelado Computacional",
        cognitive_type="creative",
        requires_study=True,
    )
    Grade.objects.create(
        subject=s3, period=period, score=5.5, max_score=10.0, date=TODAY
    )
    for i in range(2):
        Project.objects.create(
            user=user,
            subject=s3,
            name=f"Simulación {i+1}",
            due_date=TODAY,
            priority=3,
            status="in_progress",
        )

    for d in ["Monday", "Tuesday"]:
        ClassSchedule.objects.create(
            user=user,
            subject=s1,
            day_of_week=d,
            start_time="08:00",
            end_time="14:00",
        )
    for d in ["Wednesday", "Thursday"]:
        ClassSchedule.objects.create(
            user=user,
            subject=s2,
            day_of_week=d,
            start_time="08:00",
            end_time="14:00",
        )
    ClassSchedule.objects.create(
        user=user,
        subject=s3,
        day_of_week="Friday",
        start_time="08:00",
        end_time="14:00",
    )

    for d in WEEKDAYS:
        Occupation.objects.create(
            user=user,
            description="Prácticas de Laboratorio",
            day_of_week=d,
            start_time="15:00",
            end_time="18:00",
            energy_drain=-15,
        )

    return user


def main():
    print("=" * 76)
    print("CL-CHRONOS: Live 4-Layer Algorithmic Execution from Raw Input Data")
    print("=" * 76)

    scenarios = [
        ("SCENARIO A (Cognitive Leeway)", setup_scenario_a()),
        ("SCENARIO B (Workload Saturation)", setup_scenario_b()),
        ("SCENARIO C (Acute Crisis)", setup_scenario_c()),
    ]

    for title, user in scenarios:
        output = CLChronosEngine(user).generate_full_schedule()
        m = output["metrics"]
        analytics = output["subject_analytics"]
        schedule = output["schedule"]

        study_blocks_count = sum(
            1
            for day_events in schedule.values()
            for ev in day_events
            if ev["type"] == "study"
        )
        recommended_total = sum(s["recommended_hours"] for s in analytics)
        assigned_total = recommended_total - m["total_missing_hours"]

        print(f"\n▶ {title}")
        print("  [Layer 1 Output - Computed Priorities & Demand]")
        for s in analytics:
            print(
                f"    • {s['name']}: p_s = {s['priority']} | h_s ="
                f" {s['recommended_hours']:.2f} h ({s['smart_label']})"
            )

        print("  [Layers 2-4 Output - Exported Telemetry Metrics]")
        print(
            f"    • Total study blocks scheduled : {study_blocks_count} blocks"
        )
        print(f"    • Recommended weekly demand    : {recommended_total:.2f} h")
        print(f"    • Hours effectively assigned   : {assigned_total:.2f} h")
        print(
            "    • Hours pruned for protection  :"
            f" {m['burnout_prevention_hours']:.2f} h"
        )
        print(
            "    • Hours lost to collisions     :"
            f" {m['schedule_collision_hours']:.2f} h"
        )
        print(
            f"    • Peak energy debt             : {m['energy_debt_peak']:.2f} pts"
        )
        print(
            "    • Urgency maneuvers (survival) :"
            f" {m['survival_mode_activations']}"
        )
        print(f"    • Crisis state active          : {m['crisis_mode_active']}")
        print(
            f"    • Global compliance            : {m['is_perfect_schedule']}"
        )

    print("\n" + "=" * 76)


if __name__ == "__main__":
    main()