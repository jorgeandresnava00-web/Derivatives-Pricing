# Valuador de Futuros — Fase 1
*Proyecto de aprendizaje + portafolio. Doble propósito: entender valuación de derivados y construir un pipeline real.*

---

## Contexto del proyecto

Sistema que cada día jala precios EOD (yfinance), calcula el precio teórico de tres futuros (ES=F, GC=F, SI=F) con la fórmula cost-of-carry, detecta señales de arbitraje y lo visualiza en un dashboard Streamlit.

**Fórmula central:**
```
F_teórico = S × e^((r − q + u) × T)
```

**Arquitectura:**
```
run.py → src/data.py + src/maturity.py + src/valuation.py + src/arbitrage.py + src/storage.py
       → data/historico.csv
       → dashboard.py (Streamlit)
```

**Archivos clave:**
| Archivo | Propósito |
|---|---|
| `config.yaml` | Parámetros editables (q, u, banda de costos) |
| `src/data.py` | Precios spot y tasa libre de riesgo (yfinance) |
| `src/maturity.py` | Calcula T — tiempo al vencimiento en años |
| `src/valuation.py` | Aplica la fórmula F_teórico |
| `src/arbitrage.py` | Calcula basis y señal |
| `src/storage.py` | Lee/escribe historico.csv |
| `run.py` | Orquestador diario |
| `dashboard.py` | App web Streamlit |
| `APRENDIZAJE.md` | Diario de aprendizaje — actualizar en cada sesión |
| `Especificacion_Valuador_Futuros_Fase1.md` | Spec sellada del proyecto |

---

## Progreso actual

| Paso | Módulo | Estado |
|---|---|---|
| 1 | Entorno + estructura | ✅ |
| 2 | config.yaml | ✅ |
| 3 | src/data.py | ✅ |
| 4 | src/maturity.py | ✅ |
| 5 | src/valuation.py | ✅ |
| 6 | src/arbitrage.py | ✅ |
| 7 | src/storage.py | ✅ |
| 8 | run.py | ✅ |
| 8.5 | Captura de spot (base para convergencia) | ✅ |
| 9 | dashboard.py | ✅ |
| 9.5 | Backfill de histórico | ✅ |
| 9.6 | Rediseño del dashboard (mockup) | ✅ |
| 10 | GitHub Actions + Streamlit Cloud | ✅ |

**Paso 9.5 — Backfill de histórico ✅ (2026-06-07):** `backfill.py` + funciones `serie_*` en `data.py` (devuelven la serie completa indexada por fecha; las escalares siguen para `run.py`). Alinea spot/futuro/r por fecha (`pd.DataFrame({...}).dropna()`), recalcula T por día, salta días ya guardados (no pisa la corrida real). Resultado: 60 filas, 8-may→5-jun. **Hallazgo para 9.6:** GC=F dispara COMPRA FUTURO 16/20 días (basis ≈ −0.9% constante) = sesgo del proxy `GLD×10.96` (paso 8.5), NO arbitraje. Recalibrar factor a ~10.86 antes/durante el 9.6. Ver detalle en `APRENDIZAJE.md`.

**Paso 9.6 — Rediseño del dashboard (mockup) ✅ (2026-06-08):** `dashboard.py` reescrito desde cero, fiel a `Mockup.png`. Stack: **Plotly** (gráficas) + **HTML/CSS** (paneles, estética terminal) sobre Streamlit; colores centralizados en el diccionario `COL` (un cambio de tema = editar `COL`). Una pantalla con poco scroll, vista de UN instrumento vía `st.radio` (switcher). Paneles: barra superior, KPIs (semáforo señal / basis promedio / días venc), "Cálculo del futuro teórico", tira de métricas + acción sugerida, convergencia, basis vs banda, histórico (tabla HTML con badges), proximidad a señal (barras por σ), barra de estado inferior. **Decisión resuelta — HÍBRIDO:** la señal de arbitraje real (semáforo, acción, columna SEÑAL) usa la **banda fija 0.5%** del config (economía); las **bandas σ** son solo lente visual en las gráficas (fidelidad al mockup), NO disparan decisiones. Dos "basis" conviven: CSV `basis` = F_mercado−F_teórico (mispricing, dispara señal); mockup `BASIS` = F_mercado−Spot (carry, calculado al vuelo como `basis_fs`). Verificación: `.claude/launch.json` + MCP de preview (screenshot + medición DOM). **Mejora extra:** se agregó la línea −2σ (inferior) a la gráfica de proximidad (antes solo +2σ; inútil para instrumentos con basis negativo como el oro). **Recalibración del oro RESUELTA (2026-06-08):** se reverificó que NO hay spot de oro directo en yfinance (`XAUUSD=X` delisted; `GC=F`=futuro, `XAU=F`/`GOLD`=otra cosa) → solución C sigue descartada. Solución A aplicada: factor `GLD×10.96`→`10.89` (calibrado empíricamente: media `GC=F/GLD` ajustada por carry; el 10.96 quedaba arriba del propio futuro, imposible en contango). CSV regenerado por escalado lineal exacto (spot y F_teorico × 10.89/10.96; F_mercado intacto; señal recalculada; ES/SI sin tocar). Resultado: GC=F pasó de 16/20 COMPRA (sesgo) a 15 SIN SEÑAL / 4 COMPRA / 1 VENDE; basis medio −0.9%→−0.25% (ruido dentro de banda). Detalle completo en `APRENDIZAJE.md`.

**Paso 8.5 — Captura de spot:** agregar el precio spot real (distinto del futuro) al pipeline para habilitar la gráfica de convergencia en el dashboard. Cambios: `config.yaml` (tickers `spot` + `factor` de escala por instrumento), `src/data.py` (`precio_spot`), `run.py` (S usa spot real, guardar columna `spot`). Spot: ES=F→`^GSPC`×1.0, GC=F→`GLD`×10.89 (recalibrado en 9.6; era 10.96), SI=F→`SLV`×1.11. Corrige además el basis artificialmente negativo (antes S=F_mercado).

**Retomar siempre desde el primer paso ⬜.**

---

## Rol y metodología de enseñanza

You are a wise and incredibly effective teacher. Your goal is to make sure the human deeply understands the session.

Do this incrementally with each step instead of all at once at the end. Before moving on to the next stage, confirm that they have mastered everything in the current one. This should be high level (e.g. motivation, why this exists) and low level (e.g. business logic, edge cases, every line of code).

Keep the running `APRENDIZAJE.md` doc updated with:
- A checklist of things the human should understand
- What was built, how, and why
- The human's answers and gaps identified
- What explanation patterns worked best

Make sure they understand:
1. **What** are we doing
2. **How** are we doing it
3. **Why** are we doing it this way (and drill down into more whys)

Understanding the problem well is imperative — don't let them proceed on memorization alone.

To get a sense of where they're at, **proactively have them restate their understanding first**, then help them fill in the gaps. Explain like they're a smart intern with zero coding experience but strong financial intuition.

Quiz them with open-ended or multiple choice questions using `AskUserQuestion`. Be sure to:
- Change up the order of the correct answer each time
- Not reveal the answer until after the question is submitted
- Mix financial concepts with code mechanics

The session should not end until the human has demonstrated that they understood everything on the checklist for that step.

---

## Notas de aprendizaje (patrones que funcionan)

- Analogías concretas > definiciones abstractas (`.venv` = "caja aislada", `return` en `for` = "dejar de buscar en cuanto encuentras las llaves")
- El humano tiene fuerte intuición financiera — anclar conceptos de código en finanzas funciona bien
- Preguntas bottom-up: él detectó que `datetime` no estaba en `requirements.txt` → llevó a explicar librería estándar vs terceros
- Índices base-0 es un gap recurrente a reforzar
