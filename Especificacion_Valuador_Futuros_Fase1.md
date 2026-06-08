# Especificación — Valuador de Futuros (Fase 1)

*Sellada: 2026-06-02*

---

## 1. Objetivo

Proyecto aplicado de valuación de derivados financieros. Doble propósito:

- **Aprender código** y entender cómo se aplica la valuación financiera en un sistema real.
- **Portafolio / CV** — demostrar valuación cost-of-carry, detección de arbitraje y un pipeline de datos automatizado.

**No es para trading real.** Es un laboratorio de valuación con datos de fin de día.

**Modo de trabajo:** Claude escribe el código; el usuario lo entiende. Se explica cada pieza antes de avanzar. La configuración vive en un archivo editable sin necesidad de programar.

---

## 2. Alcance Fase 1 (sellado)

- **Solo futuros.** Opciones (Black-Scholes) y swaps quedan para fases posteriores.
- **Sin ganchos anticipados** — se construye un pipeline completo y bien entendido de futuros antes de tocar lo demás. Cada derivado es un proyecto en sí.

---

## 3. Instrumentos

| Instrumento | Ticker yfinance | Grupo | Método |
|---|---|---|---|
| E-mini S&P 500 | `ES=F` | A (carry observable) | Cost-of-carry directo — ancla, caso de libro de texto |
| Oro | `GC=F` | A | Cost-of-carry directo |
| Plata | `SI=F` | A | Cost-of-carry directo |

**Fórmula de valuación:**

```
F_teórico = S × e^((r − q + u) × T)
```

Donde:
- `S` = precio spot del subyacente
- `r` = tasa libre de riesgo
- `q` = dividend yield (S&P) o ≈0 (metales)
- `u` = costo de almacenaje (metales)
- `T` = tiempo a vencimiento (en años)

**Detección de arbitraje:** `basis = F_mercado − F_teórico`. Hay señal cuando `|basis|` excede una banda de costos de transacción.

---

## 4. Datos

- **Fuente:** `yfinance` (gratis, sin API key). Precios **EOD** (fin de día).
- **Inputs del modelo:**
  - `r` = `^IRX` (T-bill 13 semanas) vía yfinance — automático
  - `q` = constante configurable (S&P ~1.3%, metales 0)
  - `u` (almacenaje) = constante configurable (~0.4%/año)
  - `T` = aproximado al vencimiento trimestral más cercano *(limitación documentada)*
- **Histórico inicial:** backfill de **1–2 años** + append del dato nuevo cada día.
- **Almacenamiento:** archivo **CSV versionado** (la "base de datos" del proyecto).

---

## 5. Arquitectura

```
script.py
   │  jala precios EOD con yfinance
   │  calcula F_teórico, basis y señal
   ▼
historico.csv  (append diario, versionado)
   ▼
dashboard Streamlit  (lee el histórico y lo grafica)
```

**Fases de hosting:**
1. **Local primero** — correr el script a mano para entenderlo pieza por pieza.
2. **Migrar a GitHub Actions** — cron diario en la nube; corre aunque la laptop esté apagada; el repo público es el artefacto de CV.

**Frecuencia:** 1 vez al día (EOD).

---

## 6. Dashboard (Streamlit)

De arriba hacia abajo, por impacto:

1. **Tabla resumen del día** — instrumento, precio mercado, F_teórico, basis, %, semáforo de señal. Lo primero que se ve.
2. **Precio mercado vs teórico** — una gráfica por instrumento; dos líneas que casi se tocan, se separan cuando hay desalineación.
3. **Basis + señal de arbitraje** — el spread en el tiempo con banda de costos sombreada y puntos marcados al romper la banda.
4. **Inputs del modelo** — panel con `r`, `q`, `T`, `u` del día. Transparencia didáctica (no es caja negra).

Paleta alineable a la marca Nava (institucional, sobria) en la fase de diseño.

---

## 7. Limitaciones aceptadas y documentadas

- **Datos EOD, no en vivo** → no operable; es laboratorio.
- **Ticker continuo sin vencimiento exacto** → `T` aproximado.
- **Grupo B excluido en Fase 1** (energía, granos: petróleo, gas, maíz, trigo, soya, café) por *convenience yield* no observable gratis. Llega en **Fase 2** con el método de **carry implícito del término** (despejar la tasa de carry comparando dos vencimientos, sin necesidad de convenience yield).

---

## 8. Roadmap

| Fase | Contenido | Método |
|---|---|---|
| **1** | Futuros Grupo A: S&P + Oro + Plata | Cost-of-carry directo |
| **2** | Futuros Grupo B: energía + granos | Carry implícito del término |
| **3** | Opciones | Black-Scholes |
| **4** | Swaps | Por definir |

---

## 9. Pendiente operativo

- [ ] Confirmar / instalar **Python** en el Windows del usuario (primer paso antes de escribir código).

---

## 10. Costo

100% gratis. Único costo: la licencia de Claude (ya pagada). yfinance, GitHub Actions, Streamlit Community Cloud — todo en tier gratuito.
