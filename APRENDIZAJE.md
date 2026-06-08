# Diario de Aprendizaje — Valuador de Futuros Fase 1

> **Propósito:** Registrar qué se está construyendo, por qué, y qué entiende el humano en cada paso.
> Este archivo se actualiza en vivo durante cada sesión.

---

## El proyecto en una frase

Un sistema que cada día jala precios de mercado, calcula cuánto *debería* valer cada futuro (ES=F, GC=F, SI=F), compara ese valor teórico con el precio real, y avisa si hay una señal de arbitraje — todo guardado en CSV y visible en un dashboard web.

---

## La arquitectura de arriba nivel

```
script.py → historico.csv → dashboard Streamlit
```

| Pieza | Qué hace |
|---|---|
| `run.py` | El orquestador: une todo, corre 1 vez al día |
| `src/data.py` | Jala precios de yfinance |
| `src/maturity.py` | Calcula T (tiempo al vencimiento) |
| `src/valuation.py` | Aplica la fórmula cost-of-carry |
| `src/arbitrage.py` | Calcula basis y decide si hay señal |
| `src/storage.py` | Lee/escribe el CSV histórico |
| `dashboard.py` | App web Streamlit para visualizar |
| `config.yaml` | Todos los parámetros editables |

---

## La fórmula central

```
F_teórico = S × e^((r − q + u) × T)
```

| Símbolo | Qué es | Dónde viene |
|---|---|---|
| S | Precio spot (hoy) | yfinance |
| r | Tasa libre de riesgo | yfinance (^IRX) |
| q | Dividend yield | config.yaml (constante) |
| u | Costo de almacenaje | config.yaml (constante) |
| T | Años al vencimiento | calculado (próximo trimestre) |

---

## Progreso por pasos

| Paso | Título | Estado | Entendimiento |
|---|---|---|---|
| 1 | Entorno y estructura | ✅ Completo | ✅ Comprendido |
| 2 | config.yaml | ✅ Completo | ✅ Comprendido |
| 3 | data.py | ✅ Completo | ✅ Comprendido |
| 4 | maturity.py | ✅ Completo | ✅ Comprendido |
| 5 | valuation.py | ✅ Completo | ✅ Comprendido |
| 6 | arbitrage.py | ✅ Completo | ✅ Comprendido |
| 7 | storage.py | ✅ Completo | ✅ Comprendido |
| 8 | run.py | ✅ Completo | ✅ Comprendido |
| 9 | dashboard.py | ✅ Completo | ✅ Comprendido |
| 9.5 | backfill.py | ✅ Completo | ✅ Comprendido |
| 9.6 | Rediseño dashboard (mockup) | ✅ Completo | ✅ Comprendido |
| 10 | GitHub Actions | ⬜ Pendiente | — |

---

## PASO 1 — Entorno y estructura del proyecto

### ¿Qué se está construyendo?

La base de todo. Sin esto, nada corre. Se instala Python, se crea un **entorno virtual aislado** (`.venv`), se instalan las dependencias, y se crea la estructura de carpetas que usará el proyecto.

### ¿Por qué se hace así?

**Entorno virtual:** Python permite tener muchos proyectos en la misma computadora, y cada uno puede necesitar versiones distintas de las mismas librerías. El `.venv` es una "caja" aislada para este proyecto — lo que instales aquí no afecta otros proyectos ni el Python del sistema.

**requirements.txt:** Es el "recetario" de dependencias. Si mañana cambias de computadora o alguien más quiere correr tu proyecto, un solo comando (`pip install -r requirements.txt`) reconstruye todo el entorno exactamente igual.

### Comandos del paso 1 (PowerShell)

```powershell
# Crear el entorno virtual
python -m venv .venv

# Activarlo (el prompt debe mostrar (.venv))
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Verificar que yfinance está disponible
python -c "import yfinance; print('OK')"
```

### Cómo sé que funcionó

- [ ] `python --version` muestra 3.10 o superior
- [ ] El prompt de la terminal muestra `(.venv)`
- [ ] `python -c "import yfinance"` no da error

### Preguntas de comprensión

1. ¿Por qué un entorno virtual y no instalar todo "global"?
2. Si mañana cambias de computadora, ¿qué archivo reconstruye todo?

### Respuestas del humano (registradas en sesión)

- `requirements.txt` = receta de librerías del proyecto. Correcto al 100%.
- `.venv` = Python aislado dentro de la carpeta. Correcto al 100%.
- Preguntó: "¿por qué no instalar en el Python global? ¿afecta rendimiento?"

### Gaps identificados y resueltos

- **Gap:** No sabía que el problema de instalar global son los *conflictos de versiones*, no el rendimiento.
- **Explicación que funcionó:** ejemplo concreto — pandas 2.2 vs 1.3 entre dos proyectos distintos. Dos `.venv` = cada uno tiene la versión que necesita, sin pisarse.

---

---

## PASO 4 — maturity.py

### ¿Qué se está construyendo?

El módulo que calcula **T** — el único input de la fórmula que no viene de yfinance ni del config, sino de la lógica de fechas de los contratos.

### ¿Por qué se hace así?

- Los futuros CME tienen **vencimiento trimestral** (Mar/Jun/Sep/Dic) porque la liquidez se concentra ahí por convención de mercado. Los contratos mensuales existen técnicamente pero son casi ilíquidos.
- La fecha exacta es el **3er viernes** del mes de vencimiento (regla CME para equity/índices).
- `T` se mide en **años** para ser consistente con `r`, `q` y `u` que son tasas anuales.

### Las tres funciones del módulo

| Función | Qué hace |
|---|---|
| `_tercer_viernes(year, month)` | Calcula el 3er viernes de un mes dado (aritmética de calendario) |
| `proximo_vencimiento()` | Itera {Mar,Jun,Sep,Dic} de este año y el siguiente; devuelve el primero que no llegó |
| `tiempo_a_vencimiento()` | `(fecha_venc - hoy).days / 365.0` → T en años |

### El truco de `(4 - dia_semana) % 7`

Python numera días: Lun=0 … Vie=4 … Dom=6.
Para saber cuántos días faltan desde el inicio del mes hasta el primer viernes:
- Si el 1ro es Miércoles (2): `4-2 = 2` días → primer viernes es el día 3
- Si el 1ro es Sábado (5): `(4-5) % 7 = 6` días → primer viernes es el día 7
El `% 7` maneja el wrap-around cuando el mes ya empezó pasando el viernes.

### Output real (2026-06-03)

```
Hoy:              2026-06-03
Próximo venc.:    2026-06-19  (Friday)
Días que faltan:  16
T (años):         0.0438
```

### Limitación documentada

Usamos el mismo vencimiento trimestral para los tres instrumentos (ES, GC, SI). En realidad cada uno puede tener su propio calendario de vencimiento exacto, pero la diferencia es de días y está dentro del error aceptado para este laboratorio.

### Preguntas de comprensión

1. ¿Por qué dividimos los días entre 365 y no los dejamos como días?
2. Si hoy fuera 2026-12-20 (después del 3er viernes de diciembre), ¿cuál sería el próximo vencimiento que devolvería `proximo_vencimiento()`?
3. ¿Qué devuelve `.days` sobre un `timedelta`?

### Respuestas y gaps del humano

- **¿Qué hace maturity.py?** → "sacar la fecha de hoy, el próximo vencimiento, la diferencia y convertirla en años." ✅ Correcto al 100%.
- **¿Por qué 0.0438 y no 16?** → "el bloque 4 lo anualiza dividiendo entre 365." ✅ Correcto, identificó la línea exacta.
- **Bonus (22-dic-2026):** → "marzo 19 de 2027." ✅ Correcto — verificado: 3er viernes de mar/2027 = día 19.
- **Sobre liquidez trimestral:** entendió el mecanismo de red — el ciclo trimestral se auto-refuerza: más volumen → más liquidez → todos van ahí. También conectó el rollover 4x vs 12x como ventaja operativa. ✅ Razonamiento propio, no repetición.
- **Gap pendiente:** explicación línea por línea del código (Python nuevo para él). → Resuelto en sesión.
- **Observación destacada:** detectó solo que `datetime` no está en `requirements.txt` — preguntó por qué. Llevó a explicar librería estándar vs. terceros. Razonamiento bottom-up excelente.
- **Gap resuelto:** diferencia entre librería estándar (viene con Python) y librerías de terceros (se instalan, van en requirements.txt).
- **Gap resuelto:** qué es un `for` loop — iteración sobre una lista.
- **Gap resuelto:** `return` dentro de un `for` detiene el loop y sale de la función inmediatamente.
- **Gap menor:** aritmética `(4-0)%7 = 4`, no 2. Confundió lunes=0 con lunes=1 (índices base-0 en Python).

---

## PASO 5 — valuation.py

### ¿Qué se está construyendo?

El módulo más corto del proyecto — 5 líneas — pero el corazón matemático. Aplica la fórmula cost-of-carry para calcular el precio teórico de un futuro dado el precio spot y las condiciones de mercado.

### ¿Por qué se hace así?

**Separación de responsabilidades:** `valuation.py` recibe los datos como parámetros — no los busca solo. Esto lo hace independiente de internet, testeable en aislamiento, y reutilizable con datos históricos. Quien conecta todos los módulos es `run.py`.

**Analogía clave del humano:** "Es una forma de que los scripts se comuniquen entre sí pero cada uno funcione de manera independiente." ✅ Descripción exacta.

### El código completo

```python
import math

def valuar_futuro(S: float, r: float, q: float, u: float, T: float) -> float:
    """Precio teórico de un futuro usando cost-of-carry: F = S * e^((r - q + u) * T)"""
    return S * math.exp((r - q + u) * T)
```

### Los 5 parámetros

| Parámetro | Significado | Fuente |
|---|---|---|
| S | Precio spot del subyacente | data.py (yfinance) |
| r | Tasa libre de riesgo (decimal) | data.py (^IRX) |
| q | Dividend yield continuo (decimal) | config.yaml |
| u | Costo de almacenaje (decimal) | config.yaml |
| T | Años al vencimiento | maturity.py |

### Por qué q se resta y u se suma

- `r` = costo de financiar la posición (te cuesta)
- `q` = dividendos que cobras si tienes el activo físico (te paga → reduce el carry cost)
- `u` = bodega, seguro, custodia (te cuesta)

### Ejemplo numérico (oro, 3 meses)

```
F = 2400 × e^((0.05 + 0.004) × 0.25)
F = 2400 × e^(0.0135)
F ≈ $2,432.6
```

El futuro vale $32.6 más que el spot — ese es el costo de "cargar" oro durante 3 meses.

### Respuestas y gaps del humano

- **Separación de responsabilidades:** Entendió inmediatamente la analogía "scripts que se comunican pero funcionan independiente." ✅
- **¿Por qué u=0 en ES=F?** → "un índice no es un activo físico, no hay nada que guardar en bodega." ✅
- **¿Por qué q se resta?** → "los dividendos reducen el costo de mantener el activo, son un ingreso que compensa." ✅
- **¿F > o < spot para el oro?** → "mayor, porque r+u > 0." ✅

### Conceptos nuevos del paso

- `math.exp(x)` = e^x en Python (librería estándar `math`)
- Parámetros de función: la función no jala sus propios datos, los recibe de quien la llama
- Separación de responsabilidades entre módulos

---

## PASO 6 — arbitrage.py

### ¿Qué se está construyendo?

El módulo que detecta oportunidades de arbitraje. Compara el precio de mercado del futuro contra el precio teórico y decide si la desviación es suficientemente grande para ser rentable.

### Las dos funciones

```python
def calcular_basis(F_mercado, F_teorico):
    return F_mercado - F_teorico

def señal_arbitraje(basis, banda):
    if basis > banda:   return "VENDE FUTURO"
    if basis < -banda:  return "COMPRA FUTURO"
    return "SIN SEÑAL"
```

### ¿Por qué una banda y no comparar contra cero?

El arbitraje tiene costos reales: comisiones, slippage, margen. Si `|basis| < costos`, no es rentable. La banda de 0.5% del `config.yaml` representa ese umbral mínimo.

### Los tres casos

| Caso | Significado | Señal |
|---|---|---|
| `basis > +banda` | Futuro caro vs. teórico | `"VENDE FUTURO"` |
| `basis < -banda` | Futuro barato vs. teórico | `"COMPRA FUTURO"` |
| `\|basis\| ≤ banda` | Rango normal | `"SIN SEÑAL"` |

### ¿Por qué string y no booleano?

Hay tres estados, no dos. Un `True/False` pierde la dirección (¿vendo o compro?). El string es legible directamente en el CSV y en el dashboard.

### ¿Quién convierte la banda de % a dólares?

`run.py` — el orquestador calcula `banda_usd = F_teorico × 0.005` antes de llamar a `señal_arbitraje`. `arbitrage.py` solo compara números; no sabe de configs ni precios teóricos.

### Respuestas y gaps del humano

- **Descripción del módulo:** "va a ver si hay arbitraje donde la diferencia entre precio teórico y precio real sea mayor a cierto número." ✅ Correcto de entrada.
- **¿Por qué banda y no cero?** → "porque ejecutar el arbitraje tiene costos reales." ✅
- **Ejemplo numérico (basis=+$40, banda=$26.55):** → "VENDE FUTURO." ✅
- **¿Quién convierte la banda?** → No sabía → se explicó con el principio de separación ya conocido. ✅ Entendió el razonamiento.

---

## PASO 7 — storage.py

### ¿Qué se está construyendo?

El módulo que persiste los datos en el tiempo. Cada día que corre `run.py`, agrega 3 filas nuevas al CSV (una por instrumento) sin borrar el historial anterior.

### Las dos funciones

```python
def guardar_registro(ruta, registro):
    # Si el CSV existe → léelo, agrega la fila nueva, guarda
    # Si no existe → crea el CSV con solo esa fila

def cargar_historico(ruta):
    # Si el CSV existe → devuélvelo como DataFrame
    # Si no existe → devuelve DataFrame vacío (primer día)
```

### Estructura del CSV

```
fecha,      ticker, F_mercado, F_teorico, basis,  señal
2026-06-04, ES=F,   5350.00,   5310.00,   40.00,  VENDE FUTURO
2026-06-04, GC=F,   2432.00,   2430.50,   1.50,   SIN SEÑAL
```

Cada día agrega 3 filas. El historial crece indefinidamente.

### Conceptos nuevos

| Concepto | Qué es |
|---|---|
| `dict` | Pares clave-valor. `{"ticker": "ES=F", "basis": 40.0}`. Así recibe `guardar_registro` los datos de `run.py` |
| `Path` | Clase de `pathlib` para manejar rutas. Permite `ruta.exists()` para verificar si el archivo ya existe |
| `pd.DataFrame([dict])` | Convierte un diccionario en una tabla de una fila |
| `pd.concat([df1, df2])` | Pega dos tablas verticalmente |
| `index=False` | Le dice a pandas que no escriba la columna de números de fila (0,1,2...) en el CSV |
| `-> None` | La función no devuelve nada — su trabajo es el efecto de escribir el archivo |

### Código defensivo

`cargar_historico` devuelve `pd.DataFrame()` vacío (no error) cuando el CSV no existe — para que el dashboard funcione desde el primer día sin historial. Anticipar casos borde en lugar de dejar que el programa explote.

### Respuestas y gaps del humano

- **¿Qué hace storage.py?** → "el script que guarda todos los datos, el que lo manda al CSV." ✅
- **Columnas del CSV:** → Seleccionó fecha+ticker, F_mercado+F_teórico, basis+señal. ✅ Completo.
- **Librería para CSV:** → Eligió `csv` estándar (razonamiento válido). Se explicó por qué pandas es mejor en este contexto (1 línea vs. 8, compatibilidad con dashboard). ✅
- **¿Por qué DataFrame vacío en lugar de error?** → "para que el dashboard no explote el primer día." ✅
- **`index=False`:** → No sabía. Se explicó con el ejemplo de la columna extra (0,1,2...) que pandas agrega por defecto. ✅

---

## PASO 8 — run.py

### ¿Qué se está construyendo?

El orquestador — el script que une todos los módulos y corre una vez al día. No calcula nada nuevo: delega a cada módulo su responsabilidad y conecta los resultados.

### Flujo completo

1. Leer `config.yaml` → parámetros (q, u, banda, ruta CSV)
2. Calcular `r`, `T`, `hoy` una sola vez (son iguales para los 3 tickers)
3. Loop sobre los 3 instrumentos:
   - Jalar precio spot → `data.py`
   - Sacar q y u del config para ese ticker
   - Calcular F_teórico → `valuation.py`
   - Calcular basis → `arbitrage.py`
   - Convertir banda de % a USD → `run.py` (separación de responsabilidades)
   - Detectar señal → `arbitrage.py`
   - Empacar en dict y guardar → `storage.py`
   - Imprimir resumen en terminal

### Output real (2026-06-05)

```
ES=F: F_mercado=7458.50 | F_teorico=7465.15 | basis=-6.65 | SIN SEÑAL
GC=F: F_mercado=4366.80 | F_teorico=4373.55 | basis=-6.75 | SIN SEÑAL
SI=F: F_mercado=69.24   | F_teorico=69.34   | basis=-0.11 | SIN SEÑAL
```

CSV generado: `data/historico.csv` con 3 filas, una por instrumento.

### Interpretación del output

- Basis negativo en los 3 = mercado paga ligeramente menos que el teórico
- Ninguno dispara señal porque el basis ($6.65, $6.75, $0.11) está muy por debajo de la banda (~$37, ~$22, ~$0.35)
- Significa que el mercado está dentro del rango de eficiencia — no hay arbitraje rentable hoy

### Conceptos nuevos del paso

| Concepto | Qué es |
|---|---|
| `yaml.safe_load()` | Lee un archivo YAML y lo convierte en diccionario Python |
| `cfg["instrumentos"].items()` | Itera sobre pares (ticker, params) del config |
| `date.today().isoformat()` | Fecha de hoy como string: "2026-06-05" |
| `round(x, 2)` | Redondea a 2 decimales para limpiar el CSV |
| `f"{var:.2f}"` | Formato de string: muestra float con exactamente 2 decimales |
| `Set-ExecutionPolicy` | Comando de Windows para permitir correr scripts .ps1 |

### Respuestas y gaps del humano

- **Flujo general:** describió los 6 pasos en orden correcto sin ayuda. ✅
- **¿Por qué r y T antes del loop?** → "son iguales para los 3, no tiene sentido calcularlos 3 veces." ✅
- **Bloque 5:** no lo entendía — se explicó instrumento por instrumento (historia del oro). ✅ Resuelto.
- **¿Por qué banda_usd en run.py?** → "porque arbitrage.py solo compara números." ✅ Aplicó el principio solo.
- **Interpretación del basis negativo:** → "el mercado paga menos de lo que debería." ✅
- **¿Por qué SIN SEÑAL con basis -6.65?** → "porque no supera la banda mínima de costos." ✅

---

## PASO 8.5 — Captura del spot (base para la convergencia)

### ¿Por qué surgió este paso?

Al diseñar el dashboard (paso 9), el humano pidió ver la **gráfica de convergencia**: cómo `F_teórico`, `F_real` (futuro) y `spot` se mueven y se juntan al acercarse el vencimiento. Detectó solo que el spot no se estaba guardando.

### El hallazgo de fondo (no solo faltaba el dato)

En `run.py` actual: `S = precio_cierre(ticker)` y `F_mercado = precio_cierre(ticker)` usan **el mismo ticker** → `S == F_mercado`. Consecuencia matemática:

```
F_teórico = F_mercado × e^(+algo)  →  siempre > F_mercado
basis = F_mercado − F_teórico       →  SIEMPRE negativo
```

Por eso en el paso 8 los 3 basis salieron negativos: no era señal, era un **artefacto**. Usar el spot real arregla el modelo, no solo habilita la gráfica.

### Datos verificados en yfinance

| Instrumento | Futuro | Spot real | Decisión |
|---|---|---|---|
| S&P 500 | `ES=F` 7467 | `^GSPC` 7449 (limpio) | spot real, factor 1.0 |
| Oro | `GC=F` 4367 | `XAUUSD=X` muerto → ETF `GLD` 398 | `GLD` × 10.96 |
| Plata | `SI=F` 69.2 | `XAGUSD=X` muerto → ETF `SLV` 62.3 | `SLV` × 1.11 |

Los metales no tienen spot gratis limpio en yfinance; se usa ETF × factor de escala (aproximado, editable, deriva lento por comisiones).

### Los cambios (mínimos gracias al diseño modular)

| Archivo | Cambio |
|---|---|
| `config.yaml` | `spot:` y `factor:` por instrumento |
| `src/data.py` | función `precio_spot(ticker, factor)` |
| `run.py` | `S` usa spot real; guardar columna `spot` |
| `src/storage.py` | **nada** (guarda cualquier clave del dict) |
| `valuation/maturity/arbitrage.py` | **nada** |

Refuerza el principio de **separación de responsabilidades**: el cambio de fuente de S no toca la fórmula ni el almacenamiento.

### Pendiente: regenerar el CSV

El `historico.csv` viejo no tiene columna `spot` y su basis es artificial → borrarlo y regenerarlo con datos correctos.

### Resultado verificado (2026-06-05, CSV regenerado)

```
fecha,      ticker, spot,    F_mercado, F_teorico, basis,  señal
2026-06-05, ES=F,   7460.01, 7463.0,    7466.67,   -3.67,  SIN SEÑAL
2026-06-05, GC=F,   4365.70, 4363.8,    4372.44,   -8.64,  SIN SEÑAL
2026-06-05, SI=F,   69.15,   68.99,     69.26,     -0.27,  SIN SEÑAL
```

`spot` ≠ `F_mercado` → el fix funcionó. El basis ahora es señal legítima (no artefacto), aunque hoy caiga dentro de banda. Descomposición ES=F: spot 7460 + carry teórico 6.66 = F_teórico 7466.67; el futuro de mercado (7463) cae ENTRE spot y teórico → mercado cobra menos carga de la predicha → basis −3.67 (futuro barato vs justo).

### Respuestas y gaps del humano

- **¿Por qué hoy spot y F_real son la misma línea?** → "no estamos jalando el spot de ningún lado ni documentándolo." ✅ Detectó el problema solo.
- **¿Por qué precio_spot llama a precio_cierre?** → "ya pides el cierre antes, solo agregas una línea para multiplicar por el factor." ✅ Captó la reutilización (DRY). Gap menor afinado: "spot verdadero" solo aplica al S&P; metales son proxy.
- **Restate de los 3 cambios:** describió correctamente data.py (variable spot nueva), la distinción futuro vs spot en los 3 activos, y storage guardando spot vía el dict→fila. ✅ Comprensión sólida.

### Estado: ✅ código completo y verificado. Base lista para la gráfica de convergencia del dashboard.

---

## PASO 9 — dashboard.py · FASE DE DISEÑO

### ¿Qué se hizo en esta fase?

Antes de escribir una línea de `dashboard.py`, se diseñó **cómo se va a ver**. Se usó la metodología "Design It Twice" (de *A Philosophy of Software Design*): la primera idea casi nunca es la mejor, así que se generaron **3 diseños radicalmente distintos** con sub-agentes en paralelo, se compararon, y se sintetizó lo mejor de cada uno.

### Los datos con los que trabaja el dashboard

El dashboard NO calcula nada — solo **lee y muestra** `data/historico.csv`. Columnas disponibles:
`fecha, ticker, F_mercado, F_teorico, basis, señal`. Hoy hay 1 día (3 filas); el histórico crece cada corrida.

### Los tres diseños generados

| Diseño | Filosofía | Fortaleza | Debilidad |
|---|---|---|---|
| **A — Minimalista** | 3 tarjetas, una pantalla, cero interacción. "Entender todo en 3 seg." | Rápido de leer, perfecto día 1, imposible de usar mal | Riesgo de verse "básico" |
| **B — Explorador** | Sidebar + 3 pestañas + waterfall que descompone r/q/u/T | Profundidad analítica, demuestra rigor financiero | Complejo; zonas vacías día 1 (gráfica histórica de 1 punto) |
| **C — Terminal Bloomberg** | Tema oscuro, mono, semáforo, glow. Estética de mesa de trading | Wow-factor para portafolio | CSS frágil; zonas históricas vacías hoy |

### Criterios de comparación (de *A Philosophy of Software Design*)

- **Profundidad:** interfaz pequeña que esconde mucha complejidad = buena. A es el más "profundo"; B el más "shallow" (expone mucha superficie).
- **El problema del "primer día":** con solo 3 filas, las gráficas históricas de B y C se ven rotas/vacías. A no tiene ese problema porque solo muestra hoy.
- **Contra los dos objetivos:** monitor diario → gana A (velocidad). Portafolio → C impresiona por estética, B por rigor.

### Decisión: LA SÍNTESIS

Ningún diseño puro ganó. Se combinó:
1. **Esqueleto de A** — las 3 tarjetas Mercado-vs-Teórico sin scroll, estado apagado/encendido que hace saltar la señal.
2. **Estética de C** — tema oscuro/mono/semáforo, pero como **capa final opcional**.
3. **Una pieza de B** — la descomposición de la fórmula (waterfall r/q/u/T) abajo. Clave: funciona perfecto día 1 porque NO necesita histórico.
4. **Pospuesto** — la gráfica de evolución histórica (útil en semanas, hoy no).

**Estrategia de construcción elegida:** *"Empieza nativo, CSS después."* Primero que funcione con componentes nativos de Streamlit (`st.metric`, `st.columns`, `st.container`), luego agregar la estética terminal como paso aislado. Madurez de ingeniería: primero correcto, luego bonito.

### Por qué esta decisión es buena (principio transferible)

Diseñar para el **caso común** (¿hay señal hoy?) y el **estado real de los datos** (día 1, sin histórico) en vez de para un futuro hipotético lleno de datos. Las zonas que necesitan histórico se posponen o se marcan como "se llenan con el tiempo".

### Pendiente para la siguiente sub-fase

Implementar `dashboard.py` con la síntesis, en versión nativa primero. → Ver sub-plan abajo.

---

## PASO 9 — dashboard.py · SUB-PLAN DE IMPLEMENTACIÓN

> Este es el paso más largo. Se construye por **bloques**, cada uno entendido antes de pasar al siguiente (metodología de siempre: el humano restate → se llenan gaps → quiz).

### Principio rector del dashboard

`dashboard.py` **solo lee y dibuja** el CSV. NO calcula valuaciones (eso es trabajo de `run.py`). Separación de responsabilidades, igual que el resto del proyecto. Si un dato no está en el CSV, el dashboard no puede mostrarlo.

### Cómo corre Streamlit (concepto base)

Streamlit ejecuta el script **de arriba a abajo cada vez** que el usuario interactúa (cambia un filtro, etc.). No es como una página web normal con botones que llaman funciones; es un script que se re-corre completo. Esto hay que entenderlo antes de escribir nada.

### Checklist de comprensión del paso 9

- [ ] Cómo Streamlit corre el script top-to-bottom y redibuja
- [ ] Cómo cargar el CSV (reusar `storage.cargar_historico`) y filtrar "hoy" (último día)
- [ ] El caso día-1 / CSV vacío (código defensivo)
- [ ] `st.columns` para poner las 3 tarjetas lado a lado
- [ ] `st.metric` (y su `delta`) para mostrar precios
- [ ] Colorear/encender la tarjeta según la columna `señal`
- [ ] Graficar serie de tiempo (la convergencia: spot · futuro · teórico)
- [ ] Cómo correr el dashboard: `streamlit run dashboard.py`

### Bloques de construcción (en orden)

| Bloque | Qué construye | Componentes clave | Estado |
|---|---|---|---|
| **0 — Setup** | `st.set_page_config` + cargar config y CSV + manejar CSV vacío + sacar "hoy" (última fecha) | `st.set_page_config`, `cargar_historico`, pandas filter, `st.stop` | ✅ |
| **1 — Header** | Título + fecha + banda ±0.5% | `st.title`, `st.caption` | ✅ |
| **2 — Tarjetas** | 3 tarjetas Mercado-vs-Teórico lado a lado (lo primero sin scroll) | `st.columns(3)`, `st.container(border=True)`, `st.metric`, máscara booleana | ✅ |
| **3 — Señal visual** | La tarjeta se "enciende" según `señal` (rojo=VENDE, verde=COMPRA, gris=SIN SEÑAL) | `st.success/error/info`, if/elif/else | ✅ |
| **4 — Convergencia** | Gráfica de spot · F_mercado · F_teorico en el tiempo (la pieza estrella) + caso "1 punto" | `st.line_chart`, `st.selectbox` (dispara rerun) | ✅ |
| **5 — Descomposición** | Expander: cómo S se vuelve F_teorico (r, q, u, T) — atribución secuencial | `st.expander`, `st.latex`, `st.columns`+`st.metric`, tabla markdown | ✅ |
| **6 — Estética** | Tema oscuro charcoal + naranja (config.toml) + CSS fino (títulos naranja, paneles redondeados) | `.streamlit/config.toml`, `st.markdown`+CSS | ✅ |
| **7 — KPIs del día** | Fila superior: nº señales activas, \|basis\| promedio, días al vencimiento | `st.columns`, `st.metric`, suma de booleanos, `.abs().mean()`, `.iloc[0]` | ✅ |
| **8 — Basis en el tiempo** | Basis % de cada instrumento vs banda ±0.5% (líneas de referencia) | `df.pivot` (largo→ancho), `st.line_chart` | ✅ |
| **9 — Blotter histórico** | Tabla ordenable del registro reciente | `st.dataframe`, `sort_values`, `hide_index` | ✅ |
| **10 — Barras distancia a banda** | \|basis%\| por instrumento: qué tan cerca de disparar señal | `st.bar_chart` | ✅ |

> Estética elegida (bloque 6): inspirada en dashboard charcoal + naranja. Colores: fondo `#2B2B33`, paneles `#34343E`, acento `#F5821F`, texto `#E8E8EA`.

### ✅ Decisión resuelta (bloque 5): guardar r y T en el CSV

Se eligió la opción (b), consistente con el paso 8.5: se extendió `run.py` para guardar `r` y `T` en cada registro (ya se calculaban antes del loop, solo se agregaron al dict). CSV regenerado con 9 columnas: `fecha, ticker, r, T, spot, F_mercado, F_teorico, basis, señal`. El dashboard sigue siendo solo-lector. La descomposición saca r/T/spot del CSV y q/u del config.

**Nota:** al regenerar el CSV (2026-06-05, precios movidos), ES=F dio basis **+9.51 (positivo)** — confirma en vivo que el basis ya no está forzado a ser negativo.

### Herramientas ya verificadas

streamlit 1.58.0, altair 6.1.0, plotly (en requirements). Sin bloqueos.

---

## PASO 9.5 — Backfill de histórico *(planeado)*

### Motivación

Las gráficas (convergencia, basis-en-el-tiempo, barras de proximidad) hoy se ven "solas" porque solo hay 1 día de datos. El humano propuso jalar días anteriores para llenarlas. Quedan ~14 días al vencimiento (19 jun 2026), así que se puede llenar con las últimas semanas.

### Enfoque técnico

- yfinance trae varios días con `history(period="1mo")` (no solo el último cierre).
- Crear `backfill.py` (SEPARADO de `run.py`, que es solo "hoy"). Para cada día pasado: T = (venc − ese_día).days/365, jalar spot/futuro/r de ESE día, valuar, escribir fila.
- Ojo: `r` (^IRX) también tiene histórico diario; usarlo para que cada día sea correcto.
- Beneficio extra: habilita las **bandas σ** del mockup (necesitan histórico de basis para la desviación estándar).

### ✅ IMPLEMENTADO (2026-06-07)

**La trampa conceptual:** `data.py` terminaba todas sus funciones en `.iloc[-1]` — jalaba varios días pero tiraba todos menos el último. `run.py` está hecho para "dame HOY". El backfill necesita lo contrario: la **columna entera**.

**Los dos cambios (y por qué solo dos):**
| Archivo | Cambio | Por qué |
|---|---|---|
| `src/data.py` | +3 funciones `serie_*` (`serie_cierre`, `serie_spot`, `serie_tasa`) que devuelven la **serie completa indexada por fecha**. Las escalares se quedan para `run.py`. | Único módulo que decía "solo el último día". |
| `backfill.py` (nuevo) | Gemelo de `run.py` pero itera sobre la serie; recalcula T por fecha; salta días ya guardados. | Orquestador del pasado. |
| `valuation / arbitrage / maturity / storage` | **NADA** | Reciben parámetros — no les importa si el dato es de hoy o de hace 3 semanas. La separación de responsabilidades pagó: 80% del pipeline se reusó intacto. |

**El corazón técnico — ALINEAR series (no pegarlas):**
```python
df = pd.DataFrame({"spot": spots, "F_mercado": futuros, "r": tasas}).dropna()
```
pandas junta las tres Series por su **índice de fecha** (no por posición de fila). `dropna()` deja solo los días que tienen spot Y futuro Y r. Si se pegaran por posición, un feriado distinto entre tickers desalinearía el spot de un día con el futuro de otro → valuación basura.

**No duplicar:** `ya_existe = set(zip(hist["fecha"], hist["ticker"]))` protege la corrida real de `run.py` (2026-06-05). El backfill se detuvo en 06-04. Resultado: **60 filas, 8-may → 5-jun, 20 días**.

**T per día (verificado):** el humano predijo correcto que T era MAYOR en el pasado. Se ve en el CSV: T se encoge de ~0.117 (8-may) a ~0.038 (5-jun) → el carry se aprieta hacia 0 = la convergencia hecha dato.

### 🔍 HALLAZGO que solo el backfill pudo revelar

Con 20 días, las señales muestran un patrón imposible de ver con 1 punto:

| Instrumento | SIN SEÑAL | COMPRA FUTURO | VENDE FUTURO |
|---|---|---|---|
| ES=F | 20/20 | 0 | 0 |
| GC=F | 4 | **16** | 0 |
| SI=F | 7 | 11 | 2 |

El oro dispara "COMPRA FUTURO" 16 de 20 días, basis siempre negativo (−20 a −87 ≈ **−0.9%**). El humano lo diagnosticó solo: *"es sospechoso, no una oportunidad."* **Una señal que persiste sin cerrarse no es arbitraje — es sesgo del modelo.** Causa raíz: el proxy del spot `GLD × 10.96` (paso 8.5) está ~0.9% inflado de forma constante → infla F_teórico → basis sistemáticamente negativo. Fix futuro: recalibrar factor a ~10.86 (terreno del 9.6).

**Por qué importa:** el 5-jun aislado el basis del oro era −3.72 (parecía sano). El sesgo solo emerge al ver la serie. Esto distingue **ruido (ES=F oscila ±) de sesgo (GC=F siempre −)** — exactamente lo que medirán las **bandas σ** del paso 9.6.

### 🛡️ Protección contra el rollover de vencimiento (2026-06-07, mismo día)

El humano detectó solo una limitación: al llegar al vencimiento (19-jun) el contrato continuo (`ES=F` etc.) rola al siguiente (sep) → la gráfica muestra un **diente de sierra** (converge a 0, salta arriba). Eso es comportamiento de mercado real, no bug.

**El bug real estaba en el backfill:** calculaba `venc = proximo_vencimiento()` UNA vez (arriba del loop) y se lo aplicaba a todos los días. Si se corre tras un rollover (ej. en julio), a un día de junio le asignaría el venc de septiembre → T sobrestimada → valuación inflada.

**Fix:** `proximo_vencimiento(desde=None)` ahora acepta una fecha opcional (default = hoy, no rompe `run.py`). El backfill la llama POR DÍA: `venc = proximo_vencimiento(desde=fecha)` dentro del loop. Cada día histórico se valúa con el vencimiento que le tocaba (mayo→jun, julio→sep).

**Conceptos que el humano clavó aquí:**
- **Comportamiento emergente:** el código NO programa la convergencia. Solo jala precios de hoy + saca el próximo venc + guarda. La convergencia/diente de sierra EMERGE al graficar los días juntos (analogía: time-lapse del sol — tomas una foto diaria, el movimiento aparece solo).
- **`run.py` se auto-corrige en el rollover** porque recalcula venc cada día desde cero; el backfill no, porque reconstruía el pasado con el "calendario de hoy".
- **Valor por defecto en parámetro** (`desde=None`) permite endurecer el backfill sin tocar `run.py`.
- Analogía que funcionó: leer periódicos viejos con la fecha impresa en CADA periódico, no con el calendario de la pared de hoy.

## PASO 9.6 — Rediseño del dashboard según mockup *(planeado)*

### Referencia

`mockup.png` en la raíz del proyecto (hecho por el humano con GPT image). **LEERLO primero** en la sesión de rediseño. Es la realización fiel del "Diseño C — terminal Bloomberg" que se generó en la fase de diseño.

### Qué cambia vs. la versión actual (10 bloques)

1. **Una sola pantalla, sin scroll** — grid fijo tipo cockpit (la versión actual scrollea).
2. **Vista de UN instrumento a la vez** con switcher, diseñada para **escalar a más instrumentos** sin rediseñar (no las 3 tarjetas fijas actuales).
3. **Estética terminal fiel al mockup:** monoespaciado, fondo charcoal, acentos naranja/verde/teal, semáforo grande.
4. **Paneles nuevos del mockup:**
   - Barra superior: FECHA/HORA · INSTRUMENTO · VENCIMIENTO · ESTADO DEL MERCADO.
   - KPIs: Señal de arbitraje (semáforo + SÍ/NO + desviación), Basis promedio, Días a vencimiento.
   - Panel "CÁLCULO DEL FUTURO TEÓRICO": fórmula + inputs (S, r, q, T) + resultado.
   - Panel instrumento: Spot · Futuro mercado · Futuro teórico · Basis · ACCIÓN SUGERIDA (botón) · Carry implícito · Desviación · Mispricing.
   - Gráficas: Convergencia del contrato, Basis vs banda, Histórico (tabla), Proximidad a señal (barras coloreadas por σ).
   - Barra de estado inferior: fuente, actualización, frecuencia, latencia, conexión, sistema.

### Decisión pendiente del rediseño

El mockup usa **bandas estadísticas ±1σ/±2σ** (desviación estándar del basis), NO la banda fija de costos 0.5% del config. Definir en la sesión: ¿migrar a σ-bands, mantener el 0.5%, o mostrar ambas? (σ-bands requieren el backfill del paso 9.5 primero.)

### Orden sugerido

9.5 (backfill) ANTES de 9.6 (rediseño), para que el rediseño ya tenga datos y bandas σ con qué trabajar.

### ✅ IMPLEMENTADO (2026-06-08)

`dashboard.py` reescrito desde cero, fiel al `Mockup.png`. Verificado en vivo (Streamlit headless + capturas + medición DOM): cabe en una pantalla con poco scroll (block-container ~1045px) y los 3 instrumentos + estados de señal renderizan bien.

**Las tres capas que se introdujeron (concepto nuevo del humano):**
| Capa | Rol | Analogía que funcionó | Dónde |
|---|---|---|---|
| Streamlit | armazón (cuartos, pisos) | el edificio | todo el archivo |
| HTML/CSS | estructura + estilo (pintura, molduras) | decoración | bloque `<style>` + cada `<div class="panel">` |
| Plotly | gráficas interactivas finas | el plano en la pared | `go.Figure()`, `base_layout()` |

**Por qué se abandonó lo nativo (`st.metric`, `st.line_chart`):** rígido, no permite el borde naranja, el semáforo, la mono, ni las bandas σ sombreadas. HTML/CSS da control de pixel; Plotly da control de cada línea/banda. Trade-off aceptado: más código, pero estética terminal fiel.

**Colores centralizados en UN diccionario `COL`** (decisión de diseño deliberada): un cambio de tema (ej. modo claro) = cambiar el diccionario, no buscar colores regados. El `<style>` los consume vía f-string `{COL['bg']}`.

**Dos conceptos de "basis" que conviven (la confusión más sutil, ya aclarada):**
- CSV `basis` = `F_mercado − F_teórico` = **mispricing** (lo que dispara señal).
- Mockup `BASIS` = `F_mercado − Spot` = **carry**, NO está en el CSV → se calcula al vuelo: `d["basis_fs"] = d["F_mercado"] - d["spot"]`. Ejemplo limpio de "cálculo de presentación" (deriva, no recalcula nada oficial).

**Decisión resuelta — σ-bands vs banda fija → HÍBRIDO:** la señal de arbitraje REAL (semáforo SÍ/NO, acción sugerida, columna SEÑAL) usa la **banda fija 0.5%** del config (economía dura). Las **bandas σ** son solo lente visual en las gráficas de basis y proximidad (fidelidad al mockup), NO disparan decisiones. El humano eligió esto con su intuición: "lo económicamente correcto manda; lo estadístico acompaña".

**Recorrido del dato (el corazón de `dashboard.py`):** CSV (60 filas, formato largo: una por ticker-día) → `df` → filtro a un instrumento → `d` (la "película", ~20 días) → `d.iloc[-1]` = `fila` (la "foto de hoy"). Paneles de números leen de `fila`; gráficas y tabla leen de `d`. Graficar `df` sin filtrar = trampa (mezcla ES~7400 + GC~4500 + SI~75 en una línea ilegible).

#### El recorrido del dato, PASO A PASO (esto *es* `dashboard.py`)

**La forma del CSV — formato "largo":** una fila por **instrumento-día** (no una fila por día con muchas columnas). 60 filas = 3 instrumentos × 20 días. Toda la pantalla sale de filtrar/recortar/hacer cuentas chiquitas sobre esta tabla.

```
fecha        ticker   r       T        spot      F_mercado  F_teorico  basis   señal
2026-06-05   ES=F     0.036   0.038    7416.37   7432.50    7422.99    9.51    SIN SEÑAL
2026-06-05   GC=F     ...
2026-06-05   SI=F     ...
2026-06-04   ES=F     ...      ← mismo instrumento, otro día
```

**El pipeline (orden real de ejecución del archivo):**
```
1. cargar_historico()        →  df   (las 60 filas completas)
2. df.empty? → st.stop()         (guard: sin datos, no pintes nada)
3. hoy = df["fecha"].max()       (¿cuál es el día más reciente?)
4. st.radio(...) → ticker        (¿qué instrumento eligió el usuario? = el "cartel")
5. d = df[df["ticker"]==ticker]  (recorto: SOLO las ~20 filas de ese instrumento)
6. fila = d.iloc[-1]             (la fila del último día = el "hoy" de ese instrumento)
7. cuentas de presentación:      basis_fs, mu, sd, z, carry, desviación...
8. pintar cada panel leyendo de fila / d
```

**Pasos 5-6 son la clave:** de 60 filas → me quedo con las ~20 de *un* instrumento (`d`), y de ésas, la última fila (`fila`) es el "hoy".

| Panel | Lee de | Por qué |
|---|---|---|
| Barra superior, KPIs, tira de métricas, fórmula | **`fila`** | un solo día (escalares: `spot`, `F_mkt`, `F_teo`, `r`, `T`) |
| Gráficas (convergencia, basis, proximidad) | **`d`** | una línea/serie necesita *muchos* días |
| Tabla histórica | **`d`** | las últimas 8 filas |

**Regla mnemónica:** `fila` = "la foto de hoy" · `d` = "la película del instrumento". Los paneles de números usan la foto; los de gráficas usan la película.

**La trampa de `df` sin filtrar:** si graficaras `df` directo, mezclarías ES (~7400) + GC (~4500) + SI (~75) en la misma línea → basura ilegible. Por eso *primero* filtras a un instrumento y *luego* graficas. La decisión de diseño "un instrumento a la vez" del mockup, hecha código.

**Verificación con preview headless:** se usó `.claude/launch.json` + MCP de preview (screenshot + `preview_eval` para medir alturas reales). Lección de tooling: la captura escalada engaña sobre la proporción vertical; medir el DOM (`getBoundingClientRect`) es la verdad.

**Ajuste post-feedback:** el humano pidió más aire entre paneles (chocaban). Se subieron los gaps a `0.9rem`, se quitaron los márgenes negativos, y cada gráfica se envolvió en `st.container(border=True)` con estilo de panel → cada recuadro respira.

### Checklist de comprensión del paso 9.6 (todo ✅)

- [x] `run.py` calcula y escribe / `dashboard.py` lee y muestra (frontera firme: sin correr run.py, ves el último día guardado)
- [x] CSV ≠ base de datos (archivo de texto plano = "memoria")
- [x] Streamlit (armazón) + HTML/CSS (estilo) + Plotly (gráficas); plotly en requirements.txt
- [x] Modelo de re-ejecución: el script corre completo desde la línea 1 en cada interacción ("actor con amnesia")
- [x] Memoria entre reruns: variable normal se reinicia / widget se acuerda solo (cartel) / session_state (pizarra) / cache (decorados pre-armados)
- [x] Dónde se cambia el diseño (diccionario `COL` + `<style>` + `config.toml`)
- [x] Recorrido del dato: `fila` (foto de hoy) vs `d` (película); por qué graficar `df` sin filtrar es trampa
- [x] Decisión σ-bands vs banda fija (eligió híbrido con criterio económico)

### Quiz — respuestas del humano (todas correctas a la primera)

1. *Sin correr run.py hoy, ¿qué ves?* → "El último día que SÍ se corrió" ✅
2. *Contador con variable normal tras 3 clics* → "Siempre 1, nunca sube" ✅ (clavó que necesita session_state)
3. *Convergencia (3 líneas, muchos días), ¿lee de fila o d?* → "De `d`, la película" ✅

### Patrones de enseñanza que funcionaron

- **Analogía unificada del teatro** para el modelo de memoria (actor con amnesia / cartel del espectador / pizarra / decorados pre-armados): el humano pidió explícitamente "explícame con una analogía" y selló los 4 conceptos de una.
- **Tablas comparativas** (cache vs session_state, fila vs d, banda fija vs σ) > prosa.
- El humano sigue anclando bien en código pero pide analogías para conceptos nuevos de infraestructura (reruns, memoria) — su intuición financiera no cubre eso, así que la analogía cotidiana es el puente.
- **Analogía del coche para banda fija vs σ:** límite legal (60 km/h, fijo = costo) = banda fija que multa; "vas más rápido de lo que tú sueles" = banda σ, lucecita informativa que NO multa. El humano no había captado que "híbrido" no es un tercer tipo de banda sino la *decisión* de usar cada una para algo distinto.

### Banda fija vs σ — dónde vive cada una (aclarado en sesión 7)

- **Señal real** (semáforo SÍ/NO, acción, columna SEÑAL, KPI "Desviación") → **banda fija 0.5%** (`F_teorico × 0.005`), igual para los 3 instrumentos. Es economía: ¿el mispricing supera el costo de operar?
- **Bandas σ** → SOLO en las **2 gráficas de la columna derecha**: "Basis vs banda" (franja ±1σ + líneas ±2σ) y "Proximidad" (barras coloreadas por tramo σ + líneas ±2σ). Lente estadística, NO disparan decisiones. Se calculan sobre el basis carry (`Futuro − Spot`).
- El humano detectó solo que la gráfica de proximidad necesitaba también la línea **−2σ** (inferior), no solo +2σ — sin ella, un instrumento con basis negativo (el oro) no tiene referencia de cuándo sale del rango por abajo. **Fix aplicado.**

### ✅ Recalibración del proxy del oro — solución A (2026-06-08, deuda del 9.5 saldada)

**El problema (diagnosticado por el humano en 9.5):** spot del oro = proxy `GLD × 10.96`. El factor estaba ~0.9% alto → inflaba spot → inflaba F_teorico → basis sistemáticamente negativo → 16/20 días "COMPRA FUTURO" falso. *Una señal que nunca se cierra = error de medición, no arbitraje.*

**Se reverificó la solución C (matar el proxy):** se probaron tickers de spot directo en yfinance — `XAUUSD=X` (delisted, 404), `GC=F` (es el futuro), `XAU=F` y `GOLD` (otra cosa: GOLD = acción de Barrick). **No hay spot de oro limpio en yfinance** → C sigue descartada por la misma razón original. Confirmado, no asumido.

**Solución A aplicada — calibrar el número con datos reales (no a ojo):**
- Lógica: el spot proxy debe quedar *alineado con el futuro* (futuro ≈ spot + carry chico). Se sacó la media del ratio `GC=F / GLD` (~10.90) y se ajustó por el carry (~×0.998) → **factor ≈ 10.89.**
- Señal de que el 10.96 estaba mal: daba spot proxy *por encima* del propio futuro (10.96 > ratio real), imposible en contango (el futuro debe estar arriba del spot).
- `config.yaml`: `factor 10.96 → 10.89`.

**Regeneración quirúrgica del CSV (sin re-jalar de yfinance):** el spot escala **lineal** con el factor, y `F_teorico = spot × e^(carry)` (el exponente no depende del factor), así que:
```
nuevo_spot      = viejo_spot      × (10.89/10.96)
nuevo_F_teorico = viejo_F_teorico × (10.89/10.96)
nuevo_basis     = F_mercado − nuevo_F_teorico     (F_mercado = GC=F, intacto)
nueva_señal     = señal_arbitraje(nuevo_basis, nuevo_F_teorico × 0.005)
```
Solo se reescribieron las 20 filas de GC=F; ES=F y SI=F quedaron **byte-idénticas** al backup (verificado). Cero llamadas a la red.

**Resultado:** GC=F pasó de **16 COMPRA / 4 SIN SEÑAL** a **15 SIN SEÑAL / 4 COMPRA / 1 VENDE** (distribución sana, como ES). Basis medio: −0.9% (sesgo) → −0.25% (ruido dentro de banda). El día más reciente (06-05) quedó VENDE FUTURO legítimo (tenía ratio fut/GLD alto ese día).

**Conceptos que reforzó:**
- **Los proxies arrastran sesgos que hay que vigilar** (lección de medición, no de finanzas).
- **Por qué el factor deriva:** GLD cobra comisión vendiendo oro → oro-por-acción baja ~0.4%/año → el factor sube ~0.03%/mes (despreciable mes a mes; el 10.96 estaba viejo, no mal-calculado).
- **Escalado lineal exacto** evita re-jalar datos: cuando una transformación es proporcional, se aplica directo al resultado guardado.

**Deuda futura (opcional):** la solución C (spot directo) requeriría otra fuente de datos fuera de yfinance; el factor habrá que recalibrarlo cada varios meses si se queda en A.

---

## PASO 2 — config.yaml *(próximo)*

> Se documenta cuando lleguemos.

---

## Sesiones

| Sesión | Fecha | Pasos cubiertos | Notas |
|---|---|---|---|
| 1 | 2026-06-03 | Paso 1 | — |
| 2 | 2026-06-04 | Pasos 5, 6, 7 | Intuición financiera muy sólida. Gap principal: conceptos nuevos de código (string, dict, index). Se resuelven con analogías concretas. |
| 3 | 2026-06-05 | Paso 8 (run.py) | Entendió el flujo orquestador completo. Bloques 1-4 y 6 los describió solo. Gap en bloque 5 (la acción dentro del loop) — resuelto con explicación instrumento por instrumento. Aplicó separación de responsabilidades sin que se lo pidieran. |
| 4 | 2026-06-05 | Paso 9 (diseño) | Fase de diseño del dashboard con metodología "Design It Twice" (3 diseños en paralelo). Decisión propia: síntesis A+B+C, estrategia "nativo primero, CSS después". Mostró criterio al elegir empezar simple y construir la estética al final. |
| 5 | 2026-06-07 | Pasos 8.5 + 9 completos | Construyó el spot real (8.5, arregló basis artificial) y los 10 bloques del dashboard (9). Dominó conceptos nuevos: máscaras booleanas, suma de booleanos como conteo, modelo de re-run de Streamlit, `pivot`, atribución de la fórmula, config.toml vs CSS. Analogía propia destacada: if/elif/else = IF anidado de Excel. Cerró proponiendo un rediseño (mockup propio) → planeado como 9.5 (backfill) + 9.6 (rediseño terminal, una pantalla, vista por instrumento). |
| 6 | 2026-06-07 | Paso 9.5 (backfill) | Construyó `backfill.py` + funciones `serie_*` en data.py. Predijo correcto que T era mayor en el pasado (convergencia). Captó por qué solo data.py cambia (separación de responsabilidades → 80% reuso). Entendió ALINEAR series por fecha vs pegar por posición, y el de-dup por (fecha, ticker). **Punto alto:** diagnosticó solo el sesgo del oro (16/20 COMPRA FUTURO = proxy GLD inflado, no arbitraje) — "una señal que no se cierra es error de medición". Gap inicial: no sabía cuál módulo cambia (se enseñó con la tabla de reuso). |
| 7 | 2026-06-08 | Paso 9.6 (rediseño terminal) + recalibración oro | Claude implementó primero el `dashboard.py` fiel al mockup (Plotly + HTML/CSS, una pantalla, vista por instrumento), luego sesión de enseñanza. El humano clavó las 3 preguntas del quiz a la primera. Dominó: frontera run.py/dashboard.py, las 3 capas (Streamlit/HTML-CSS/Plotly), modelo de re-ejecución de Streamlit, memoria entre reruns (variable vs widget vs session_state vs cache), recorrido del dato (fila vs d). Pidió analogía → teatro (actor con amnesia) selló el modelo de memoria. Decisión propia: híbrido σ-bands (visual) + banda fija (señal real). Pidió más aire entre paneles → ajuste de gaps + containers con borde. **Cierre:** detectó solo que faltaba la línea −2σ en proximidad (fix), y pidió ejecutar la solución A del oro: se reverificó que no hay spot directo en yfinance (C descartada), se calibró el factor 10.96→10.89 con datos reales y se regeneró el CSV del oro por escalado lineal exacto (sesgo −0.9%→−0.25%, 16 COMPRA falsos → distribución sana). |

---

## Conceptos financieros aprendidos

*(Se llena con cada paso)*

| Concepto | Definición simple | En qué paso lo aprendiste |
|---|---|---|
| Cost-of-carry | El precio justo de un futuro = precio hoy + lo que cuesta "cargar" el activo hasta el vencimiento | — |
| Basis | F_mercado − F_teórico. La desalineación entre precio real y justo | — |
| EOD | End of Day — precio de cierre, no en vivo | — |
| Librería estándar | Módulos que vienen incluidos con Python (datetime, math, os…). No se instalan, no van en requirements.txt | Paso 4 |
| Librería de terceros | Paquetes hechos por la comunidad (yfinance, pandas…). Se instalan con pip, van en requirements.txt | Paso 4 |
| `for` loop | Itera sobre cada elemento de una lista y ejecuta un bloque de código por cada uno | Paso 4 |
| `return` dentro de `for` | Detiene el loop inmediatamente y devuelve el valor — no sigue iterando | Paso 4 |
| Índices base-0 | En Python los conteos empiezan en 0. Lunes=0, Martes=1… Viernes=4 | Paso 4 |

---

## Patrones de aprendizaje

*(Lo que está funcionando bien para que aprendas)*

> *Se llena durante el proceso*
