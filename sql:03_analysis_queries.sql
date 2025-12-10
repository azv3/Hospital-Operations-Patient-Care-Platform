# SQL Queries & Sample Analyses

USE hospital_operations;


#1 Average Length of Stay by Department
SELECT
  o.name       AS organization_name,
  e.dept_group AS department,
  COUNT(e.encounter_id) AS num_encounters,
  ROUND(AVG(TIMESTAMPDIFF(HOUR, e.start, e.stop)), 1) AS avg_stay_hours
FROM encounters e
LEFT JOIN organizations o
  ON e.organization_id = o.org_id
WHERE e.stop IS NOT NULL
  AND e.dept_group IS NOT NULL
GROUP BY o.name, e.dept_group
ORDER BY avg_stay_hours DESC;


#2 Top 10 diagnoses overall
SELECT
  c.code,
  c.description,
  COUNT(*) AS num_cases
FROM conditions c
JOIN encounters e
  ON c.encounter_id = e.encounter_id
GROUP BY c.code, c.description
ORDER BY num_cases DESC
LIMIT 10;


#3. Provider workload
SELECT
  pr.provider_id,
  pr.name             AS provider_name,
  o.name              AS organization_name,
  COUNT(a.appointment_id)            AS num_appointments,
  SUM(a.duration_minutes)            AS total_minutes,
  ROUND(AVG(a.duration_minutes), 1)  AS avg_minutes_per_appt
FROM appointments a
JOIN providers pr
  ON a.provider_id = pr.provider_id
LEFT JOIN organizations o
  ON a.organization_id = o.org_id
GROUP BY
  pr.provider_id,
  pr.name,
  o.org_id,
  o.name
ORDER BY num_appointments DESC
LIMIT 10;

-- CTE: compute per-provider workload, then filter to those above the average number of appointments:
WITH provider_load AS (
  SELECT
    provider_id,
    COUNT(*) AS num_appointments,
    SUM(duration_minutes) AS total_minutes
  FROM appointments
  GROUP BY provider_id
),
overall AS (
  SELECT AVG(num_appointments) AS avg_appts
  FROM provider_load
)
SELECT
  pr.provider_id,
  pr.name AS provider_name,
  pr.speciality_group AS department,
  pl.num_appointments,
  pl.total_minutes
FROM provider_load pl
JOIN providers pr
  ON pr.provider_id = pl.provider_id
CROSS JOIN overall o
WHERE pl.num_appointments > o.avg_appts
ORDER BY pl.num_appointments DESC;


-- Stored Procedure: Provider workload summary for a date range
DELIMITER $$

DROP PROCEDURE IF EXISTS sp_provider_workload_summary $$
CREATE PROCEDURE sp_provider_workload_summary(
  IN p_provider_id BIGINT,  
  IN p_start_date DATE,
  IN p_end_date   DATE
)
BEGIN
  SELECT
    pr.provider_id,
    pr.name AS provider_name,
    pr.speciality_group AS department,
    DATE(a.appointment_datetime)       AS appt_date,
    COUNT(*)                           AS num_appointments,
    SUM(a.duration_minutes)            AS total_minutes,
    ROUND(AVG(a.duration_minutes), 1)  AS avg_minutes   -- 1 decimal place
  FROM providers pr
  JOIN appointments a
    ON a.provider_id = pr.provider_id
  WHERE pr.provider_id = p_provider_id
    AND a.appointment_datetime >= p_start_date
    AND a.appointment_datetime < DATE_ADD(p_end_date, INTERVAL 1 DAY)
  GROUP BY
    pr.provider_id,
    pr.name,
    pr.speciality_group,
    DATE(a.appointment_datetime)
  ORDER BY appt_date;
END $$

DELIMITER ;

-- Using the Stored Procedure
CALL sp_provider_workload_summary(126, '2017-01-01', '2019-01-01');


#4. Department utilization by encounter volume
SELECT
  e.dept_group AS department,
  COUNT(e.encounter_id) AS num_encounters,
  -- total hours
  ROUND(
    SUM(
      CASE
        WHEN e.start IS NOT NULL AND e.stop IS NOT NULL
        THEN TIMESTAMPDIFF(MINUTE, e.start, e.stop)
        ELSE 0
      END
    ) / 60.0,
    1
  ) AS total_hours,
  -- average stay hours
  ROUND(
    AVG(
      CASE
        WHEN e.start IS NOT NULL AND e.stop IS NOT NULL
        THEN TIMESTAMPDIFF(MINUTE, e.start, e.stop)
        ELSE NULL
      END
    ) / 60.0,
    2
  ) AS avg_stay_hours
FROM encounters e
WHERE e.dept_group IS NOT NULL
GROUP BY e.dept_group
ORDER BY num_encounters DESC;


-- View: Department utilization summary
DROP VIEW IF EXISTS vw_department_utilization;

CREATE VIEW vw_department_utilization AS
SELECT
  e.dept_group AS department,
  COUNT(DISTINCT e.encounter_id)    AS num_encounters,
  COUNT(DISTINCT a.appointment_id)  AS num_appointments,
  -- total hours (from minutes)
  ROUND(
    SUM(
      CASE
        WHEN e.start IS NOT NULL AND e.stop IS NOT NULL
        THEN TIMESTAMPDIFF(MINUTE, e.start, e.stop)
        ELSE 0
      END
    ) / 60.0,
    1
  ) AS total_encounter_hours,
  -- average stay hours
  ROUND(
    AVG(
      CASE
        WHEN e.start IS NOT NULL AND e.stop IS NOT NULL
        THEN TIMESTAMPDIFF(MINUTE, e.start, e.stop)
        ELSE NULL
      END
    ) / 60.0,
    2
  ) AS avg_stay_hours
FROM encounters e
LEFT JOIN appointments a
  ON a.encounter_id = e.encounter_id
WHERE e.dept_group IS NOT NULL
GROUP BY e.dept_group;

-- Using the View
SELECT *
FROM vw_department_utilization
ORDER BY num_encounters DESC;

