# CL-CHRONOS: Cognitive-Load & Chronobiological Heuristic Resource Optimization Network Operating Scheduler

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776AB.svg)](https://www.python.org/)
[![Django 6.0](https://img.shields.io/badge/Django-6.0-092E20.svg)](https://www.djangoproject.com/)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0008--1196--5154-A6CE39.svg)](https://orcid.org/0009-0008-1196-5154)
[![DOI](https://zenodo.org/badge/1457355754.svg)](https://doi.org/10.5281/zenodo.24223241)
[![Preprint DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24223577.svg)](https://doi.org/10.5281/zenodo.24223577)

**CL-CHRONOS** is an open-source, four-layer algorithmic scheduling engine written in Python/Django. Unlike conventional static planners (e.g., Google Calendar, Notion, Trello) that treat physical time as a uniform container and assume an infinite mental reserve, CL-CHRONOS explicitly models **human cognitive energy as a constrained thermodynamic resource**, integrating Cognitive Load Theory, ultradian rest-activity cycles, and circadian executive constraints into a unified mathematical framework.

> **📄 Associated Research Paper:**
> * **English Manuscript:** *Heuristic Optimization of Study Schedules Based on Cognitive and Chronobiological Load*
> * **Spanish Manuscript:** *Optimización heurística de horarios de estudio basada en carga cognitiva y cronobiología*
> * **Author:** Martín Sebastián Guevara Ulloa

---

## 🧠 Four-Layer Mathematical Architecture

The engine conceptualizes academic planning as a constraint-based scheduling problem over a discrete daily temporal domain $T = \{0, 1, \dots, 1439\}$ across days $D = \{1, \dots, 7\}$, structured into four sequential layers:

### 1. Layer 1: Priority Model and Workload Inflation (`algorithm/capa1.py`)
* **Normalized Academic Performance ($a_s \in [0, 1]$):** Evaluates historical grades within the active academic period and assigns a discrete weakness factor $r_s \in \{1, 3, 5\}$.
* **Hybrid Urgency ($u_s$) & Academic Protection Floor:** Implements an *Earliest Deadline First (EDF)* heuristic across pending exams and projects, enforcing a minimum urgency floor ($u_s \ge 3$) whenever a subject is at risk of failing ($a_s < 0.6$).
* **Asymmetric Multi-Criteria Priority ($w_s, p_s$):** Computes continuous weight $w_s = 0.2 r_s + 0.5 u_s + 0.3 d_s$ (with neutral baseline structural complexity $d_s = 3$) and clamps it to a discrete priority $p_s \in [1, 5]$.
* **Supplementary Filter & Piecewise Project Inflation:** Assigns $0.0\text{ h}$ to supplementary courses to preserve cognitive reserve, while scaling core subject and project workloads via a piecewise function with a $1.5\times$ heuristic inflation weight for critical deadlines ($\delta_j \le 3\text{ days}$).

### 2. Layer 2: Thermodynamic & Chronobiological Allocation (`algorithm/capa2.py`)
* **Protected Daily Capacity ($C_d$):** Truncates autonomous study to a maximum of $2.0\text{ h/day}$ whenever fixed external workloads (classes + occupational shifts) exceed $5.0\text{ h}$.
* **Weekly Ego-Depletion Decay ($\alpha_d$) & Upper Homeostatic Saturation:** Scales the daily energy ceiling ($L = 100\text{ pts}$) by an empirical weekday decay factor $\alpha_d \in [0.70, 1.00]$ and clamps biological recovery via $E_d(t) \leftarrow \min(E_d(t), L \cdot \alpha_d)$.
* **Dynamic Intraday Fatigue Scaling:** Models block energy expenditure by cognitive profile ($k_s \in \{35.0, 25.0, 20.0, 10.0\}\text{ pts/h}$) scaled by prior same-profile sessions $f_c$ on day $d$:
  $$E_{cost}(f_c) = \Delta t \cdot k_s \cdot (1 + 0.15 \cdot f_c)$$
* **Preventive Anti-Burnout Brakes & Graceful Degradation:** Enforces priority-dependent minimum energy reserve thresholds ($E_{min} \in \{-50.0, -150.0, -300.0\}\text{ pts}$), triggering a two-level microblock degradation protocol and *Snap-to-Grid* human-symmetric rounding (nearest 10-minute multiple, 20-minute floor).
* **Interleaved Greedy Selection:** Enforces strict subject alternation $s(b_k) \neq s(b_{k-1})$ between consecutive study blocks unless operating under single-queue or critical survival exceptions (`AUTO_CRUNCH_CRAMMING`).

### 3. Layer 3: Sliding-Window Collision Resolution (`algorithm/capa3.py`)
* **Biological Friction Buffers ($\beta$):** Shifts colliding blocks forward in time ($t_{start} = t_{end}^{collision} + \beta$), injecting $\beta = l_{dec} = 30\text{ min}$ after classes, work shifts, or passive routines, and $\beta = l_{br} = 15\text{ min}$ after active/deep recovery or prior study sessions to account for task-switching costs and ultradian recovery.
* **Hard Circadian Wind-Down & Midnight Invariance:** Restricts logical-mathematical (`logic_math`) sessions to conclude strictly by `21:00` (`9:00 p.m.`) and prevents any block from crossing the `23:59` boundary.

### 4. Layer 4: Semantic Rendering & Explainable AI (`algorithm/capa4.py`, `algorithm/ia_engine.py`)
* **Midnight Carryover & Gap Interpolation:** Carries over nocturnal routines crossing midnight (`00:00` start) and interpolates calendar voids into structured biological slots (`Rest & Sleep`, `Morning Routine / Prep`, `Break / Decompression`, `Adaptive Slot / Flex Time`, and `Wind-down / Sleep Prep`).
* **Tele-Strategic XAI Module:** Connects to an LLM (`deepseek-v4-flash`, temperature $0.3$) governed by non-intervention constraints to translate scalar telemetry (`energy_debt_peak`, `burnout_prevention_hours`, `survival_mode_activations`) into an executive natural-language justification (`ai_insight`).

---

## 📂 Repository Structure

```text
cl-chronos-backend/
├── algorithm/              # Core 4-layer mathematical engine & XAI module
│   ├── capa1.py            # Layer 1: Priority & piecewise hour calculation
│   ├── capa2.py            # Layer 2: Thermodynamics, fatigue & interleaving
│   ├── capa3.py            # Layer 3: Sliding window & biological friction
│   ├── capa4.py            # Layer 4: Semantic interpolation & carryover
│   ├── engine.py           # Main orchestrator (CLChronosEngine)
│   └── ia_engine.py        # Layer 4 Explainable AI (XAI) post-processor
├── capa1/                  # Layer 1 ORM models (academics, difficulty, projects)
├── capa2/                  # Layer 2 ORM models (planner, preferences, limits)
├── capa3/                  # Layer 3 ORM models (occupation, routine, schedule)
├── users/                  # Custom User model
├── api/                    # REST API serializers, views & endpoints
├── cl_chronos/             # Django project settings & root URL configuration
├── .env.example            # Environment variable template
├── manage.py               # Django CLI utility
└── requirements.txt        # Reproducible Python dependencies
```

## 📄 Dual Licensing (GNU AGPLv3 + Commercial License)

**CL-CHRONOS** is dual-licensed to support open academic research while protecting commercial production deployments:

1. **Open-Source Academic & Network Copyleft License (GNU AGPLv3):**
   This project is free software licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. It is freely available for academic scrutiny, reproducibility, non-commercial research, and open-source projects. Under AGPLv3, any party that modifies or deploys CL-CHRONOS over a network (including SaaS, web, or mobile backends) must make the complete source code of their entire interacting system publicly available under the same AGPLv3 license.
2. **Commercial Proprietary License (The Nexa Ecosystem):**
   As the sole copyright holder, **Martín Sebastián Guevara Ulloa** reserves the right to deploy and distribute the CL-CHRONOS engine within closed-source proprietary commercial applications—specifically **Nexa** (iOS / Android)—and to grant separate commercial licenses to third-party organizations wishing to integrate CL-CHRONOS without AGPLv3 copyleft obligations.

For commercial licensing inquiries or research collaborations, contact: `msgu0603@gmail.com`.