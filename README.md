Sistema de Análisis Inteligente para Operaciones Rappi

Esta herramienta transforma el lenguaje natural en consultas SQL precisas, infiere visualizaciones y genera reportes ejecutivos en tiempo real.

Arquitectura y Stack Tecnológico
Frontend: Streamlit(intefaz interactiva y diseño de gráficos)
Backend: FastAPI
Base de Datos: SQLite
LLM/inferencia: Gemini 2.5 Flash-Lite (Vía Google AI Studio)
Data & Visualización: Pandas y Plotly Express

Instalación y Configuración
Para realizar la instalación del proyecto es necesario tener Python instalado, para ello utilizaremos la versión 3.14.4 o versiones similares. Se recomienda crear un entorno virtual para realizar la instalación de las librerías y tecnologías sin que intervengan con otras instalaciones o versiones.

Clonar el repositorio:
Una vez establecido el lugar donde se va a alojar el proyecto podemos iniciar clonando el repositorio:

git clone [link] 
cd nombre-del-repo

Instalación de tecnologías necesarias:
Una vez clonado el repositorio hay que posicionarnos en la carpeta backend para instalar las tecnologías necesarias:

cd backend
pip install -r requirements.txt

Configuración de Variables de Entorno:
Crearemos un archivo .env en la raíz del proyecto y agregaremos la clave de API de Gemini:

GEMINI_API_KEY=tu_clave_API_Gemini

Para conseguir la clave API hay que ingresar al siguiente link (https://aistudio.google.com/) y crear una clave de API, esta API cuenta con un trial de prueba gratuito con cierto numero de consultas limitado, se recomienda agregar una cuenta de facturación para poder acceder a más consultas y que el proyecto pueda funcionar adecuadamente sin limitaciones. El LLM a utilizar es Gemini 2.5 Flash-Lite, este modelo de lenguaje se basa en tokens, gastando tokens dependiendo de la complejidad de las preguntas y de las respuestas, teniendo un costo de $0.075 USD/1M de tokens para inputs(preguntas) y $0.30 USD/1M de tokens para outputs(respuestas), aproximadamente el proyecto tiene un gasto de 20,000 tokens input y 5,000 tokens output en 10 preguntas, lo que equivaldría a un gasto de $0.0030 USD por cada 10 preguntas.

Creación de Base de Datos:
una vez clonado el repositorio hay que crear la base de datos SQLite, la cual es de ayuda para el funcionamiento local, sin embargo se creo la estructura para hacer el cambio o bases de datos más escalables como PostgresSQL. Para crearla debemos posicionarnos dentro de la carpeta backend y ejecutar el script de extraccion_db.py. Este proceso debe hacerse solo una vez.

cd backend
python extraccion_db.py

Ejecución de la aplicación:
El sistema funciona con una arquitectura de dos capas, para ello se necesitan abrir dos terminales, una para levantar el backend y otra para levantar el frontend:

En la primera terminal debemos estar en el directorio raíz, de ahi navegamos a la carpeta backend y ejecutamos el comando de ejecución:

cd backend
uvicorn app.main:app --reload

En la segunda terminal debemos estar en el directorio raíz, de ahi navegamos a la carpeta frontend y ejecutamos el comando de ejecución:

cd frontend
streamlit run app.py

Y listo, puedes hacer uso de la aplicación, si tienes algún problema en la instalación se recomienda eliminar y volver a ejecutar los pasos. 
