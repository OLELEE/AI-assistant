import sqlite3
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "rappi_data.sqlite")

def build_database():
    print("Conectando a SQLite en:", DB_PATH)
    conn = sqlite3.connect(DB_PATH)

    try:
        print("Leyendo Excel...")

        df_metrics = pd.read_excel('OP_rappi.xlsx', sheet_name=0)
        df_metrics.columns = df_metrics.columns.str.strip().str.upper().str.replace(" ", "_")
        print("Metrics shape:", df_metrics.shape)

        df_metrics.to_sql('metrics_input', conn, if_exists='replace', index=False)

        df_orders = pd.read_excel('OP_rappi.xlsx', sheet_name=1)
        df_orders.columns = df_orders.columns.str.strip().str.upper().str.replace(" ", "_")
        print("Orders shape:", df_orders.shape)

        df_orders.to_sql('orders_input', conn, if_exists='replace', index=False)

        print("Base de datos creada correctamente")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    build_database()