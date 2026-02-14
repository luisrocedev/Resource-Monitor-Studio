# Paso 4 · Actividad y entrega

**DNI:** 53945291X  
**Curso:** DAM2 - Programación de procesos y servicios  
**Lección:** `301-Actividades final de unidad - Segundo trimestre/003-Monitorización de recursos`

## 1) Descripción del ejercicio personal

Se desarrolla **Resource Monitor Studio**, un sistema de monitorización periódica de servidor inspirado en el ejemplo de clase (`server_monitor.py`) y ampliado a un panel web integral con persistencia SQL y analítica temporal.

## 2) Modificaciones estéticas y visuales (calado alto)

- Rediseño integral del panel en estilo dashboard profesional.
- Tarjetas KPI con estado en tiempo real.
- Gráficas de líneas y barras para visualización histórica y agregada.
- Tabla de alertas con severidad visual y lectura operativa.
- Controles de monitorización interactivos (pausa, reanudación, intervalo).

## 3) Modificaciones funcionales y de base de datos (calado alto)

- Recolección periódica automática con hilo en segundo plano.
- Captura de múltiples recursos de sistema: CPU, RAM, disco, red y procesos.
- Persistencia estructurada en **SQLite**:
  - `metrics` para histórico de muestras.
  - `alerts` para incidencias por umbral.
- Motor de reglas de alertas (`warning`/`critical`) con trazabilidad.
- API REST para explotación de datos:
  - `/api/series` (serie temporal)
  - `/api/rollup` (agregación hora/día)
  - `/api/stats` (estado global)
  - `/api/control` (control runtime)

## 4) Justificación de cumplimiento de rúbrica

- Se cumple la temática de clase (monitorización de recursos) con ampliación técnica avanzada.
- Se aportan cambios visuales profundos y medibles.
- Se aportan cambios funcionales y de base de datos de mucho calado, propios de segundo curso.
- La solución queda preparada para ejecución, validación y demostración en entrega final.
