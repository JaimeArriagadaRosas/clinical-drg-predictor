# Clinical Intelligence Platform

Plataforma modular de ingeniería de datos y Machine Learning clínico, evolucionada a partir del proyecto universitario original de predicción de Grupos Relacionados por Diagnóstico (GRD).

El objetivo del repositorio es conservar la capacidad de clasificación GRD existente y convertirla en una base reproducible para ML Engineering, analítica clínica, procesamiento batch y streaming, y futuras capacidades de farmacovigilancia basadas en datos públicos.

## Estado

El proyecto se encuentra en una migración controlada desde la implementación académica original hacia un monorepo con backend modular.

- La implementación histórica permanece temporalmente en `src/` como capa de compatibilidad.
- El código nuevo se desarrolla en `apps/`, `packages/` y `pipelines/`.
- Los artefactos generados, modelos y datos procesados no se versionan.
- Hadoop/MapReduce no se conserva como requisito arquitectónico: Spark se incorporará únicamente cuando exista una carga distribuida que lo justifique.

## Arquitectura objetivo

```text
apps/
  api/                  FastAPI / OpenAPI
packages/
  clinical-core/        contratos clínicos compartidos
  clinical-drg/         dominio e inferencia GRD
pipelines/
  training/             entrenamiento y evaluación
  analytics/            procesamiento analítico
  streaming/            procesamiento de eventos
infra/                   runtime y contenedores
tests/                   pruebas automatizadas
docs/                    arquitectura y decisiones
src/                     compatibilidad temporal con la versión académica
```

La organización es un **monorepo** y el backend comienza como **monolito modular**. Los procesos se separan únicamente cuando existen necesidades de ejecución distintas, por ejemplo consumidores Kafka o trabajos Spark.

## Capacidades heredadas

La versión académica incluye:

- procesamiento de historiales clínicos con diagnósticos ICD-10 y procedimientos ICD-9;
- ingeniería de características para clasificación GRD;
- Random Forest y LightGBM como modelos de clasificación;
- API/chatbot clínico con integración opcional de Google Gemini;
- pipeline secuencial de carga, análisis de calidad, preprocesamiento y entrenamiento.

## Dirección tecnológica

La evolución del proyecto utiliza o contempla, según exista un caso de uso real:

- Python 3.11+;
- FastAPI y Pydantic para transporte HTTP y contratos;
- Polars, DuckDB y Parquet para analítica local;
- LightGBM/XGBoost y scikit-learn para modelado;
- MLflow para trazabilidad y ciclo de vida de modelos;
- Kafka mediante `confluent-kafka` para streaming;
- Spark para procesamiento distribuido cuando el volumen lo requiera;
- Docker para reproducibilidad.

## Datos

Los datos clínicos y artefactos de entrenamiento no se consideran código fuente. El repositorio evita versionar resultados generados y modelos serializados. La procedencia y forma de reconstruir datasets se documentará en `docs/data/`.

## Ejecución heredada

Mientras dura la migración, la aplicación original puede iniciarse con:

```bash
python src/main.py
```

El pipeline histórico se puede ejecutar con:

```bash
python src/training/training_main.py
```

La nueva API FastAPI será el punto de entrada oficial una vez completada la primera fase de migración.

## Documentación

La arquitectura y las reglas de migración están documentadas en `docs/architecture/clinical-intelligence-platform.md`.

## Aviso

Este proyecto es de carácter académico y de ingeniería de software/ML. No constituye una herramienta de diagnóstico médico ni sustituye evaluación clínica profesional.
