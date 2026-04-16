from fastapi import APIRouter
from app.services.query_service import process_question
import sqlite3
import pandas as pd
import google.generativeai as genai
from app.db.connection import get_connection

router = APIRouter()

def run_query(query: str):
    """Función helper para ejecutar SQL y devolver diccionario"""
    conn = None
    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn)

        return df.to_dict('records')

    except Exception as e:
        return None, str(e)

@router.get("/generar_reporte")
def generar_reporte_endpoint():

    anomalias = run_query("""
        SELECT 
            COUNTRY, CITY, ZONE, METRIC, 
            L1W_ROLL, L0W_ROLL,
            ROUND(((L0W_ROLL - L1W_ROLL) / NULLIF(L1W_ROLL, 0)) * 100, 2) AS Porcentaje_Variacion
        FROM metrics_input
        WHERE L1W_ROLL > 0 
        AND ((L0W_ROLL - L1W_ROLL) / NULLIF(L1W_ROLL, 0)) <= -0.10
        ORDER BY Porcentaje_Variacion ASC;
    """)
    
    tendencias = run_query("""
        SELECT 
            COUNTRY, CITY, ZONE, METRIC, 
            L3W_ROLL, L2W_ROLL, L1W_ROLL, L0W_ROLL
        FROM metrics_input
        WHERE L0W_ROLL < L1W_ROLL 
        AND L1W_ROLL < L2W_ROLL 
        AND L2W_ROLL < L3W_ROLL;
    """)

    benchmarking = run_query("""
        WITH Promedios_Liga AS (
            SELECT COUNTRY, ZONE_TYPE, METRIC, AVG(L0W_ROLL) as Promedio_Ideal
            FROM metrics_input
            GROUP BY COUNTRY, ZONE_TYPE, METRIC
        )
        SELECT 
            m.COUNTRY, m.CITY, m.ZONE, m.ZONE_TYPE, m.METRIC, 
            m.L0W_ROLL AS Valor_Actual, 
            p.Promedio_Ideal
        FROM metrics_input m
        JOIN Promedios_Liga p 
        ON m.COUNTRY = p.COUNTRY AND m.ZONE_TYPE = p.ZONE_TYPE AND m.METRIC = p.METRIC
        WHERE m.L0W_ROLL < (p.Promedio_Ideal * 0.80);
    """)

    correlacion = run_query("""
        SELECT 
            m.ZONE, 
            m.L0W_ROLL AS Lead_Penetration, 
            o.L0W AS Total_Orders
        FROM metrics_input m
        JOIN orders_input o 
        ON m.COUNTRY = o.COUNTRY AND m.CITY = o.CITY AND m.ZONE = o.ZONE
        WHERE m.METRIC = 'Lead Penetration' AND m.L0W_ROLL < 0.3
        AND o.METRIC = 'Orders' AND o.L0W < 1000;
    """)

    opportunity = run_query("""
        WITH Estadisticas_Globales AS (
            SELECT METRIC, AVG(L0W_ROLL) as promedio_nacional
            FROM metrics_input
            GROUP BY METRIC
        ),
        Oportunidades_Calculadas AS (
            SELECT 
                m.COUNTRY, m.ZONE, m.METRIC, m.ZONE_PRIORITIZATION,
                m.L0W_ROLL as valor_actual,
                g.promedio_nacional,
                o.L0W as volumen_ordenes,
                -- Calculamos un score de oportunidad (0 a 100)
                ( (g.promedio_nacional - m.L0W_ROLL) / g.promedio_nacional * 40 + 
                (o.L0W / (SELECT MAX(L0W) FROM orders_input) * 40) +
                (CASE WHEN m.ZONE_PRIORITIZATION = 'Tier 1' THEN 20 ELSE 0 END)
                ) as opportunity_score
            FROM metrics_input m
            JOIN orders_input o ON m.ZONE = o.ZONE AND m.COUNTRY = o.COUNTRY
            JOIN Estadisticas_Globales g ON m.METRIC = g.METRIC
            WHERE m.L0W_ROLL < g.promedio_nacional -- Solo donde estamos por debajo
            AND o.METRIC = 'Orders'
        )
        SELECT * FROM Oportunidades_Calculadas 
        ORDER BY opportunity_score DESC 
        LIMIT 5;
    """)

    prompt_maestro = f"""
        Eres el Director de Data Science y Operaciones de Rappi. Tu objetivo es redactar un "Reporte Ejecutivo de Insights Operacionales" en formato Markdown.

        A continuación, te proporciono los datos duros extraídos matemáticamente del motor de reglas:

        DATOS DEL MOTOR ANALÍTICO:
        - ANOMALÍAS: {anomalias}
        - TENDENCIAS: {tendencias}
        - BENCHMARKING: {benchmarking}
        - CORRELACIONES: {correlacion}
        - OPORTUNIDADES: {opportunity}
    
        ESTRUCTURA OBLIGATORIA DEL REPORTE (Sigue este orden y usa estos títulos exactos):

            # Reporte Ejecutivo de Insights Operacionales

            ## Resumen Ejecutivo
            (Redacta un Top 3 a 5 de los hallazgos más críticos a nivel global cruzando toda la información. Ve directo al grano sobre dónde estamos perdiendo más eficiencia o dinero).

            ## Detalle por Categoría de Insight y Recomendaciones
            (Para cada una de las siguientes categorías, explica detalladamente los hallazgos usando los datos duros proporcionados. E inmediatamente después de explicar el hallazgo de la categoría, incluye un sub-bullet llamado "💡 Recomendación Accionable" con una acción operativa específica para resolver ese problema).

            **1. Anomalías (Cambios drásticos >10%):**
            - [Detalle de zonas/métricas afectadas con porcentajes en negrita].
            - 💡 **Recomendación Accionable:** [Tu acción operativa sugerida].

            **2. Tendencias Preocupantes (Deterioro consistente):**
            - [Detalle de las caídas continuas].
            - 💡 **Recomendación Accionable:** [Tu acción operativa sugerida].

            **3. Benchmarking (Performance divergente):**
            - [Comparación de zonas vs sus promedios].
            - 💡 **Recomendación Accionable:** [Tu acción operativa sugerida].

            **4. Correlaciones:**
            - [Relaciones detectadas entre distintas métricas].
            - 💡 **Recomendación Accionable:** [Tu acción operativa sugerida].

            **5. Oportunidades Generales:**
            - [Zonas priorizadas por volumen y brecha de mejora].
            - 💡 **Recomendación Accionable:** [Tu acción operativa sugerida].

            REGLAS ESTRICTAS DE REDACCIÓN:
            1. CERO LENGUAJE DE MÁQUINA: NO menciones que usaste SQL, ni que recibiste diccionarios. Presenta la información como tu propio análisis.
            2. CERO ALUCINACIONES: NO inventes números que no estén en los DATOS.
            3. MANEJO DE VACÍOS: Si alguna categoría viene vacía (ej. []), simplemente indica "Sin alertas relevantes esta semana" y omite la recomendación de ese punto.
                    
            ## Recomendaciones Operativas
            (Da acciones precisas basadas en todo lo anterior).
    """

    modelo_reporte = genai.GenerativeModel('gemini-2.5-flash-lite')
    respuesta = modelo_reporte.generate_content(prompt_maestro)

    return {"reporte_markdown": respuesta.text}

@router.post("/query")
async def query(body: dict):
    try:
        question = body.get("question")
        history = body.get("history", [])

        result = process_question(question, history)

        return result

    except Exception as e:
        return {
            "error": str(e),
            "data": None,
            "sql": None
        }