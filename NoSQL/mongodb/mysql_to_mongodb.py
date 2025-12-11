import mysql.connector
import pymongo
from datetime import datetime
from decimal import Decimal

def create_mongodb_documents():
    print("🏥 Starting Professional MySQL to MongoDB Migration")
    print("=" * 60)
    
    # 1. Database Connections
    try:
        # Connect to MySQL (your teammate's cleaned database)
        mysql_conn = mysql.connector.connect(
            host='localhost',
            user='root',           # Your MySQL username
            password='',   # Your MySQL password
            database='hospital_operations',
            charset='utf8mb4'
        )
        mysql_cursor = mysql_conn.cursor(dictionary=True)
        print("✅ Connected to MySQL: hospital_operations")
        
        # Connect to MongoDB
        mongo_client = pymongo.MongoClient(
            'mongodb://localhost:27017/',
            serverSelectionTimeoutMS=5000
        )
        # Test connection
        mongo_client.admin.command('ismaster')
        mongo_db = mongo_client['hospital_platform']
        
        # Drop existing collections for clean migration
        mongo_db.drop_collection('patient_summaries')
        mongo_db.drop_collection('operational_metrics')
        
        patients_collection = mongo_db['patient_summaries']
        metrics_collection = mongo_db['operational_metrics']
        print("✅ Connected to MongoDB: hospital_platform")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    # 2. Get total counts for progress tracking
    mysql_cursor.execute("SELECT COUNT(*) as total FROM patients")
    total_patients = mysql_cursor.fetchone()['total']
    print(f"📊 Migrating {total_patients} patients...")

    # 3. Get all patients with their data
    mysql_cursor.execute("""
        SELECT p.*, 
               TIMESTAMPDIFF(YEAR, p.birthdate, CURDATE()) as age
        FROM patients p
    """)
    patients = mysql_cursor.fetchall()

    migrated_count = 0
    error_count = 0

    # 4. Process each patient into rich MongoDB documents
    for patient in patients:
        try:
            patient_id = patient['patient_id']
            
            # Get patient's encounters with organization and provider info
            mysql_cursor.execute("""
                SELECT e.*, 
                       o.name as organization_name,
                       pr.name as provider_name,
                       pr.specialty as provider_specialty,
                       pay.name as payer_name
                FROM encounters e
                LEFT JOIN organizations o ON e.organization_id = o.org_id
                LEFT JOIN providers pr ON e.provider_id = pr.provider_id
                LEFT JOIN payers pay ON e.payer_id = pay.payer_id
                WHERE e.patient_id = %s
                ORDER BY e.start DESC
            """, (patient_id,))
            encounters = mysql_cursor.fetchall()

            # Get patient's conditions
            mysql_cursor.execute("""
                SELECT description, start, stop, code
                FROM conditions 
                WHERE patient_id = %s
                ORDER BY start DESC
            """, (patient_id,))
            conditions = mysql_cursor.fetchall()

            # Get patient's procedures
            mysql_cursor.execute("""
                SELECT description, procedure_date, base_cost, code
                FROM procedures 
                WHERE patient_id = %s
                ORDER BY procedure_date DESC
            """, (patient_id,))
            procedures = mysql_cursor.fetchall()

            # Get patient's medications
            mysql_cursor.execute("""
                SELECT description, start, stop, base_cost, total_cost
                FROM medications 
                WHERE patient_id = %s
                ORDER BY start DESC
            """, (patient_id,))
            medications = mysql_cursor.fetchall()

            # Calculate financial metrics
            total_healthcare_cost = sum(
                enc['total_claim_cost'] or 0 
                for enc in encounters
            )
            encounter_count = len(encounters)
            active_conditions = [
                cond['description'] for cond in conditions 
                if cond['stop'] is None
            ]

            # Build comprehensive MongoDB document
            patient_doc = {
                "_id": patient['patient_source_id'],
                "metadata": {
                    "mysql_patient_id": patient_id,
                    "migration_timestamp": datetime.now(),
                    "data_version": "1.0"
                },
                "demographics": {
                    "name": {
                        "first": patient['first'],
                        "last": patient['last'],
                        "prefix": patient['prefix'],
                        "suffix": patient['suffix']
                    },
                    "birthdate": patient['birthdate'].isoformat() if patient['birthdate'] else None,
                    "age": patient['age'],
                    "gender": patient['gender'],
                    "race": patient['race'],
                    "ethnicity": patient['ethnicity'],
                    "marital_status": patient['marital'],
                    "location": {
                        "address": patient['address'],
                        "city": patient['city'],
                        "state": patient['state'],
                        "zip": patient['zip'],
                        "coordinates": {
                            "lat": float(patient['lat']) if patient['lat'] else None,
                            "lon": float(patient['lon']) if patient['lon'] else None
                        }
                    }
                },
                "clinical_summary": {
                    "total_encounters": encounter_count,
                    "active_conditions": active_conditions,
                    "total_conditions": len(conditions),
                    "total_procedures": len(procedures),
                    "total_medications": len(medications),
                    "healthcare_metrics": {
                        "total_expenses": float(patient['healthcare_expenses']) if patient['healthcare_expenses'] else 0,
                        "total_coverage": float(patient['healthcare_coverage']) if patient['healthcare_coverage'] else 0,
                        "calculated_costs": float(total_healthcare_cost)
                    }
                },
                "encounters": [
                    {
                        "encounter_id": enc['encounter_source_id'],
                        "date": {
                            "start": enc['start'].isoformat() if enc['start'] else None,
                            "end": enc['stop'].isoformat() if enc['stop'] else None
                        },
                        "type": enc['description'],
                        "class": enc['class'],
                        "clinical": {
                            "reason_code": enc['reason_code'],
                            "reason_description": enc['reason_description']
                        },
                        "providers": {
                            "organization": enc['organization_name'],
                            "provider": enc['provider_name'],
                            "specialty": enc['provider_specialty']
                        },
                        "financial": {
                            "base_cost": float(enc['base_encounter_cost']) if enc['base_encounter_cost'] else 0,
                            "total_claim_cost": float(enc['total_claim_cost']) if enc['total_claim_cost'] else 0,
                            "payer_coverage": float(enc['payer_coverage']) if enc['payer_coverage'] else 0,
                            "payer": enc['payer_name']
                        }
                    } for enc in encounters
                ],
                "conditions": [
                    {
                        "description": cond['description'],
                        "code": cond['code'],
                        "timeline": {
                            "start": cond['start'].isoformat() if cond['start'] else None,
                            "end": cond['stop'].isoformat() if cond['stop'] else None,
                            "is_active": cond['stop'] is None
                        }
                    } for cond in conditions
                ],
                "procedures": [
                    {
                        "description": proc['description'],
                        "code": proc['code'],
                        "date": proc['procedure_date'].isoformat() if proc['procedure_date'] else None,
                        "cost": float(proc['base_cost']) if proc['base_cost'] else 0
                    } for proc in procedures
                ],
                "medications": [
                    {
                        "description": med['description'],
                        "timeline": {
                            "start": med['start'].isoformat() if med['start'] else None,
                            "end": med['stop'].isoformat() if med['stop'] else None
                        },
                        "cost": {
                            "base": float(med['base_cost']) if med['base_cost'] else 0,
                            "total": float(med['total_cost']) if med['total_cost'] else 0
                        }
                    } for med in medications
                ]
            }

            # Insert into MongoDB
            patients_collection.insert_one(patient_doc)
            migrated_count += 1
            
            if migrated_count % 100 == 0:
                print(f"✅ Migrated {migrated_count}/{total_patients} patients...")

        except Exception as e:
            print(f"❌ Error migrating patient {patient_id}: {e}")
            error_count += 1

    # 5. Create operational metrics collection
    try:
        # Get department utilization
        mysql_cursor.execute("""
            SELECT o.name as department, 
                   COUNT(*) as encounter_count,
                   AVG(TIMESTAMPDIFF(HOUR, e.start, e.stop)) as avg_stay_hours
            FROM encounters e
            JOIN organizations o ON e.organization_id = o.org_id
            WHERE e.stop IS NOT NULL
            GROUP BY o.name
            ORDER BY encounter_count DESC
        """)
        department_metrics = mysql_cursor.fetchall()

        # Get top conditions
        mysql_cursor.execute("""
            SELECT description, COUNT(*) as patient_count
            FROM conditions
            GROUP BY description
            ORDER BY patient_count DESC
            LIMIT 10
        """)
        top_conditions = mysql_cursor.fetchall()

        metrics_doc = {
            "_id": "operational_dashboard",
            "migration_summary": {
                "total_patients_migrated": migrated_count,
                "total_errors": error_count,
                "migration_date": datetime.now(),
                "data_timeframe": "2017-2018"
            },
            "department_utilization": [
                {
                    "department": dept['department'],
                    "encounter_count": dept['encounter_count'],
                    "average_stay_hours": float(dept['avg_stay_hours']) if dept['avg_stay_hours'] else 0
                } for dept in department_metrics
            ],
            "clinical_insights": {
                "top_conditions": [
                    {
                        "condition": cond['description'],
                        "patient_count": cond['patient_count']
                    } for cond in top_conditions
                ]
            }
        }
        
        metrics_collection.insert_one(metrics_doc)
        print("✅ Operational metrics created")

    except Exception as e:
        print(f"❌ Error creating metrics: {e}")

    # 6. Cleanup and summary
    mysql_cursor.close()
    mysql_conn.close()
    mongo_client.close()

    print("=" * 60)
    print(f"🎉 MIGRATION COMPLETED!")
    print(f"📊 Patients migrated: {migrated_count}/{total_patients}")
    print(f"❌ Errors: {error_count}")
    print(f"💾 MongoDB collections created:")
    print(f"   - patient_summaries ({migrated_count} documents)")
    print(f"   - operational_metrics (1 document)")
    print("🔍 Open MongoDB Compass to view your data!")

if __name__ == "__main__":

    create_mongodb_documents()
