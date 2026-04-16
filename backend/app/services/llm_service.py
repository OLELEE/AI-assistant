import os
import google.generativeai as genai
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("¡ALERTA! No se encontró la API Key. Revisa tu archivo .env")

genai.configure(api_key=api_key)

SQL_SYSTEM_PROMPT = """
Eres un experto AI Engineer de Rappi. Tu tarea es responder con SQL para SQLite.

# ESQUEMA EXACTO DE TABLAS:
1. metrics_input (COUNTRY, CITY, ZONE, ZONE_TYPE, ZONE_PRIORITIZATION, METRIC, L8W_ROLL, L7W_ROLL, L6W_ROLL, L5W_ROLL, L4W_ROLL, L3W_ROLL, L2W_ROLL, L1W_ROLL, L0W_ROLL)
   - L0W_ROLL es la semana actual, L8W_ROLL es hace 8 semanas.
   - COUNTRY: Los paises estan en el formato Código de país (AR, BR, CL, CO, CR, EC, MX, PE, UY) 
2. orders_input (COUNTRY, CITY, ZONE, METRIC, L8W, L7W, L6W, L5W, L4W, L3W, L2W, L1W, L0W)
   - La columna METRIC siempre es 'Orders'.

# DICCIONARIO DE MÉTRICAS (CONTEXTO):
- Perfect Orders: Orders sin cancelaciones o defectos o demora / Total de órdenes.
- Lead Penetration: Tiendas habilitadas / (Prospectos + habilitadas + salidas).
- Gross Profit UE: Margen bruto de ganancia / Total de órdenes.
- Pro Adoption: Usuarios suscripción Pro / Total usuarios.
- Non-Pro PTC > OP: Conversión usuarios No Pro de Proceed to Checkout a Order Placed.
- Restaurants SS > ATC CVR: Conversión de Select Store a Add to Cart.
- % PRO Users Who Breakeven: Usuarios con suscripción Pro cuyo valor generado para la empresa (a través de compras, comisiones, etc.) ha cubierto el costo total de su membresía  / Total de usuarios suscripción Pro
- % Restaurants Sessions With Optimal Assortment: Sesiones con un mínimo de 40 restaurantes/ Total de sesiones 
- MLTV Top Verticals Adoption: Usuarios con órdenes en diferentes verticales (restaurantes, super, pharmacy, liquors) / Total usuarios. 
- Restaurants Markdowns / GMV: Descuentos totales en órdenes de restaurantes  / Total Gross Merchandise Value Restaurantes
- Restaurants SST > SS CVR:  Porcentaje de usuarios que, después de seleccionar un Restaurantes o "Supermercados"), proceden a seleccionar una tienda en particular de la lista que se les presenta.
- Retail SST > SS CVR: Porcentaje  de usuarios que, después de seleccionar un Supermercados, proceden a seleccionar una tienda en particular de la lista que se les presenta. 
- Turbo Adoption: Total de usuarios que compran en Turbo (Servicio fast de Rappi) / total de usuarios de Rappi con tiendas de turbo disponible

# REGLAS CRÍTICAS:
1. Genera SOLO la consulta SQL. Cero explicaciones, cero disculpas, cero texto conversacional.
2. NUNCA inventes umbrales numéricos fijos (ej. value < 0.8). Si el usuario pregunta por zonas "problemáticas", "anomalías" o "peores", evalúa el deterioro comparando la semana actual contra las anteriores (ej. L0W_ROLL < L1W_ROLL o calculando caídas porcentuales).
3. NUNCA inventes valores para las columnas basándote en los ejemplos del usuario. Limítate ESTRICTAMENTE a usar los nombres que aparecen en el "DICCIONARIO DE MÉTRICAS". Si el usuario menciona factores que no existen en el diccionario, usa la métrica global más cercana (ej. si mencionan 'tiempos de entrega', usa 'Perfect Orders').
4. MANEJO DE UBICACIONES (CITY vs ZONE): El usuario rara vez especificará si un lugar es una ciudad o una zona. Cuando el usuario mencione CUALQUIER ubicación geográfica (ej. 'Chapinero', 'Bogotá', 'Condesa'):
   - NO asumas a qué columna pertenece.
   - DEBES usar SIEMPRE una condición OR buscando en ambas columnas.
   - Usa LOWER() y LIKE para evitar errores de tipeo, mayúsculas o nombres parciales.
   - Ejemplo OBLIGATORIO: WHERE (LOWER(CITY) LIKE '%chapinero%' OR LOWER(ZONE) LIKE '%chapinero%')
"""

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash-lite', 
    system_instruction=SQL_SYSTEM_PROMPT
)

def clean_sql(text: str) -> str:
    """Extrae el SQL crudo de la respuesta."""
    return text.replace("```sql", "").replace("```", "").strip()

def generar_sql(question: str, history: List[Dict] = None) -> str:
    """Toma el historial, lo formatea para Gemini y genera el SQL."""
    if history is None:
        history = []

    formatted_history = []
    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        formatted_history.append({
            "role": role,
            "parts": [msg["content"]]
        })

    chat = model.start_chat(history=formatted_history)

    safety = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    response = chat.send_message(question, safety_settings=safety)

    return clean_sql(response.text)

