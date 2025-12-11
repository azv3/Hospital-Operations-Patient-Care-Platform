import pymongo
from datetime import datetime
import json

def comprehensive_mongodb_analytics():
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['hospital_platform']
    patients = db['patient_summaries']
    
    print("🏥 COMPREHENSIVE MONGODB HOSPITAL ANALYTICS")
    print("=" * 70)
    
    # 1. FIXED: Hypertension analysis with multiple condition patterns
    print("1. 🔍 CARDIOVASCULAR CONDITIONS ANALYSIS")
    cardiovascular_conditions = [
        "Hypertension", "Heart Disease", "Myocardial Infarction", 
        "Atrial Fibrillation", "Congestive heart failure"
    ]
    
    for condition in cardiovascular_conditions:
        # Use regex for flexible matching
        count = patients.count_documents({
            "conditions.description": {"$regex": condition, "$options": "i"}
        })
        print(f"   - {condition}: {count} patients ({count/990*100:.1f}%)")
    
    print()
    
    # 2. Cost analysis with detailed breakdown
    print("2. 💰 FINANCIAL ANALYSIS & COST DRIVERS")
    cost_brackets = [
        (0, 10000, "Low"),
        (10000, 50000, "Medium"), 
        (50000, 100000, "High"),
        (100000, 1000000, "Very High"),
        (1000000, 5000000, "Extreme")
    ]
    
    for min_cost, max_cost, label in cost_brackets:
        count = patients.count_documents({
            "clinical_summary.healthcare_metrics.total_expenses": {
                "$gte": min_cost, "$lt": max_cost
            }
        })
        percentage = (count / 990) * 100
        print(f"   - {label} Cost (${min_cost:,}-${max_cost:,}): {count} patients ({percentage:.1f}%)")
    
    print()
    
    # 3. Department performance analysis
    print("3. 🏥 DEPARTMENT PERFORMANCE & EFFICIENCY")
    dept_pipeline = [
        {"$unwind": "$encounters"},
        {"$group": {
            "_id": "$encounters.providers.organization",
            "total_encounters": {"$sum": 1},
            "avg_claim_cost": {"$avg": "$encounters.financial.total_claim_cost"},
            "total_revenue": {"$sum": "$encounters.financial.total_claim_cost"},
            "unique_patients": {"$addToSet": "$_id"}
        }},
        {"$project": {
            "department": "$_id",
            "total_encounters": 1,
            "avg_claim_cost": 1,
            "total_revenue": 1,
            "unique_patient_count": {"$size": "$unique_patients"},
            "encounters_per_patient": {"$divide": ["$total_encounters", {"$size": "$unique_patients"}]}
        }},
        {"$sort": {"total_revenue": -1}},
        {"$limit": 10}
    ]
    
    departments = list(patients.aggregate(dept_pipeline))
    for dept in departments:
        print(f"   - {dept['department']}:")
        print(f"     👥 {dept['unique_patient_count']} patients, {dept['total_encounters']} encounters")
        print(f"     💰 Avg cost: ${dept['avg_claim_cost']:.2f}, Total: ${dept['total_revenue']:,.2f}")
        print(f"     📊 {dept['encounters_per_patient']:.1f} encounters per patient")
        print()
    
    # 4. Chronic disease burden analysis
    print("4. 🩺 CHRONIC DISEASE BURDEN & COMORBIDITY ANALYSIS")
    chronic_pipeline = [
        {"$project": {
            "name": {"$concat": ["$demographics.name.first", " ", "$demographics.name.last"]},
            "chronic_conditions": {
                "$size": {
                    "$filter": {
                        "input": "$conditions.description",
                        "as": "condition",
                        "cond": {
                            "$or": [
                                {"$regexMatch": {"input": "$$condition", "regex": "Hypertension", "options": "i"}},
                                {"$regexMatch": {"input": "$$condition", "regex": "Diabetes", "options": "i"}},
                                {"$regexMatch": {"input": "$$condition", "regex": "Heart Disease", "options": "i"}},
                                {"$regexMatch": {"input": "$$condition", "regex": "COPD", "options": "i"}},
                                {"$regexMatch": {"input": "$$condition", "regex": "Obesity", "options": "i"}}
                            ]
                        }
                    }
                }
            },
            "total_encounters": "$clinical_summary.total_encounters",
            "total_costs": "$clinical_summary.healthcare_metrics.total_expenses"
        }},
        {"$match": {"chronic_conditions": {"$gte": 2}}},  # Patients with 2+ chronic conditions
        {"$sort": {"chronic_conditions": -1, "total_costs": -1}},
        {"$limit": 10}
    ]
    
    chronic_patients = list(patients.aggregate(chronic_pipeline))
    print(f"   Found {len(chronic_patients)} patients with multiple chronic conditions")
    print("   Top 10 patients with highest chronic disease burden:")
    for patient in chronic_patients[:5]:
        print(f"   - {patient['name']}: {patient['chronic_conditions']} chronic conditions")
        print(f"     Encounters: {patient['total_encounters']}, Costs: ${patient['total_costs']:,.2f}")
    
    print()
    
    # 5. Temporal analysis - encounter patterns
    print("5. 📅 TEMPORAL ANALYSIS & PATIENT JOURNEYS")
    temporal_pipeline = [
        {"$unwind": "$encounters"},
        {"$project": {
            "year": {"$year": {"$toDate": "$encounters.date.start"}},
            "month": {"$month": {"$toDate": "$encounters.date.start"}},
            "encounter_type": "$encounters.type",
            "cost": "$encounters.financial.total_claim_cost"
        }},
        {"$group": {
            "_id": {"year": "$year", "month": "$month"},
            "encounter_count": {"$sum": 1},
            "total_cost": {"$sum": "$cost"},
            "avg_cost": {"$avg": "$cost"}
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1}},
        {"$limit": 12}
    ]
    
    temporal_data = list(patients.aggregate(temporal_pipeline))
    print("   Monthly Encounter Trends:")
    for month_data in temporal_data:
        print(f"   - {month_data['_id']['year']}-{month_data['_id']['month']:02d}: "
              f"{month_data['encounter_count']} encounters, "
              f"${month_data['total_cost']:,.2f} total")
    
    # 6. Create summary document for dashboards
    summary_doc = {
        "_id": "analytics_summary",
        "timestamp": datetime.now(),
        "key_metrics": {
            "total_patients": 990,
            "avg_encounters_per_patient": sum(p['clinical_summary']['total_encounters'] for p in patients.find()) / 990,
            "total_healthcare_costs": sum(p['clinical_summary']['healthcare_metrics']['total_expenses'] for p in patients.find()),
            "high_cost_patients_count": patients.count_documents({
                "clinical_summary.healthcare_metrics.total_expenses": {"$gt": 50000}
            })
        },
        "top_conditions": cardiovascular_conditions,
        "generated_by": "comprehensive_analytics_script"
    }
    
    # Store summary for quick retrieval
    db.analytics_summaries.replace_one({"_id": "analytics_summary"}, summary_doc, upsert=True)
    print(f"\n✅ Analytics summary saved to MongoDB for quick dashboard access")

if __name__ == "__main__":
    comprehensive_mongodb_analytics()