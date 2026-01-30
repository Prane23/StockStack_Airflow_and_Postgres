import os
import random
from datetime import datetime, timezone, timedelta
import json
import pandas as pd
import time
from dotenv import load_dotenv
import psycopg2

# add airflow imports , uncomment below while running locally 
from airflow import DAG
from airflow.operators.python import PythonOperator

# Load environment variables from .env
load_dotenv()

# Directory paths for raw and transformed data
raw_data_dir = "data/stock/raw/"
transformed_data_dir = "data/stock/transformed/"


def generate_stock_data():
    """
    Generate fake stock data and save as JSON files in raw_data_dir.
    """
    os.makedirs(raw_data_dir, exist_ok=True)
    print("Generating stock data...")

    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    stock_data = []

    for _ in range(10):
        ticker = random.choice(tickers)
        price = round(random.uniform(100, 500), 2)

        # 10% chance to inject incorrect (bad) price
        if random.random() < 0.1:
            price = 0

        record = {
            "ticker": ticker,
            "price": price,
            "volume": random.randint(1000, 1_000_000),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        stock_data.append(record)

    # Save file with timestamp identifier
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    raw_file_path = os.path.join(raw_data_dir, f"stock_data_{timestamp}.json")

    with open(raw_file_path, "w") as file:
        json.dump(stock_data, file)

    print(f"Generated file: {raw_file_path}")


def transform_stock_data():
    """
    Read raw JSON files, clean the data, compute pct_change,
    and save as CSV in transformed_data_dir.
    """
    print("Transforming stock data...")
    os.makedirs(transformed_data_dir, exist_ok=True)

    files = os.listdir(raw_data_dir)
    if not files:
        print("No raw data files found.")
        return

    all_records = []

    for file_name in files:
        full_path = os.path.join(raw_data_dir, file_name)

        with open(full_path, "r") as file:
            data = json.load(file)
            all_records.extend(data)

    # Convert to DataFrame
    df = pd.DataFrame(all_records)

    # Filter out invalid rows (bad data)
    df = df[df["price"] > 0]

    # Compute % change (simple example)
    df["pct_change"] = df["price"].pct_change().fillna(0)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    #print(df.head())

    # Save transformed CSV  
    output_path = os.path.join(transformed_data_dir, "transformed_stock_data.csv")
    df.to_csv(output_path, index=False)

    print(f"Transformed file saved: {output_path}")


def load_to_postgres():
    """
    Load the transformed CSV into PostgreSQL using UPSERT to avoid duplicates.
    """
    print(os.getenv("POSTGRES_PORT"))
    conn = None

    try:
        # Connect to Postgres
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            port=os.getenv("POSTGRES_PORT")
        )
        print("Connected to Postgres")

        # Enable autocommit for schema/table creation + inserts
        conn.autocommit = True
        cursor = conn.cursor()

        # Create schema
        cursor.execute("CREATE SCHEMA IF NOT EXISTS stock_schema;")

        # Create table with TIMESTAMPTZ
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_schema.stock_data (
                id SERIAL PRIMARY KEY,
                ticker VARCHAR(10),
                price NUMERIC,
                volume INT,
                pct_change NUMERIC,
                ts TIMESTAMPTZ,
                CONSTRAINT unique_stock_row UNIQUE (ticker, ts)
            );
        """)

        # Read transformed CSV
        csv_path = os.path.join(transformed_data_dir, "transformed_stock_data.csv")
        df = pd.read_csv(csv_path)

        # Convert timestamp column to Python datetime (required for psycopg2)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

        # Insert with UPSERT
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO stock_schema.stock_data
                (ticker, price, volume, pct_change, ts)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (ticker, ts)
                DO UPDATE SET
                    price = EXCLUDED.price,
                    volume = EXCLUDED.volume,
                    pct_change = EXCLUDED.pct_change;
            """, (
                row["ticker"],
                row["price"],
                row["volume"],
                row["pct_change"],
                row["timestamp"]  # now a proper timezone-aware datetime
            ))

        print("Loaded transformed data into Postgres (UPSERT enabled).")

    except Exception as e:
        print("Postgres Load Error:", e)
        raise  # Force Airflow to show task failure

    finally:
        if conn:
            conn.close()

def main():
    """
    Main workflow for the ETL pipeline:
    1. Generate raw fake stock data
    2. Transform raw data
    3. Load processed data into Postgres
    """
    for _ in range(5):
        generate_stock_data()
        transform_stock_data()
        load_to_postgres()
        time.sleep(5)

# uncomment below while running locally 
# main()

#comment below while running locally
# -----------------------------
# Airflow DAG
# -----------------------------
default_args = {
    "start_date": datetime(2026, 1, 1),
    "retries": 2,
    "retry_delay": timedelta(minutes=1)
}

with DAG(
    dag_id="mock_stock_etl",
    default_args=default_args,
    schedule_interval="*/5 * * * *",  # run every 5 min
    catchup=False,
    description="ETL pipeline generating fake stock data → transform → Postgres"
):

    task_generate = PythonOperator(
        task_id="generate_stock_data",
        python_callable=generate_stock_data
    )

    task_transform = PythonOperator(
        task_id="transform_stock_data",
        python_callable=transform_stock_data
    )

    task_load = PythonOperator(
        task_id="load_to_postgres",
        python_callable=load_to_postgres
    )

    # DAG Task Order
    task_generate >> task_transform >> task_load