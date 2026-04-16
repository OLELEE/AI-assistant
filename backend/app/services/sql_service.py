import pandas as pd
from app.db.connection import get_connection


def is_safe_sql(query: str) -> bool:
    """
    Evita queries peligrosas generadas por el LLM.
    """
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]
    query_upper = query.upper()
    return not any(word in query_upper for word in forbidden)


def run_query(query: str):
    """
    Ejecuta SQL de forma segura y controlada.
    """
    if not is_safe_sql(query):
        return None, "Query bloqueada por seguridad"

    conn = None
    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn)

        return df, None

    except Exception as e:
        return None, str(e)

    finally:
        if conn:
            conn.close()