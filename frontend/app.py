import streamlit as st
import sqlite3
import requests
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import plotly.express as px
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

st.set_page_config(page_title="Rappi Ops AI", page_icon="", layout="wide")
hide_streamlit_style = """
<style>
    [data-testid="stToolbar"] {visibility: hidden !important;}
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
</style>
"""
st.title("Asistente de Operaciones SP&A - Rappi")
st.markdown("Sistema inteligente, intenta hacer preguntas lo más específicas posibles")

with st.sidebar:
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
    st.header("Reporte Ejecutivo")
    st.markdown("Generar reporte ejecutivo con insights más relevantes")

    if st.button("Generar Reporte Automático", type="secondary", use_container_width=True):

        st.session_state.mostrar_reporte = True

if st.session_state.get("mostrar_reporte", False):
    
    # Este spinner se mostrará mientras FastAPI y SQLite hacen el trabajo pesado
    with st.container():
        
        with st.spinner("Generando Reporte..."):
            try:
                url_backend = "http://127.0.0.1:8000/generar_reporte"
                response = requests.get(url_backend, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    reporte_md = data.get("reporte_markdown", "No se recibió contenido.")
                    st.markdown(reporte_md)
                    st.download_button(
                        label="Descargar Reporte (Markdown)",
                        data=reporte_md,
                        file_name="reporte_operaciones_rappi.md",
                        mime="text/markdown"
                    )
                else:
                    st.error(f"Error del servidor ({response.status_code}): No se pudo generar el reporte.")
            
            except requests.exceptions.ConnectionError:
                st.error("No se pudo conectar con el Backend. ¿Está corriendo FastAPI en localhost:8000?")
            except Exception as e:
                st.error(f"Ocurrió un error inesperado: {e}")
        
        st.markdown("---")
        if st.button("Cerrar Reporte", use_container_width=True):
            st.session_state.mostrar_reporte = False
            st.rerun()
        

# --- INICIALIZAR MEMORIA Y CHAT ---
if "history" not in st.session_state:
    st.session_state.history = []

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "¡Hola! Estoy listo para analizar las métricas."}]

if "chat_session" not in st.session_state and api_key:
    # Iniciamos la sesión de chat nativa de Gemini para la memoria
    st.session_state.chat_session = model.start_chat(history=[])

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- MOTOR PRINCIPAL ---
if user_question := st.chat_input("Escribe tu pregunta, intenta específicar ciudades, zonas y terminos"):

    st.session_state.messages.append({"role": "user", "content": user_question})

    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        with st.spinner("Consultando backend..."):

            try:
                response = requests.post(
                    "http://127.0.0.1:8000/query",
                    json={
                        "question": user_question,
                        "history": st.session_state.history[-6:]
                    },
                    timeout=60
                )

                #print("Status code:", response.status_code)
                #print("Response text:", response.text)

                data = response.json()

            except Exception as e:
                st.error(f"Error conectando con backend: {e}")
                st.stop()

        #  Manejo de error
        if data.get("error"):
            msg = f"Error: {data['error']}"
            st.error(msg)
            st.session_state.messages.append({"role": "assistant", "content": msg})

        else:
            df = pd.DataFrame(data["data"])

            # Mostrar tabla
            #st.dataframe(df, use_container_width=True)

            # Mostrar SQL
            #with st.expander("Ver SQL generado"):
             #   st.code(data["sql"], language="sql")

            # Mostrar autocorrección si ocurrió
            if data.get("attempts", 0) > 0:
                st.dialog(f"Se esta profundizando más la petición, intentos: {data['attempts']}")
            
            with st.spinner("Generando insight..."):
                prompt_insight = f"""
                El usuario preguntó: '{user_question}'
                Los datos de la base de datos arrojaron esto: {df.head(10).to_dict()}

                Tu tarea como Analista Senior de Rappi es doble:
                1. Redacta un insight ejecutivo muy breve (1 o 2 párrafos) respondiendo a la pregunta original basándote en los números. No menciones que usaste SQL.
                2. Sugerencias Proactivas: Al final de tu respuesta, agrega una sección llamada "💡 Siguientes pasos sugeridos:" y propón 2 preguntas analíticas de seguimiento que el usuario podría hacerte para profundizar en el problema detectado.

                REGLA DE VISUALIZACIÓN:
                Al final de todo tu texto, añade OBLIGATORIAMENTE una de estas etiquetas exactas según lo que mejor represente a los datos que estás viendo:
                - [VISUAL: LINEAS] -> Si los datos muestran evolución (tienen columnas de tiempo L8W-L0W).
                - [VISUAL: BARRAS] -> Si comparas magnitudes entre diferentes zonas, países o categorías.
                - [VISUAL: TABLA] -> Si es una lista muy diversa o no hay una comparación clara.
                - [VISUAL: NINGUNO] -> Si la respuesta es un solo valor o no amerita gráfico.
                """

                response_insight = genai.GenerativeModel('gemini-2.5-flash-lite').generate_content(prompt_insight)
                respuesta_cruda = response_insight.text
                texto_limpio = respuesta_cruda
                tipo_grafico = "NINGUNO"
                
                if "[VISUAL: BARRAS]" in respuesta_cruda:
                    tipo_grafico = "BARRAS"
                    texto_limpio = respuesta_cruda.replace("[VISUAL: BARRAS]", "").strip()
                elif "[VISUAL: LINEAS]" in respuesta_cruda:
                    tipo_grafico = "LINEAS"
                    texto_limpio = respuesta_cruda.replace("[VISUAL: LINEAS]", "").strip()
                elif "[VISUAL: TABLA]" in respuesta_cruda:
                    tipo_grafico = "TABLA"
                    texto_limpio = respuesta_cruda.replace("[VISUAL: TABLA]", "").strip()
                elif "[VISUAL: NINGUNO]" in respuesta_cruda:
                    texto_limpio = respuesta_cruda.replace("[VISUAL: NINGUNO]", "").strip()

                st.markdown(texto_limpio)

                if not df.empty:
                    try:
                        if tipo_grafico == "BARRAS":
                            # Columnas para graficas barras
                            fig = px.bar(df, x=df.columns[0], y=df.columns[1], color=df.columns[0])
                            st.plotly_chart(fig, use_container_width=True)

                        elif tipo_grafico == "LINEAS":
                            # gráficas de tiempo
                            if any("L" in col for col in df.columns):
                                # Convertimos las columnas en filas para que Plotly las entienda
                                df_melted = df.melt(id_vars=[df.columns[0]], var_name='Semana', value_name='Valor')
                                fig = px.line(df_melted, x='Semana', y='Valor', color=df.columns[0], markers=True)
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                fig = px.line(df, x=df.columns[0], y=df.columns[1], markers=True)
                                st.plotly_chart(fig, use_container_width=True)
                                
                        elif tipo_grafico == "TABLA":
                            if not df.empty:
                                st.dataframe(df, use_container_width=True)

                        elif tipo_grafico == "NINGUNO":
                            if not df.empty:
                                st.dataframe(df, use_container_width=True)

                    except Exception as e:
                         if not df.empty:
                            st.dataframe(df, use_container_width=True)

           # if not df.empty:
            #    st.dataframe(df, use_container_width=True)

            #st.dataframe(df, use_container_width=True)
            st.session_state.messages.append({"role": "assistant", "content": texto_limpio})

            st.session_state.history.append({
                "role": "user",
                "content": user_question
            })

            st.session_state.history.append({
                "role": "assistant",
                "content": data["sql"]
            })