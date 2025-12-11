import redis
import pymongo
from datetime import datetime
import time

def setup_redis_dashboard():
    # Connect to Redis
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    # Connect to MongoDB
    mongo_client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = mongo_client['hospital_platform']
    patients = db['patient_summaries']
    
    print("🚀 SETTING UP REDIS REAL-TIME DASHBOARD")
    print("=" * 60)
    
    # 1. Basic counters
    total_patients = patients.count_documents({})
    r.set("dashboard:total_patients", total_patients)
    
    # 2. High-cost patient counter
    high_cost_count = patients.count_documents({
        "clinical_summary.healthcare_metrics.total_expenses": {"$gt": 50000}
    })
    r.set("dashboard:high_cost_patients", high_cost_count)
    
    # 3. Department encounter counts
    pipeline = [
        {"$unwind": "$encounters"},
        {"$group": {
            "_id": "$encounters.providers.organization",
            "count": {"$sum": 1}
        }}
    ]
    
    departments = list(patients.aggregate(pipeline))
    for dept in departments[:10]:  # Top 10 departments
        r.hset("dashboard:departments", dept['_id'], dept['count'])
    
    # 4. Condition prevalence
    condition_pipeline = [
        {"$unwind": "$conditions"},
        {"$group": {
            "_id": "$conditions.description",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 15}
    ]
    
    top_conditions = list(patients.aggregate(condition_pipeline))
    for condition in top_conditions:
        r.zadd("dashboard:top_conditions", {condition['_id']: condition['count']})
    
    # 5. Real-time metrics with timestamps
    r.set("dashboard:last_updated", datetime.now().isoformat())
    r.set("dashboard:data_freshness", "live")
    
    print("✅ Redis dashboard populated with real-time metrics:")
    print(f"   - Total patients: {r.get('dashboard:total_patients')}")
    print(f"   - High-cost patients: {r.get('dashboard:high_cost_patients')}")
    print(f"   - Departments tracked: {r.hlen('dashboard:departments')}")
    print(f"   - Top conditions: {r.zcard('dashboard:top_conditions')}")
    print(f"   - Last updated: {r.get('dashboard:last_updated')}")

def simulate_live_updates():
    """Simulate real-time updates to the dashboard"""
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    print("\n🔄 SIMULATING LIVE HOSPITAL UPDATES")
    print("=" * 50)
    
    # Simulate new patient registrations
    for i in range(5):
        time.sleep(2)
        current_count = int(r.get("dashboard:total_patients"))
        r.incr("dashboard:total_patients")
        r.set("dashboard:last_updated", datetime.now().isoformat())
        print(f"📈 New patient registered! Total: {current_count + 1}")
    
    # Simulate new encounters
    for i in range(3):
        time.sleep(1)
        r.incr("dashboard:today_encounters")
        print(f"🏥 New encounter recorded! Today: {r.get('dashboard:today_encounters')}")

if __name__ == "__main__":
    setup_redis_dashboard()
    simulate_live_updates()