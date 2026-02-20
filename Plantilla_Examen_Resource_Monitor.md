# Resource-Monitor-Studio — Plantilla de Examen

**Alumno:** Luis Rodríguez Cedeño · **DNI:** 53945291X  
**Módulo:** Programación de Servicios y Procesos · **Curso:** DAM2 2025/26

---

## 1. Introducción

- **Qué es:** Monitor de recursos hardware (CPU, RAM, disco, red) con muestreo concurrente, alertas automáticas y dashboard Chart.js
- **Contexto:** Módulo de PSP — hilos daemon, muestreo periódico, SQLite time-series, API REST, alerta por umbrales
- **Objetivos principales:**
  - Muestreo de métricas con `psutil` (CPU, RAM, disco, red, procesos)
  - Hilo daemon (`threading.Thread`) que muestrea en intervalos configurables
  - Almacenamiento en SQLite time-series + aggregaciones (rollup hora/día)
  - Motor de alertas con reglas de umbral (warning/critical)
  - Dashboard web con Chart.js y control de pausa/reanudación/intervalo
- **Tecnologías clave:**
  - Python 3.11, `psutil` (métricas hardware), `threading` (hilo daemon)
  - SQLite (`sqlite3`), Flask (API REST), Chart.js (frontend), `strftime` SQL
- **Arquitectura:** `app.py` (248 líneas: muestreo + alertas + API REST) → `templates/index.html` (dashboard) → `static/app.js` (Chart.js + auto-refresh) → `static/styles.css`

---

## 2. Desarrollo de las partes

### 2.1 Muestreo con psutil

- `collect_sample()` → lee CPU, RAM, disco, red, procesos en un diccionario
- Cada métrica usa una función específica de `psutil`
- Se ejecuta dentro del hilo sampler

```python
import psutil

def collect_sample() -> dict:
    """Capturar métricas instantáneas del sistema."""
    net = psutil.net_io_counters()
    return {
        "cpu_percent":   psutil.cpu_percent(interval=0.3),
        "ram_percent":   psutil.virtual_memory().percent,
        "ram_used_mb":   round(psutil.virtual_memory().used / (1024**2), 1),
        "disk_percent":  psutil.disk_usage('/').percent,
        "disk_used_gb":  round(psutil.disk_usage('/').used / (1024**3), 2),
        "net_sent_mb":   round(net.bytes_sent / (1024**2), 2),
        "net_recv_mb":   round(net.bytes_recv / (1024**2), 2),
        "processes":     len(psutil.pids()),
    }
```

> **Explicación:** `psutil.cpu_percent(interval=0.3)` bloquea 300ms para medir CPU real. `virtual_memory()` devuelve RAM (percent, used). `disk_usage('/')` mide el disco raíz. `net_io_counters()` acumula bytes enviados/recibidos.

### 2.2 Hilo daemon — Sampler periódico

- `threading.Thread(target=sampler_loop, daemon=True)` → hilo background
- `daemon=True` → se cierra automáticamente al cerrar la app
- Control: pausa/reanudación/cambio de intervalo via API

```python
import threading
import time

sampler_interval = 4     # segundos entre muestras
sampler_paused = False

def sampler_loop():
    """Bucle de muestreo en hilo daemon."""
    while True:
        if not sampler_paused:
            sample = collect_sample()
            insert_metric(sample)        # SQLite
            evaluate_alerts(sample)      # motor de alertas
        time.sleep(sampler_interval)

# Arrancar hilo daemon
sampler_thread = threading.Thread(target=sampler_loop, daemon=True)
sampler_thread.start()
```

> **Explicación:** El hilo daemon ejecuta un bucle infinito: muestrea, guarda en SQLite, evalúa alertas y duerme N segundos. `daemon=True` significa que el hilo muere cuando el proceso principal termina, sin necesidad de cleanup explícito.

### 2.3 SQLite time-series + Rollup

- `INSERT` cada muestra con timestamp `datetime('now')`
- Rollup por hora/día: `strftime('%Y-%m-%d %H', ts)` agrupa y calcula AVG/MAX
- Purgado automático de datos antiguos (>7 días)

```python
def insert_metric(sample: dict):
    """Insertar muestra en SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO metrics (ts, cpu, ram, ram_mb, disk, disk_gb, net_sent, net_recv, procs)
        VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)
    """, (sample['cpu_percent'], sample['ram_percent'], sample['ram_used_mb'],
          sample['disk_percent'], sample['disk_used_gb'],
          sample['net_sent_mb'], sample['net_recv_mb'], sample['processes']))
    conn.commit()
    conn.close()

@app.get("/api/rollup")
def rollup():
    """Agregaciones por ventana temporal."""
    bucket = request.args.get("bucket", "hour")  # 'hour' o 'day'
    fmt = '%Y-%m-%d %H' if bucket == 'hour' else '%Y-%m-%d'
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(f"""
        SELECT strftime('{fmt}', ts) AS period,
               ROUND(AVG(cpu),1) AS avg_cpu,
               ROUND(MAX(cpu),1) AS max_cpu,
               ROUND(AVG(ram),1) AS avg_ram
        FROM metrics
        GROUP BY period ORDER BY period DESC LIMIT 24
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])
```

> **Explicación:** Cada muestra se guarda con timestamp SQLite. El rollup agrupa por hora o día usando `strftime`, calculando promedios y máximos. Esto permite mostrar tendencias sin enviar miles de puntos al frontend.

### 2.4 Motor de alertas con umbrales

- Reglas: CPU > 92% = critical, > 80% = warning; RAM ídem; Disco > 88% = critical
- Cada alerta tiene: métrica, valor, nivel, timestamp
- Se almacena en tabla `alerts` de SQLite

```python
ALERT_RULES = [
    {"metric": "cpu", "field": "cpu_percent", "warning": 80, "critical": 92},
    {"metric": "ram", "field": "ram_percent", "warning": 80, "critical": 92},
    {"metric": "disk", "field": "disk_percent", "warning": 80, "critical": 88},
]

def evaluate_alerts(sample: dict):
    """Evaluar reglas de alerta contra la muestra actual."""
    for rule in ALERT_RULES:
        value = sample.get(rule["field"], 0)
        level = None
        if value >= rule["critical"]:
            level = "critical"
        elif value >= rule["warning"]:
            level = "warning"
        if level:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("INSERT INTO alerts (ts, metric, value, level) VALUES (datetime('now'),?,?,?)",
                         (rule["metric"], value, level))
            conn.commit()
            conn.close()
```

> **Explicación:** Tras cada muestra, se compara cada métrica contra sus umbrales. Si supera el umbral warning o critical, se registra una alerta en SQLite. Esto permite un historial completo de incidencias del sistema.

### 2.5 API REST — Control del sampler

- `/api/stats` → KPIs (última muestra, promedios 1h, contadores alertas)
- `/api/series` → últimas N muestras para Chart.js
- `/api/control` → POST para pause/resume/interval

```python
@app.post("/api/control")
def control():
    """Pausar, reanudar o cambiar intervalo del sampler."""
    global sampler_paused, sampler_interval
    data = request.get_json(silent=True) or {}
    action = data.get("action")

    if action == "pause":
        sampler_paused = True
    elif action == "resume":
        sampler_paused = False
    elif action == "interval":
        sampler_interval = max(1, min(int(data.get("value", 4)), 60))

    return jsonify({"ok": True, "paused": sampler_paused, "interval": sampler_interval})
```

> **Explicación:** El endpoint `/api/control` permite pausar/reanudar el muestreo y cambiar el intervalo. Se usan variables globales (`sampler_paused`, `sampler_interval`) que el hilo daemon lee en cada iteración.

---

## 3. Presentación del proyecto

- **Flujo:** App arranca → hilo daemon muestrea cada 4s → SQLite acumula → Dashboard poll cada 4s → Chart.js muestra gráficas → Alertas si umbral superado
- **Demo:** `python app.py` → abrir `localhost:5053` → ver métricas en vivo → pausar/reanudar → ver alertas
- **Concurrencia:** Hilo daemon + servidor Flask principal = 2 hilos concurrentes

---

## 4. Conclusión

- **Competencias:** `threading` daemon, `psutil` monitoring, SQLite time-series, rollup SQL, alertas por umbral
- **Concepto PSP:** Hilo daemon para tarea periódica sin bloquear el servidor
- **Seguridad:** Validación de intervalos (clamping min/max), no expone datos sensibles
- **Extensibilidad:** Añadir más métricas = ampliar `collect_sample()` y reglas de alerta
- **Valoración:** Sistema de monitorización profesional con concurrencia real y dashboard interactivo
