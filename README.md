<div align="center">

# Resource Monitor Studio

**Monitorización de recursos del sistema en tiempo real · psutil · Flask · SQLite · Chart.js**

![Python](https://img.shields.io/badge/Python_3.13-3776AB?logo=python&logoColor=fff)
![Flask](https://img.shields.io/badge/Flask-000?logo=flask&logoColor=fff)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=fff)
![Chart.js](https://img.shields.io/badge/Chart.js-FF6384?logo=chartdotjs&logoColor=fff)
![psutil](https://img.shields.io/badge/psutil-292929?logo=python&logoColor=fff)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

---

## Resumen

**Resource Monitor Studio** es un sistema completo de monitorización que recolecta métricas del sistema (CPU, RAM, disco, red, procesos) cada N segundos mediante un thread en segundo plano con `psutil`, las almacena en SQLite con series temporales, evalúa reglas de alerta por umbrales (`warning` / `critical`) y visualiza todo en un dashboard web con gráficas Chart.js interactivas.

---

## Características principales

| Característica            | Detalle                                                                             |
| ------------------------- | ----------------------------------------------------------------------------------- |
| **Muestreo periódico**    | Thread daemon con intervalo configurable (0.5 – 60 s)                               |
| **Métricas**              | CPU % · RAM % · Disco % · Espacio libre · Red TX/RX · Procesos activos              |
| **Alertas automáticas**   | Reglas warning/critical con umbral, trazabilidad y persistencia                     |
| **API REST**              | `/api/stats` · `/api/series` · `/api/rollup` · `/api/alerts` · `/api/control`       |
| **Rollup**                | Promedios agregados por hora o por día                                              |
| **Dashboard**             | 3 pestañas: Dashboard · Alertas · Control                                           |
| **KPI strip**             | 6 indicadores con borde lateral semántico (azul, cian, verde, ámbar, violeta, rojo) |
| **Dark mode**             | Toggle manual + `prefers-color-scheme` + Chart.js adaptativo                        |
| **Toasts**                | Notificaciones contextuales: success · error · info · warning                       |
| **Confirm personalizado** | Overlay con `backdrop-filter` en lugar de `confirm()` nativo                        |
| **Export / Import**       | JSON con stats + series + alertas · Importación con validación                      |
| **Pills de severidad**    | `sev-warning` (ámbar) · `sev-critical` (rojo)                                       |
| **Filtros de alertas**    | Búsqueda textual + selector de severidad en memoria                                 |
| **Indicador de estado**   | Punto animado (`pulse`) verde/ámbar con texto descriptivo                           |
| **Gráficas mejoradas**    | `fill: true`, ejes adaptativos, `maxTicksLimit`                                     |
| **Responsive**            | 3 breakpoints: escritorio (6 col KPI) · tablet (3 col) · móvil (2 col)              |

---

## Inicio rápido

```bash
git clone https://github.com/luisrocedev/Resource-Monitor-Studio.git
cd Resource-Monitor-Studio
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abrir en navegador: **http://127.0.0.1:5070**

### Prueba de alertas

Con la app levantada:

```bash
python simulate_spike.py
```

Genera un pico de CPU durante ~12 s para verificar que se registran alertas en el panel.

---

## Estructura del proyecto

```
Resource-Monitor-Studio/
├── app.py               → Backend Flask + sampler thread + SQLite + API REST
├── simulate_spike.py    → Generador de pico CPU para pruebas
├── demo_simple.py       → Demo simplificada sin Flask
├── requirements.txt     → Flask + psutil
├── templates/
│   └── index.html       → SPA: header, tabs, KPIs, gráficas, alertas, control
├── static/
│   ├── app.js           → Dark mode, tabs, toasts, confirm, export/import, Chart.js
│   └── styles.css       → CSS vars, dark mode, tabs, KPIs, pills, responsive
└── docs/
    └── Actividad_Monitorizacion_Recursos_53945291X.md
```

---

## Arquitectura

```
┌────────────────────────────────────────────┐
│  Sampler Thread (psutil)                   │
│  CPU · RAM · Disco · Red · Procesos        │
│  Intervalo configurable (runtime)          │
└───────────────┬────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────┐
│  Alert Engine                              │
│  Reglas warning / critical con umbrales    │
└───────────────┬────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────┐
│  SQLite (metrics + alerts)                 │
│  Índices por epoch y severidad             │
└───────────────┬────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────┐
│  Flask API REST                            │
│  /api/stats · /api/series · /api/rollup    │
│  /api/alerts · /api/control                │
└───────────────┬────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────┐
│  Dashboard (HTML + CSS + JS + Chart.js)    │
│  Tabs · KPIs · Gráficas · Alertas · Dark   │
└────────────────────────────────────────────┘
```

---

## API REST

| Método | Endpoint                     | Descripción                                                       |
| ------ | ---------------------------- | ----------------------------------------------------------------- |
| `GET`  | `/api/stats`                 | Estado global: muestras totales, alertas, última métrica, runtime |
| `GET`  | `/api/series?limit=N`        | Serie temporal de métricas (últimas N)                            |
| `GET`  | `/api/rollup?mode=hour\|day` | Promedios agregados por hora o día                                |
| `GET`  | `/api/alerts?limit=N`        | Historial de alertas                                              |
| `POST` | `/api/control`               | `{ "action": "pause" \| "resume" \| "interval", "value": N }`     |

---

## Tecnologías

- **Python 3.13** — Threading, SQLite, API REST
- **Flask** — Servidor HTTP + rutas REST
- **psutil** — Métricas de CPU, RAM, disco, red, procesos
- **SQLite** — Persistencia con series temporales + alertas
- **Chart.js** — Gráficas de línea y barras en tiempo real
- **CSS3** — Custom properties, `color-mix()`, `backdrop-filter`, dark mode
- **JavaScript ES6** — `async/await`, `Promise`, DOM reactivo

---

## Autor

**Luis Rodriguez cedeño** · DAM2 — Programación de servicios y procesos

---

## Licencia

MIT
