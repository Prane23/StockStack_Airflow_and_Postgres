# StockStack: Airflow + Postgres ETL Pipeline
A fully containerized ETL (Extract → Transform → Load) pipeline built using:

Apache Airflow (Docker Compose)
Python (Pandas)
PostgreSQL
Docker
Environment‑based configuration (.env)

This project generates mock stock data, transforms it, and loads it into Postgres automatically on a schedule.
---
## 🚀 Project Overview
This repository contains an end‑to‑end stock data pipeline:
- Generate – Create random stock data files (JSON)
- Transform – Clean & convert them into a CSV
- Load – Insert the cleaned records into PostgreSQL (with UPSERT support)
- Schedule – Automated via Airflow every 5 minutes.

This pipeline is fully orchestrated by Apache Airflow, running inside Docker containers.

## 🏗️ Architecture
```
          ┌─────────────────────────────────────────────┐
          │                 Airflow DAG                  │
          │   mock_stock_etl (runs every 5 min)         │
          └─────────────────────────────────────────────┘
                      │         │         │
                      ▼         ▼         ▼
        ┌────────────────┐ ┌───────────────┐ ┌───────────────────┐
        │ Generate Task  │ │ Transform Task│ │ Load to Postgres  │
        │ (JSON files)   │ │ (CSV output)  │ │ (UPSERT rows)     │
        └────────────────┘ └───────────────┘ └───────────────────┘
                      │                          │
                      ▼                          ▼
             /opt/airflow/data/...         PostgreSQL database
```
---
## 📂 Repository Structure
```
StockStack_Airflow_and_Postgres/
│── dags/
│     └── stock_data.py          # Main ETL DAG
│
│── data/                        # Persisted via Docker volume
│     ├── stock/raw/             # Generated JSON files
│     └── stock/transformed/     # CSV output
│
│── docker-compose.yml            # Airflow + Postgres stack
│── .env                          # DB credentials
│── README.md                     # Documentation (this file)
```
---
## ⚙️ Prerequisites
Install the following:
  - Docker Desktop
  - Docker Compose
  - Git
That's all — Airflow and Postgres run inside containers.
## 🔧 1. Clone the Repository
 - git clone https://github.com/Prane23/StockStack_Airflow_and_Postgres.git
 - cd StockStack_Airflow_and_Postgres
## 🔐 2. Configure Environment Variables
 - Create a .env file at project root:
 - POSTGRES_USER=airflow
 - POSTGRES_PASSWORD=airflow
 - POSTGRES_DB=airflow
 - POSTGRES_PORT=5432
 Dynamic host switching
 - Docker containers: use "postgres"
 - Local scripts:     use "localhost"
POSTGRES_HOST=postgres (💡Airflow loads this .env inside Docker, so POSTGRES_HOST=postgres is correct.)
## 🚢 3. Start Airflow + Postgres
 -  docker compose up -d
 This starts:
 <img width="694" height="266" alt="image" src="https://github.com/user-attachments/assets/5fdda8ca-ff53-4796-a43e-4a18d6ceb4d8" />

## 🔑 4. Log into Airflow 
   - Default user:
   -  Username: admin
   -  Password: admin
(Open docker-compose.yml if your setup uses different credentials.)

## 📘 5. Enable the ETL Pipeline
Inside Airflow UI:
 - Open the mock_stock_etl DAG
 - Toggle the switch to ON
 - Click "Trigger DAG" (optional)
  The DAG runs every 5 minute.
## 📊 6. Where the Data is Stored
1. Inside Docker (Airflow container)
   - /opt/airflow/data/stock/raw/
   -  /                /transformed/
2. On your computer (mirrored via volume):
   -  ./data/stock/raw/
   -  ./data/stock/transformed/
3. Your CSV file is here:
   -  data/stock/transformed/transformed_stock_data.csv
  
## 🗄️ 7. Connecting to Postgres
1. Using a client like TablePlus / DBeaver:
  Host: localhost
  Port: 5432
  User: {user}
  Password: {password}
  Database: {database}
2. Table created:
  stock_schema.stock_data
---
## ⭐ Future Improvements (Optional)
   - Add pgAdmin container
   - Add API-based real stock data
   - Add dbt transformations
   - Add testing with pytest
   - Add data quality (Great Expectations)
