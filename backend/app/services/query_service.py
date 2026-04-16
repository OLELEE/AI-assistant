from app.services.llm_service import generar_sql
from app.services.sql_service import run_query


def process_question(question: str, history=None):
    """
    Orquesta todo el flujo:
    LLM → SQL → ejecución → autocorrección
    """
    if history is None:
        history = []

    sql = generar_sql(question, history)

    result, error = run_query(sql)

    attempts = 0

    while error and attempts < 2:
        correction_prompt = f"""
        El siguiente SQL falló:

        SQL:
        {sql}

        Error:
        {error}

        Corrige la consulta. Devuelve SOLO SQL válido.
        """

        sql = generar_sql(correction_prompt, history)

        result, error = run_query(sql)
        attempts += 1

    return {
        "sql": sql,
        "data": result.to_dict(orient="records") if result is not None else None,
        "error": error,
        "attempts": attempts
    }