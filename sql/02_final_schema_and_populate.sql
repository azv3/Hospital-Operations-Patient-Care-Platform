# Step 3) Create the final tables needed
# --------------------------------------
-- Use a new Schema
DROP DATABASE IF EXISTS hospital_operations;
CREATE DATABASE hospital_operations;
USE hospital_operations;


-- 3.1 Patients
DROP TABLE IF EXISTS patients;
CREATE TABLE patients (
  patient_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  patient_source_id VARCHAR(64) NOT NULL UNIQUE,
  birthdate DATE,
  deathdate DATE,
  ssn VARCHAR(32),
  drivers VARCHAR(64),
  passport VARCHAR(64),
  prefix VARCHAR(16),
  first VARCHAR(64),
  last VARCHAR(64),
  suffix VARCHAR(16),
  maiden VARCHAR(64),
  marital VARCHAR(32),
  race VARCHAR(64),
  ethnicity VARCHAR(64),
  gender VARCHAR(16),
  birthplace VARCHAR(128),
  address VARCHAR(128),
  city VARCHAR(64),
  state VARCHAR(32),
  county VARCHAR(64),
  zip VARCHAR(16),
  lat DECIMAL(9,6),
  lon DECIMAL(9,6),
  healthcare_expenses DECIMAL(14,2),
  healthcare_coverage DECIMAL(14,2)
) ENGINE=InnoDB;



-- 3.2 Organizations
DROP TABLE IF EXISTS organizations;
CREATE TABLE organizations (
  org_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  org_source_id VARCHAR(64) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  address VARCHAR(128),
  city VARCHAR(64),
  state VARCHAR(32),
  zip VARCHAR(16),
  lat DECIMAL(9,6),
  lon DECIMAL(9,6),
  phone VARCHAR(32),
  revenue DECIMAL(16,2),
  utilization DECIMAL(9,2)
) ENGINE=InnoDB;



-- 3.3 Providers (staff)
DROP TABLE IF EXISTS providers;
CREATE TABLE providers (
  provider_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  provider_source_id VARCHAR(64) NOT NULL UNIQUE,
  organization_id BIGINT NULL,
  name VARCHAR(255),
  gender VARCHAR(16),
  specialty VARCHAR(128),
  address VARCHAR(128),
  city VARCHAR(64),
  state VARCHAR(32),
  zip VARCHAR(16),
  lat DECIMAL(9,6),
  lon DECIMAL(9,6),
  utilization DECIMAL(6,2),
  CONSTRAINT fk_provider_org FOREIGN KEY (organization_id)
    REFERENCES organizations(org_id)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;



-- 3.4 Payers (for extended utilization analysis)
DROP TABLE IF EXISTS payers;
CREATE TABLE payers (
  payer_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  payer_source_id VARCHAR(64) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  address VARCHAR(128),
  city VARCHAR(64),
  state_headquartered VARCHAR(32),
  zip VARCHAR(16),
  phone VARCHAR(32),
  amount_covered DECIMAL(16,2) NULL,
  amount_uncovered DECIMAL(16,2) NULL,
  revenue DECIMAL(16,2) NULL,
  covered_encounters BIGINT NULL,
  uncovered_encounters BIGINT NULL,
  covered_medications BIGINT NULL,
  uncovered_medications BIGINT NULL,
  covered_procedures BIGINT NULL,
  uncovered_procedures BIGINT NULL,
  covered_immunizations BIGINT NULL,
  uncovered_immunizations BIGINT NULL,
  unique_customers BIGINT NULL,
  qols_avg DECIMAL(6,3) NULL,
  member_months BIGINT NULL
) ENGINE=InnoDB;



-- 3.5 Encounters
DROP TABLE IF EXISTS encounters;
CREATE TABLE encounters (
  encounter_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  encounter_source_id VARCHAR(64) NOT NULL UNIQUE,
  patient_id BIGINT NOT NULL,
  organization_id BIGINT NULL,
  provider_id BIGINT NULL,
  payer_id BIGINT NULL,
  class VARCHAR(64),
  code VARCHAR(64),
  description VARCHAR(255),
  start DATETIME NOT NULL,
  stop DATETIME NULL,
  base_encounter_cost DECIMAL(14,2),
  total_claim_cost DECIMAL(14,2),
  payer_coverage DECIMAL(14,2),
  reason_code VARCHAR(64),
  reason_description VARCHAR(255),
  CONSTRAINT fk_enc_patient FOREIGN KEY (patient_id)
    REFERENCES patients(patient_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_enc_org FOREIGN KEY (organization_id)
    REFERENCES organizations(org_id)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT fk_enc_prov FOREIGN KEY (provider_id)
    REFERENCES providers(provider_id)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT fk_enc_payer FOREIGN KEY (payer_id)
    REFERENCES payers(payer_id)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT chk_enc_time CHECK (stop IS NULL OR stop >= start)
) ENGINE=InnoDB;

-- Encounters indexes
CREATE INDEX ix_enc_patient_start
  ON encounters (patient_id, start);

CREATE INDEX ix_enc_org_start
  ON encounters (organization_id, start);

CREATE INDEX ix_enc_provider_start
  ON encounters (provider_id, start);

-- Trigger-level enforcement: stop >= start
DELIMITER $$

CREATE TRIGGER trg_encounters_before_ins
BEFORE INSERT ON encounters
FOR EACH ROW
BEGIN
  IF NEW.stop IS NOT NULL AND NEW.stop < NEW.start THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'encounters.stop must be >= encounters.start';
  END IF;
END$$

CREATE TRIGGER trg_encounters_before_upd
BEFORE UPDATE ON encounters
FOR EACH ROW
BEGIN
  IF NEW.stop IS NOT NULL AND NEW.stop < NEW.start THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'encounters.stop must be >= encounters.start';
  END IF;
END$$

DELIMITER ;



-- 3.6 Conditions (diagnoses)
DROP TABLE IF EXISTS conditions;
CREATE TABLE conditions (
  condition_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  patient_id BIGINT NOT NULL,
  encounter_id BIGINT NULL,
  start DATETIME NULL,
  stop DATETIME NULL,
  code VARCHAR(64) NOT NULL,
  description VARCHAR(255) NOT NULL,
  CONSTRAINT fk_cond_patient FOREIGN KEY (patient_id)
    REFERENCES patients(patient_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_cond_encounter FOREIGN KEY (encounter_id)
    REFERENCES encounters(encounter_id)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE INDEX ix_cond_patient_code_start
  ON conditions (patient_id, code, start);



-- 3.7 Appointments (derived from encounters)
DROP TABLE IF EXISTS appointments;
CREATE TABLE appointments (
  appointment_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  -- 1:1 with an encounter (we treat qualifying encounters as appointments)
  encounter_id BIGINT NOT NULL UNIQUE,
  -- FKs to core tables
  patient_id BIGINT NOT NULL,
  organization_id BIGINT NULL,
  provider_id BIGINT NULL,
  -- Appointment timing
  appointment_datetime DATETIME NOT NULL,
  duration_minutes INT NULL,
  -- Classification & metadata
  appointment_class VARCHAR(64) NULL,      -- from encounters.class
  code VARCHAR(64) NULL,
  description VARCHAR(255) NULL,
  reason_code VARCHAR(64) NULL,
  reason_description VARCHAR(255) NULL,
  -- Status: data only shows completed visits, but we model more states
  status ENUM('scheduled','completed','cancelled','no_show')
         NOT NULL DEFAULT 'completed',
  CONSTRAINT fk_appt_encounter FOREIGN KEY (encounter_id)
    REFERENCES encounters(encounter_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_appt_patient FOREIGN KEY (patient_id)
    REFERENCES patients(patient_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_appt_org FOREIGN KEY (organization_id)
    REFERENCES organizations(org_id)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT fk_appt_provider FOREIGN KEY (provider_id)
    REFERENCES providers(provider_id)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

-- Helpful indexes for appointment analytics
CREATE INDEX ix_appt_patient_dt   ON appointments (patient_id, appointment_datetime);
CREATE INDEX ix_appt_provider_dt  ON appointments (provider_id, appointment_datetime);
CREATE INDEX ix_appt_org_dt       ON appointments (organization_id, appointment_datetime);

-- Trigger: ensure duration_minutes is non-negative when not NULL
DELIMITER $$

CREATE TRIGGER trg_appointments_before_ins
BEFORE INSERT ON appointments
FOR EACH ROW
BEGIN
  IF NEW.duration_minutes IS NOT NULL AND NEW.duration_minutes < 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'appointments.duration_minutes must be >= 0';
  END IF;
END$$

CREATE TRIGGER trg_appointments_before_upd
BEFORE UPDATE ON appointments
FOR EACH ROW
BEGIN
  IF NEW.duration_minutes IS NOT NULL AND NEW.duration_minutes < 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'appointments.duration_minutes must be >= 0';
  END IF;
END$$

DELIMITER ;



-- 3.8 Procedures (extra table for additional analysis)
DROP TABLE IF EXISTS procedures;
CREATE TABLE procedures (
  procedure_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  patient_id BIGINT NOT NULL,
  encounter_id BIGINT NULL,
  procedure_date DATETIME NULL,
  code VARCHAR(64) NOT NULL,
  description VARCHAR(255) NOT NULL,
  base_cost DECIMAL(14,2) NULL,
  reason_code VARCHAR(64) NULL,
  reason_description VARCHAR(255) NULL,
  CONSTRAINT fk_proc_patient FOREIGN KEY (patient_id)
    REFERENCES patients(patient_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_proc_encounter FOREIGN KEY (encounter_id)
    REFERENCES encounters(encounter_id)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE INDEX ix_proc_patient   ON procedures (patient_id);
CREATE INDEX ix_proc_encounter ON procedures (encounter_id);
CREATE INDEX ix_proc_code      ON procedures (code);



-- 3.9 Medications (extra table for additional analysis)
DROP TABLE IF EXISTS medications;
CREATE TABLE medications (
  medication_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  patient_id BIGINT NOT NULL,
  encounter_id BIGINT NULL,
  payer_source_id VARCHAR(64) NULL,  -- keep payer link as source ID, joinable to payers
  start DATETIME NULL,
  stop DATETIME NULL,
  code VARCHAR(64) NOT NULL,
  description VARCHAR(255) NOT NULL,
  base_cost DECIMAL(14,2) NULL,
  payer_coverage DECIMAL(14,2) NULL,
  dispenses INT NULL,
  total_cost DECIMAL(14,2) NULL,
  reason_code VARCHAR(64) NULL,
  reason_description VARCHAR(255) NULL,
  CONSTRAINT fk_med_patient FOREIGN KEY (patient_id)
    REFERENCES patients(patient_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_med_encounter FOREIGN KEY (encounter_id)
    REFERENCES encounters(encounter_id)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT fk_med_payer FOREIGN KEY (payer_source_id)
    REFERENCES payers(payer_source_id)
    ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE INDEX ix_med_patient       ON medications (patient_id);
CREATE INDEX ix_med_encounter     ON medications (encounter_id);
CREATE INDEX ix_med_code          ON medications (code);
CREATE INDEX ix_med_payer_source  ON medications (payer_source_id);



-- 3.10 Payer transitions (extra table for longitudinal analysis)
DROP TABLE IF EXISTS payer_transitions;
CREATE TABLE payer_transitions (
  transition_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  patient_id BIGINT NOT NULL,
  payer_id BIGINT NOT NULL,
  start_year INT,
  end_year INT,
  ownership VARCHAR(64),
  CONSTRAINT fk_pt_patient FOREIGN KEY (patient_id)
    REFERENCES patients(patient_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_pt_payer FOREIGN KEY (payer_id)
    REFERENCES payers(payer_id)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX ix_pt_patient ON payer_transitions (patient_id);
CREATE INDEX ix_pt_payer   ON payer_transitions (payer_id);



# 4) Populate data into Final Schema from Staging Tables
# ------------------------------------------------------


/* 4.1 Patients (only the 1000 kept patients) */
INSERT INTO hospital_operations.patients (
  patient_source_id,
  birthdate, deathdate,
  ssn, drivers, passport,
  prefix, first, last, suffix,
  maiden, marital, race, ethnicity, gender,
  birthplace, address, city, state, county,
  zip, lat, lon,
  healthcare_expenses, healthcare_coverage
)
SELECT
  p.Id AS patient_source_id,
  p.BIRTHDATE, p.DEATHDATE,
  p.SSN, p.DRIVERS, p.PASSPORT,
  p.PREFIX, p.FIRST, p.LAST, p.SUFFIX,
  p.MAIDEN, p.MARITAL, p.RACE, p.ETHNICITY, p.GENDER,
  p.BIRTHPLACE, p.ADDRESS, p.CITY, p.STATE, p.COUNTY,
  p.ZIP, p.LAT, p.LON,
  p.HEALTHCARE_EXPENSES, p.HEALTHCARE_COVERAGE
FROM hospital_staging.stg_patients p
JOIN hospital_staging.pat_keep k
  ON k.patient_source_id = p.Id;



/* 4.2 Organizations (only those that appear in kept encounters) */
INSERT INTO hospital_operations.organizations (
  org_source_id,
  name,
  address, city, state, zip,
  lat, lon, phone,
  revenue, utilization
)
SELECT DISTINCT
  o.Id AS org_source_id,
  o.NAME,
  o.ADDRESS, o.CITY, o.STATE, o.ZIP,
  o.LAT, o.LON, o.PHONE,
  o.REVENUE, o.UTILIZATION
FROM hospital_staging.stg_organizations o
JOIN hospital_staging.enc_keep e
  ON e.ORGANIZATION = o.Id;



/* 4.3 Providers (only those linked to kept encounters) */

INSERT INTO hospital_operations.providers (
  provider_source_id,
  organization_id,
  name, gender, specialty,
  address, city, state, zip,
  lat, lon, utilization
)
SELECT DISTINCT
  pr.Id AS provider_source_id,
  org.org_id AS organization_id,
  pr.NAME,
  pr.GENDER,
  pr.SPECIALITY AS specialty,
  pr.ADDRESS, pr.CITY, pr.STATE, pr.ZIP,
  pr.LAT, pr.LON,
  pr.UTILIZATION
FROM hospital_staging.stg_providers pr
JOIN hospital_staging.enc_keep e
  ON e.PROVIDER = pr.Id
LEFT JOIN hospital_operations.organizations org
  ON org.org_source_id = pr.ORGANIZATION;

USE hospital_operations;

-- 1) Add the new column (only once)
ALTER TABLE providers
  ADD COLUMN speciality_group VARCHAR(50) NULL
  AFTER specialty;

-- 2) Temporarily disable safe updates
SET SQL_SAFE_UPDATES = 0;

-- 3) Run your department mapping
UPDATE providers
SET speciality_group =
  CASE
    -- Pediatrics
    WHEN specialty LIKE '%Pediatric%' THEN 'Pediatrics'

    -- Cardiology-related
    WHEN specialty LIKE '%Cardio%' THEN 'Cardiology'

    -- Oncology / cancer-related
    WHEN specialty LIKE '%Oncology%'
       OR specialty LIKE '%Hematology & Oncology%' THEN 'Oncology'

    -- Gastro / Neuro
    WHEN specialty LIKE '%Gastroenterology%' THEN 'Gastroenterology'
    WHEN specialty LIKE '%Neurology%'        THEN 'Neurology'

    -- Mental health
    WHEN specialty = 'Psychiatry'
       OR specialty = 'Clinical Psychologist'
       OR specialty = 'Clinical Social Worker' THEN 'Mental Health'

    -- Primary care / generalist
    WHEN specialty IN ('Family Practice', 'General Practice', 'Internal Medicine')
      THEN 'Primary Care / General'

    -- Acute & critical
    WHEN specialty = 'Emergency Medicine'     THEN 'Emergency Medicine'
    WHEN specialty LIKE '%Critical Care%'     THEN 'Critical Care / ICU'

    -- Imaging / diagnostics
    WHEN specialty LIKE '%Radiology%'         THEN 'Radiology / Imaging'
    WHEN specialty LIKE '%Nuclear Medicine%'  THEN 'Radiology / Imaging'

    -- Everything else
    ELSE 'Other / Unknown'
  END;


/* 4.4 Payers (full table, not filtered by pat_keep) */

INSERT INTO hospital_operations.payers (
  payer_source_id, name, address, city, state_headquartered, zip, phone,
  amount_covered, amount_uncovered, revenue,
  covered_encounters, uncovered_encounters,
  covered_medications, uncovered_medications,
  covered_procedures, uncovered_procedures,
  covered_immunizations, uncovered_immunizations,
  unique_customers, qols_avg, member_months
)
SELECT
  Id,
  NAME,
  ADDRESS,
  CITY,
  STATE_HEADQUARTERED,
  ZIP,
  PHONE,
  AMOUNT_COVERED,
  AMOUNT_UNCOVERED,
  REVENUE,
  COVERED_ENCOUNTERS,
  UNCOVERED_ENCOUNTERS,
  COVERED_MEDICATIONS,
  UNCOVERED_MEDICATIONS,
  COVERED_PROCEDURES,
  UNCOVERED_PROCEDURES,
  COVERED_IMMUNIZATIONS,
  UNCOVERED_IMMUNIZATIONS,
  UNIQUE_CUSTOMERS,
  QOLS_AVG,
  MEMBER_MONTHS
FROM hospital_staging.stg_payers;



/* 4.5 Encounters (from enc_keep) */

INSERT INTO hospital_operations.encounters (
  encounter_source_id,
  patient_id,
  organization_id,
  provider_id,
  payer_id,
  class,
  code,
  description,
  start,
  stop,
  base_encounter_cost,
  total_claim_cost,
  payer_coverage,
  reason_code,
  reason_description
)
SELECT
  e.Id AS encounter_source_id,
  p.patient_id,
  o.org_id AS organization_id,
  pr.provider_id,
  pay.payer_id,
  e.ENCOUNTERCLASS AS class,
  e.CODE,
  e.DESCRIPTION,
  e.START,
  e.STOP,
  e.BASE_ENCOUNTER_COST,
  e.TOTAL_CLAIM_COST,
  e.PAYER_COVERAGE,
  e.REASONCODE,
  e.REASONDESCRIPTION
FROM hospital_staging.enc_keep e
JOIN hospital_operations.patients p
  ON p.patient_source_id = e.PATIENT
LEFT JOIN hospital_operations.organizations o
  ON o.org_source_id = e.ORGANIZATION
LEFT JOIN hospital_operations.providers pr
  ON pr.provider_source_id = e.PROVIDER
LEFT JOIN hospital_operations.payers pay
  ON pay.payer_source_id = e.PAYER;

-- After encounters are populated
ALTER TABLE encounters
  ADD COLUMN dept_group VARCHAR(50) NULL
  AFTER class;

UPDATE encounters
SET dept_group =
  CASE
    WHEN class IN ('emergency', 'urgentcare') THEN 'Acute Care (ER/Urgent)'
    WHEN class = 'inpatient'                  THEN 'Inpatient / Acute'
    WHEN class = 'outpatient'                 THEN 'Outpatient Clinic'
    WHEN class = 'ambulatory'                 THEN 'Ambulatory / Clinic'
    WHEN class = 'wellness'                   THEN 'Primary / Preventive'
    ELSE 'Other / Unknown'
  END;


/* 4.6 Conditions (diagnoses for kept patients) */

INSERT INTO hospital_operations.conditions (
  patient_id,
  encounter_id,
  start,
  stop,
  code,
  description
)
SELECT
  p.patient_id,
  enc.encounter_id,
  c.START,
  c.STOP,
  c.CODE,
  c.DESCRIPTION
FROM hospital_staging.stg_conditions c
JOIN hospital_staging.pat_keep k
  ON k.patient_source_id = c.PATIENT
JOIN hospital_operations.patients p
  ON p.patient_source_id = c.PATIENT
LEFT JOIN hospital_operations.encounters enc
  ON enc.encounter_source_id = c.ENCOUNTER;



/* 4.7 Appointments (derived from encounters) */

INSERT INTO hospital_operations.appointments (
  encounter_id,
  patient_id,
  organization_id,
  provider_id,
  appointment_datetime,
  duration_minutes,
  appointment_class,
  code,
  description,
  reason_code,
  reason_description,
  status
)
SELECT
  e.encounter_id,
  e.patient_id,
  e.organization_id,
  e.provider_id,
  -- Appointment datetime = encounter start time
  e.start AS appointment_datetime,
  -- Duration in minutes, if stop exists
  CASE
    WHEN e.start IS NOT NULL AND e.stop IS NOT NULL
      THEN TIMESTAMPDIFF(MINUTE, e.start, e.stop)
    ELSE NULL
  END AS duration_minutes,
  e.class AS appointment_class,
  e.code,
  e.description,
  e.reason_code,
  e.reason_description,
  -- All encounters in Synthea are completed visits
  'completed' AS status
FROM hospital_operations.encounters e
WHERE
  e.start IS NOT NULL
  AND (
        e.class IN ('ambulatory','outpatient','wellness','urgentcare','emergency')
        OR e.class IS NULL
      )
  AND (
        e.stop IS NULL
        OR TIMESTAMPDIFF(HOUR, e.start, e.stop) <= 24
      );



/* 4.8 Medications (for kept patients) */

INSERT INTO hospital_operations.medications (
  patient_id,
  encounter_id,
  payer_source_id,
  start,
  stop,
  code,
  description,
  base_cost,
  payer_coverage,
  dispenses,
  total_cost,
  reason_code,
  reason_description
)
SELECT
  p.patient_id,
  enc.encounter_id,
  m.PAYER            AS payer_source_id,
  m.START,
  m.STOP,
  m.CODE,
  m.DESCRIPTION,
  m.BASE_COST,
  m.PAYER_COVERAGE,
  m.DISPENSES,
  m.TOTALCOST        AS total_cost,
  m.REASONCODE,
  m.REASONDESCRIPTION
FROM hospital_staging.stg_medications m
JOIN hospital_staging.pat_keep k
  ON k.patient_source_id = m.PATIENT
JOIN hospital_operations.patients p
  ON p.patient_source_id = m.PATIENT
LEFT JOIN hospital_operations.encounters enc
  ON enc.encounter_source_id = m.ENCOUNTER;



/* 4.9 Procedures (for kept patients) */

INSERT INTO hospital_operations.procedures (
  patient_id,
  encounter_id,
  procedure_date,
  code,
  description,
  base_cost,
  reason_code,
  reason_description
)
SELECT
  p.patient_id,
  enc.encounter_id,
  pr.DATE,
  pr.CODE,
  pr.DESCRIPTION,
  pr.BASE_COST,
  pr.REASONCODE,
  pr.REASONDESCRIPTION
FROM hospital_staging.stg_procedures pr
JOIN hospital_staging.pat_keep k
  ON k.patient_source_id = pr.PATIENT
JOIN hospital_operations.patients p
  ON p.patient_source_id = pr.PATIENT
LEFT JOIN hospital_operations.encounters enc
  ON enc.encounter_source_id = pr.ENCOUNTER;


/* 4.10 Payer transitions (for kept patients) */

INSERT INTO hospital_operations.payer_transitions (
  patient_id,
  payer_id,
  start_year,
  end_year,
  ownership
)
SELECT
  p.patient_id,
  pay.payer_id,
  pt.START_YEAR,
  pt.END_YEAR,
  pt.OWNERSHIP
FROM hospital_staging.stg_payer_transitions pt
JOIN hospital_operations.patients p
  ON p.patient_source_id = pt.PATIENT
JOIN hospital_operations.payers pay
  ON pay.payer_source_id = pt.PAYER;
