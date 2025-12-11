import pymongo
from pprint import pprint

def run_mongodb_queries():
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['hospital_platform']
    patients = db['patient_summaries']
    
    print("🏥 MONGODB ANALYTICAL QUERIES")
    print("=" * 60)
    
    # 1. TEXT SEARCH: Find patients with specific conditions
    print("1. 🔍 PATIENTS WITH HYPERTENSION")
    hypertensive_patients = patients.find({
        "clinical_summary.active_conditions": "Hypertensive disorder"
    })
    count = patients.count_documents({
        "clinical_summary.active_conditions": "Hypertensive disorder"
    })
    print(f"   Found {count} patients with hypertension")
    
    # Show first 3 patients
    for i, patient in enumerate(hypertensive_patients.limit(3)):
        print(f"   - {patient['demographics']['name']['first']} {patient['demographics']['name']['last']}")
        print(f"     Conditions: {', '.join(patient['clinical_summary']['active_conditions'])}")
        print(f"     Total Encounters: {patient['clinical_summary']['total_encounters']}")
        print()
    
    # 2. AGGREGATION: Top 10 most common conditions
    print("2. 📊 TOP 10 MOST COMMON CONDITIONS")
    pipeline_conditions = [
        {"$unwind": "$conditions"},
        {"$group": {"_id": "$conditions.description", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_conditions = list(patients.aggregate(pipeline_conditions))
    for condition in top_conditions:
        print(f"   - {condition['_id']}: {condition['count']} patients")
    
    print()
    
    # 3. AGGREGATION: Department utilization and costs
    print("3. 🏥 DEPARTMENT UTILIZATION & COSTS")
    pipeline_departments = [
        {"$unwind": "$encounters"},
        {"$group": {
            "_id": "$encounters.providers.organization",
            "total_encounters": {"$sum": 1},
            "avg_claim_cost": {"$avg": "$encounters.financial.total_claim_cost"},
            "total_revenue": {"$sum": "$encounters.financial.total_claim_cost"}
        }},
        {"$sort": {"total_encounters": -1}},
        {"$limit": 8}
    ]
    departments = list(patients.aggregate(pipeline_departments))
    for dept in departments:
        print(f"   - {dept['_id']}:")
        print(f"     Encounters: {dept['total_encounters']}")
        print(f"     Avg Cost: ${dept['avg_claim_cost']:.2f}")
        print(f"     Total Revenue: ${dept['total_revenue']:.2f}")
        print()
    
    # 4. FILTER: High-cost patients analysis
    print("4. 💰 HIGH-COST PATIENTS ANALYSIS")
    high_cost_threshold = 50000
    high_cost_patients = patients.find({
        "clinical_summary.healthcare_metrics.total_expenses": {"$gt": high_cost_threshold}
    }).sort("clinical_summary.healthcare_metrics.total_expenses", -1).limit(5)
    
    high_cost_count = patients.count_documents({
        "clinical_summary.healthcare_metrics.total_expenses": {"$gt": high_cost_threshold}
    })
    print(f"   Found {high_cost_count} patients with expenses > ${high_cost_threshold:,}")
    print("   Top 5 high-cost patients:")
    
    for i, patient in enumerate(high_cost_patients, 1):
        name = f"{patient['demographics']['name']['first']} {patient['demographics']['name']['last']}"
        expenses = patient['clinical_summary']['healthcare_metrics']['total_expenses']
        conditions = patient['clinical_summary']['active_conditions']
        print(f"   {i}. {name}: ${expenses:,.2f}")
        print(f"      Active Conditions: {', '.join(conditions[:3])}")
        print()
    
    # 5. COMPLEX AGGREGATION: Patient risk profiling
    print("5. 📈 PATIENT RISK PROFILING")
    risk_pipeline = [
        {"$match": {"clinical_summary.total_encounters": {"$gt": 5}}},
        {"$project": {
            "name": {"$concat": ["$demographics.name.first", " ", "$demographics.name.last"]},
            "encounter_count": "$clinical_summary.total_encounters",
            "condition_count": "$clinical_summary.total_conditions",
            "total_costs": "$clinical_summary.healthcare_metrics.total_expenses",
            "risk_score": {
                "$add": [
                    {"$multiply": ["$clinical_summary.total_encounters", 2]},
                    {"$multiply": ["$clinical_summary.total_conditions", 5]},
                    {"$divide": ["$clinical_summary.healthcare_metrics.total_expenses", 1000]}
                ]
            }
        }},
        {"$sort": {"risk_score": -1}},
        {"$limit": 5}
    ]
    risk_patients = list(patients.aggregate(risk_pipeline))
    print("   Highest Risk Patients (based on encounters + conditions + costs):")
    for patient in risk_patients:
        print(f"   - {patient['name']}:")
        print(f"     Risk Score: {patient['risk_score']:.1f}")
        print(f"     Encounters: {patient['encounter_count']}, Conditions: {patient['condition_count']}")
        print(f"     Total Costs: ${patient['total_costs']:,.2f}")
        print()

if __name__ == "__main__":
    run_mongodb_queries()