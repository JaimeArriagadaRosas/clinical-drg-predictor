# 1. Introducción

Este proyecto desarrolla un sistema de inteligencia artificial para predecir el Grupo Relacionado por Diagnóstico (GRD) en el Hospital El Pino, utilizando un modelo de Random Forest entrenado con 14561 historiales clínicos que contienen diagnósticos ICD-10, procedimientos ICD-9 y datos demográficos. El sistema incluye una interfaz de chatbot basada en Flask que permite a los usuarios ingresar información clínica en lenguaje natural, extrae automáticamente las features médicas relevantes mediante expresiones regulares, y genera predicciones del GRD con su nivel de confianza, complementadas con explicaciones en lenguaje natural generadas por la API de Gemini de Google. La arquitectura modular separa claramente las capas de datos, preprocesamiento, entrenamiento y servicio, permitiendo actualizaciones independientes y escalabilidad del modelo.

# 2. Formas de ejecución.

El proyecto se ejecuta de tres formas principales: 

1) Menú interactivo mediante python src/main.py que presenta opciones para entrenamiento completo o chatbot.

2) Pipeline de entrenamiento con python src/training/training_main.py que ejecuta las 4 etapas secuenciales (carga, calidad, preprocesamiento y entrenamiento), o individualmente cada script 01_load_data.py, 02_quality_analysis.py, 03_preprocessing.py y 04_train_models.py con sus respectivos flags como --data-path, --min-samples, --n-estimators;

3) Chatbot API mediante python -m src.api.app o python src/api/app.py que levanta el servidor Flask en http://localhost:5000 con interfaz web embebida, o ejecutando test_chatbot.py para verificar la integración completa de componentes.

# 3. Explicación de las carpetas.

- **config/**: Archivos de configuración y variables de entorno del proyecto.
- **dataset/**: Almacena los datos crudos y procesados. Aquí se ubica el archivo de datos principal.
- **docs/**: Documentación del proyecto.
- **models/**: Directorio donde se guardan los modelos entrenados y métricas.
- **notebook/**: Jupyter notebooks para análisis exploratorio de datos (EDA) y experimentación.
- **src/**: Código fuente principal del proyecto.
  - **api/**: Código del servidor Flask, extracción de features, y cliente de la API de Gemini.
  - **training/**: Scripts para el pipeline de entrenamiento de los modelos.
  - **main.py**: Menú interactivo unificado para ejecutar la aplicación.

# 4. Tecnicas usadas.

Las técnicas implementadas incluyen: Procesamiento de lenguaje natural con expresiones regulares para extracción automática de códigos ICD-10/ICD-9, edad y sexo desde texto libre; Ingeniería de características mediante codificación binaria one-hot para los 808 features (500 diagnósticos + 300 procedimientos + 7 grupos etarios + sexo); Modelado con Random Forest (200 árboles, class_weight='balanced', max_features='sqrt') y LightGBM como alternativa, ambos con validación stratified train/test split; Manejo de desbalance de clases mediante filtrado de clases minoritarias (<2 muestras) y pesos balanceados; y Arquitectura de microservicios con capas separadas para API REST (Flask), extracción de features y servicios externos (Google Gemini) con fallback automático.

## 4.1 API de Gemini.

Se utiliza la API de Google Gemini para traducir los resultados de la predicción del modelo (GRD) a un lenguaje natural y comprensible para el usuario. Esta integración enriquece la experiencia proporcionando contexto médico adicional y explicaciones claras sobre la condición inferida. Requiere la configuración de una clave de API (`GEMINI_API_KEY`) en un archivo `.env` en la raíz del proyecto.

Para obtener una API Key de Gemini, debes dirigirte a la plataforma Google AI Studio e iniciar sesión con tu cuenta de Google. Una vez dentro, busca en el menú lateral izquierdo la opción "Get API key" y haz clic en el botón azul que dice "Create API key". El sistema te pedirá que selecciones un proyecto de Google Cloud existente o que crees uno nuevo automáticamente; tras confirmar, se generará una clave alfanumérica única. Solo debes copiar esta clave y pegarla en tu archivo .env bajo la variable GEMINI_API_KEY=tu_clave_aqui, asegurándote siempre de no compartirla ni subirla a repositorios públicos.

# 5. Funcionamiento del Modelo.

El modelo opera mediante un flujo de cuatro etapas: 1) Recepción de texto donde el usuario describe síntomas/enfermedades en lenguaje natural ("mujer de 35 años con diabetes ICD-10 E11.9"); 2) Extracción de features donde el GRDFeatureExtractor aplica expresiones regulares para identificar y codificar códigos médicos (ICD-10/ICD-9), edad (mapeada a 7 grupos etarios) y sexo en un vector binario de 808 posiciones; 3) Predicción con Random Forest que procesa el vector binario a través de 200 árboles de decisión entrenados con class_weight='balanced' para manejar el desbalance de las 262 clases GRD; 4) Post-procesamiento donde se decodifica la clase predicha usando LabelEncoder, se calcula la confianza como probabilidad máxima, y se generan las 3 predicciones más probables junto con una explicación médica mediante la API de Gemini.

# 6. Flujo del proyecto.

El flujo principal de la aplicación se gestiona mediante el archivo `src/main.py`, que ofrece el siguiente menú interactivo multiplataforma:

1. **Entrenar modelo**: Permite entrenar con valores por defecto (Random Forest) o personalizar parámetros (cantidad de árboles, profundidad y uso de LightGBM).
2. **Iniciar Chatbot**: Levanta el servidor Flask para interactuar con el modelo predictivo desde el navegador en el puerto 5000.
3. **Ver historial de entrenamientos**: Muestra las métricas obtenidas en ejecuciones anteriores.
4. **Salir**: Termina la ejecución.

# 7. Capas del código.
En esta sección se presentan las capaz de este proyecto.

## 7.1. Capa de Datos (Data Layer)
  
Archivo: src/training/01_load_data.py
Función: Carga el dataset desde dataset/dataset_elpino.csv (2,978 registros hospitalarios)
Procesamiento: Detecta columnas de diagnósticos (ICD-10) y procedimientos (ICD-9)

## 7.2. Capa de Calidad (Quality Layer)
Archivo: src/training/02_quality_analysis.py
Análisis: Completitud, validación de formatos ICD, detección de outliers en edad

## 7.3. Capa de Preprocesamiento (Preprocessing Layer)
Archivo: src/training/03_preprocessing.py
Transformaciones:
Filtrado de clases GRD rare (frecuencia < 2)
Creación de features binarias: 500 ICD-10 + 300 ICD-9
Features demográficos: grupos etarios (7) + sexo
Codificación target con LabelEncoder

## 7.4. Capa de API (API Layer)
Archivo: src/api/app.py
Funciones:
Endpoints / (interfaz web), /health, /chat
Orquesta predicción + respuesta en lenguaje natural

## 7.5. Capa de Extracción de Features (Feature Extraction Layer)
Archivo: src/api/feature_extractor.py
GRDFeatureExtractor: Convierte texto conversacional → vector de 808 features
Regex patterns: ICD-10 (E11.9), ICD-9 (39.95), edad, sexo

## 7.6. Capa de IA Externa (External AI Layer)
Archivo: src/api/gemini_api.py
GeminiClient: Genera explicaciones médicas en lenguaje natural
Fallback: Mensaje estático si API no disponible
