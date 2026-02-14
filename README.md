# Resource Monitor Studio (PSP · DAM2)

Proyecto de monitorización de recursos del servidor basado en el ejemplo de clase con `psutil`, evolucionado a una solución completa con persistencia SQL y panel gráfico.

## Mejoras funcionales de calado

- Muestreo periódico en segundo plano (thread daemon) con control dinámico del intervalo.
- Captura de métricas: CPU, RAM, disco, espacio libre, red y número de procesos.
- Persistencia en **SQLite** con tablas `metrics` y `alerts`.
- Reglas automáticas de alertas por umbrales (`warning` y `critical`).
- Endpoints REST para serie temporal, rollups por hora/día, estado runtime y alertas.

## Mejoras visuales

- Dashboard moderno con KPI cards.
- Gráfica temporal (líneas) para CPU/RAM/disco.
- Gráfica agregada (barras) por hora o por día.
- Tabla de alertas con codificación visual por severidad.
- Controles de pausa/reanudación y ajuste de intervalo desde UI.

## Estructura

- `app.py` → backend Flask + monitor + SQLite.
- `templates/index.html` → panel de control.
- `static/app.js` → lógica frontend + Chart.js.
- `static/styles.css` → rediseño visual.
- `simulate_spike.py` → simulador de carga para pruebas.

## Ejecución

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abrir en navegador:

- `http://127.0.0.1:5070`

## Prueba de alertas

Con la app levantada:

```bash
python simulate_spike.py
```

Esto genera un pico de CPU para verificar que se registran alertas en el panel.
