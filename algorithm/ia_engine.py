"""CL-CHRONOS - Layer 4: Tele-Strategic Translation via Generative AI (XAI Module).

Operates strictly as an explainability module (Barredo Arrieta et al., 2020)
that translates scalar telemetry indicators (peak_energy_debt,
total_missing_hours, survival_mode_activations) and computed subject priorities
into a natural-language executive summary (ai_insight).
"""

import json
import os
import requests


def obtener_instruccion_idioma(idioma):
  if idioma == 'es':
    return (
        'El usuario habla español nativo. No traduzcas, escribe de forma'
        ' natural.'
    )

  nombres_idiomas = {'en': 'English (US)', 'ja': 'Japanese (日本語)'}
  idioma_nombre = nombres_idiomas.get(idioma, 'English')

  return (
      "\n\n[EXTREME PENALTY INSTRUCTION: The user's system language is strictly"
      f' set to {idioma_nombre}. YOU MUST GENERATE ALL TEXT VALUES IN THE JSON'
      f' EXCLUSIVELY IN {idioma_nombre}. Translate all internal context'
      f' naturally to {idioma_nombre}. DO NOT mention that you translated the'
      ' text.]\n\n'
  )


def analizar_estrategia_semanal(metrics, analytics, idioma='es'):
  """Translates CL-CHRONOS telemetry and priorities into the ai_insight executive summary."""
  api_key = os.environ.get('DEEPSEEK_API_KEY')

  fallback_json = {
      'estrategia_global': (
          'Schedule optimized successfully. Your biological energy is'
          ' protected. Trust the system.'
      ),
      'tacticas_clave': [{
          'icono': 'shield',
          'color': 'teal',
          'titulo': 'SYSTEM ONLINE',
          'descripcion': (
              'Blocks calculated and aligned with your recovery preferences.'
          ),
      }],
  }

  if not api_key:
    return fallback_json

  url = 'https://api.deepseek.com/chat/completions'
  headers = {
      'Content-Type': 'application/json',
      'Authorization': f'Bearer {api_key}',
  }

  missing_hours = metrics.get('total_missing_hours', 0)
  peak_debt = metrics.get('energy_debt_peak', 0)
  survival_activations = metrics.get('survival_mode_activations', 0)

  materias_ordenadas = sorted(
      analytics,
      key=lambda x: (
          x.get('risk_level') != 'high',
          x.get('current_average', 100),
      ),
  )
  peor_materia = (
      materias_ordenadas[0]['name'] if materias_ordenadas else 'classes'
  )
  riesgo_peor = (
      materias_ordenadas[0].get('smart_label', '') if materias_ordenadas else ''
  )

  materias_criticas = [
      f"{m['name']}"
      for m in analytics
      if m.get('priority', 0) >= 3 or m.get('risk_level') == 'high'
  ]
  contexto_materias = (
      ', '.join(materias_criticas) if materias_criticas else 'Stable.'
  )

  if missing_hours > 0:
    estado_real = (
        'CRITICAL (Overload. Hours forcefully discarded to protect biology).'
    )
  elif survival_activations > 0:
    estado_real = 'TENSE (Schedule fit, but required urgency adjustments).'
  else:
    estado_real = 'SMOOTH (Stable thermodynamic week. Zero cuts).'

  prompt = f"""
    You are the "Core Strategist" of the CL-CHRONOS system. Explain to the user HOW and WHY you organized their week.

    SYSTEM TELEMETRY:
    - Status: {estado_real}
    - Weakest subject detected: {peor_materia} ({riesgo_peor}).
    - Hours discarded due to biological limit: {missing_hours}h.
    - Energy debt peak: {peak_debt} pts.
    - Urgency maneuvers applied: {survival_activations}.
    - Critical Focus: {contexto_materias}.

    STRICT RULES (CRITICAL):
    1. DO NOT mention internal variable names (e.g. do not say "survival_activations", "peak_debt", or "missing_hours" verbatim). Translate the concept naturally.
    2. DO NOT use quotation marks to frame words. Talk directly.
    3. DO NOT recommend external study methods like Pomodoro or Flashcards. Justify the schedule generated.
    4. 'estrategia_global' (Limit: 35-45 words): Mention their critical subject ({peor_materia}) and justify your decision based on the telemetry.
    5. 'tacticas_clave': Max 2 descriptive sentences per tactic explaining the "why".

    {obtener_instruccion_idioma(idioma)}

    Generate strictly valid JSON:
    {{
      "estrategia_global": "(Empathetic and technical explanation, max 45 words).",
      "tacticas_clave": [
        {{ "icono": "(warning/bolt/balance/spa/shield/check/target)", "color": "(red/orange/amber/green/teal/blue)", "titulo": "TITLE", "descripcion": "Detailed explanation based on the schedule." }}
      ]
    }}
    Return ONLY JSON.
    """

  payload = {
      'model': 'deepseek-v4-flash',
      'thinking': {'type': 'disabled'},
      'messages': [
          {
              'role': 'system',
              'content': (
                  'You are an advanced strategist. Output only valid JSON. Obey'
                  ' language settings strictly.'
              ),
          },
          {'role': 'user', 'content': prompt},
      ],
      'temperature': 0.3,
      'response_format': {'type': 'json_object'},
  }

  try:
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    if response.status_code == 200:
      return json.loads(response.json()['choices'][0]['message']['content'])
    return fallback_json
  except Exception:
    return fallback_json