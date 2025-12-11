# MGTA603 – Final Project  
Group 7: Hospital Operations & Patient Care Platform

This project builds a SQL + NoSQL pipeline for analyzing hospital operations using synthetic EHR data (2017-2019). We focus on patient flow, department utilization, and provider workload to support operational decision-making.

---

## Project Structure

sql/
- 01_staging_and_load.sql
- 02_final_schema_and_populate.sql
- 03_analysis_queries.sql
nosql/

README.md

---


**sql/**  
Contains all SQL scripts needed to build the full analytics pipeline:
- **01_staging_and_load.sql** – staging schema + LOAD DATA + cleaning  
- **02_final_schema_and_populate.sql** – final schema, FKs, triggers, populate  
- **03_analysis_queries.sql** – analytical queries, CTEs, stored procedure, views  

---

## How to Run (Setup Instructions)
### Step 0 – Requirements
- MySQL 8+
- MySQL Workbench (recommended)
- CSV files stored locally on your machine
  *(adjust the file paths inside `01_staging_and_load.sql` to match your computer)*

## **Step 1 — Enable LOCAL INFILE**

MySQL blocks local file loading by default.  
You must enable it **both on the server** and **in MySQL Workbench**.

### A. Enable LOCAL INFILE in MySQL Workbench
1. Open **MySQL Workbench**
2. Go to **Database → Manage Connections…**
3. Select your connection and click **Edit**
4. Open the **Advanced** tab
5. Find the field **Others:** / **Advanced Parameters**
6. Add the following text:
   OPT_LOCAL_INFILE=1
7. Save and reconnect to the database
8. Re-run `LOAD DATA LOCAL INFILE` in `sql/01_staging_and_load.sql`

---

### Step 2 — Run the Staging Script
Execute: sql/01_staging_and_load.sql

This script will:
- Create the `hospital_staging` schema  
- Create all `stg_...` raw staging tables  
- Load CSVs using `LOAD DATA LOCAL INFILE`  
- Cleans names, timestamps, types, and IDs 
- Filter time of encounters to 2017–2019   
- Randomly select ~1000 patients  
- Keep only encounters linked to those patients  

---

### Step 3 — Run the Final Schema + Populate Script
Execute: sql/02_final_schema_and_populate.sql

This will:
- Create the `hospital_operations` schema  
- Build normalized tables (patients, providers, encounters, appointments, etc.)
- Add primary keys, foreign keys, triggers, and indexes  
- Populate final tables from staging tables 
- Derive:
  - `appointments` from encounters  
  - `dept_group` based on encounter class  
  - `speciality_group` for providers  

---

### Step 4 — Run Analysis Queries
Execute: sql/03_analysis_queries.sql

Includes:
- Average Length of Stay by department  
- Top diagnoses  
- Provider workload (CTE + stored procedure `sp_provider_workload_summary`)  
- Department utilization (via `vw_department_utilization` view)  

Useful for:
- Dashboarding / BI reporting  
- Operational insights  

---

## Project Purpose

The goal is to uncover operational insights for hospital administrators, such as:
- Which departments have long stays vs. high throughput  
- Provider workload and staffing imbalance  
- Most common diagnoses driving demand  
- How is capacity spread across departments?

Our data model supports:
- Patient flow & visit history
- Encounter + appointment analytics
- Provider workload & scheduling pressure
- Department utilization heatmaps
- Full operations dashboard foundation

---
