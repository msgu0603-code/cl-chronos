"""CL-CHRONOS Core Orchestrator Engine.

Coordinates the sequential execution of Layer 1 (Academic Filter), Layer 2
(Thermodynamic & Chronobiological Allocation), Layer 3 (Sliding-Window Collision
Resolution), and Layer 4 (Semantic Rendering & XAI Post-Processing).
"""

from algorithm.capa1 import Capa1
from algorithm.capa2 import Capa2
from algorithm.capa3 import Capa3
from algorithm.capa4 import Capa4
from .ia_engine import analizar_estrategia_semanal


class CLChronosEngine:
  """Main execution pipeline for the 4-layer CL-CHRONOS scheduling architecture."""

  def __init__(self, user):
    self.user = user

  def generate_full_schedule(self):
    # 1. Layer 1: Academic Priority & Recommended Hours
    capa1 = Capa1(self.user)
    recomendaciones = capa1.generar_recomendaciones()

    # 2. Layer 2: Thermodynamic & Chronobiological Preliminary Allocation
    capa2 = Capa2(self.user, recomendaciones)
    bloques_preliminares, status_capa2 = capa2.generar_bloques()

    # 3. Layer 3: Biological Friction & Sliding-Window Collision Resolution
    capa3 = Capa3(self.user, bloques_preliminares)
    bloques_aprobados, status_capa3 = capa3.generar_horario_final()

    # 4. Layer 4: Semantic Interpolation & Midnight Carryover
    is_crisis = status_capa2.get("crisis_mode", False)
    capa4 = Capa4(
        self.user, crisis_mode=is_crisis, subject_analytics=recomendaciones
    )
    horario_final = capa4.generar_horario_semanal()

    # 5. Telemetry Compilation & XAI Post-Processing
    horas_faltantes_totales = status_capa2.get("missing_hours", 0.0)
    horas_perdidas_friccion = status_capa3.get("missing_hours", 0.0)

    peak_energy_debt = status_capa2.get("peak_energy_debt", 0.0)
    survival_mode_activations = status_capa2.get("survival_mode_activations", 0)

    warnings = []
    if horas_faltantes_totales > 0:
      warnings.append(
          "CAPACITY_EXCEEDED: El usuario solicitó más horas de estudio de las"
          f" que permite su límite físico temporal (Faltan {horas_faltantes_totales}h)."
      )
    if horas_perdidas_friccion > 0:
      warnings.append(
          f"FRICTION_LOSS: Se perdieron {horas_perdidas_friccion}h debido a"
          " colisiones inamovibles o penalizaciones por descansos pasivos."
      )
    if peak_energy_debt < -80.0:
      warnings.append(
          "CRITICAL_DEBT: El usuario alcanzó niveles de sobrecarga extrema"
          f" ({peak_energy_debt} pts). Riesgo de burnout inminente."
      )
    if survival_mode_activations > 0:
      warnings.append(
          "SURVIVAL_MODE: El motor forzó el algoritmo"
          f" {survival_mode_activations} veces rompiendo reglas de interleaving"
          " o energía para salvar entregas urgentes."
      )

    metrics = {
        "is_perfect_schedule": (
            horas_faltantes_totales == 0 and horas_perdidas_friccion == 0
        ),
        "total_missing_hours": round(horas_faltantes_totales, 2),
        "burnout_prevention_hours": round(
            max(0.0, horas_faltantes_totales - horas_perdidas_friccion), 2
        ),
        "schedule_collision_hours": round(horas_perdidas_friccion, 2),
        "energy_debt_peak": round(peak_energy_debt, 2),
        "survival_mode_activations": survival_mode_activations,
        "crisis_mode_active": is_crisis,
        "warnings": warnings,
    }

    mensaje_ia = analizar_estrategia_semanal(metrics, recomendaciones)
    metrics["ai_insight"] = mensaje_ia

    return {
        "metrics": metrics,
        "schedule": horario_final,
        "subject_analytics": recomendaciones,
    }
