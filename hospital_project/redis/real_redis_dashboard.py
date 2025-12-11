import redis
import pymongo
from datetime import datetime
import time

def setup_redis_dashboard():
    print("🚀 SETTING UP REAL REDIS DASHBOARD")
    print("=" * 60)
    
    # Connect to Redis
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    # Connect to MongoDB
    mongo_client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = mongo_client['hospital_platform']
    patients = db['patient_summaries']
    
    # Clear previous data
    r.flushdb()
    print("✅ Redis database cleared")
    
    # 1. Basic counters
    total_patients = patients.count_documents({})
    r.set("dashboard:total_patients", total_patients)
    
    high_cost_count = patients.count_documents({
        "clinical_summary.healthcare_metrics.total_expenses": {"$gt": 50000}
    })
    r.set("dashboard:high_cost_patients", high_cost_count)
    
    # 2. Department encounter counts (Hash)
    dept_pipeline = [
        {"$unwind": "$encounters"},
        {"$group": {
            "_id": "$encounters.providers.organization",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]
    
    departments = list(patients.aggregate(dept_pipeline))
    for dept in departments[:15]:  # Top 15 departments
        r.hset("dashboard:departments", dept['_id'], dept['count'])
    
    # 3. Top conditions (Sorted Set - for rankings)
    condition_pipeline = [
        {"$unwind": "$conditions"},
        {"$group": {
            "_id": "$conditions.description",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    
    top_conditions = list(patients.aggregate(condition_pipeline))
    for condition in top_conditions:
        r.zadd("dashboard:top_conditions", {condition['_id']: condition['count']})
    
    # 4. Cost distribution
    cost_brackets = [
        (0, 10000, "low"),
        (10000, 50000, "medium"), 
        (50000, 100000, "high"),
        (100000, 1000000, "very_high"),
        (1000000, 5000000, "extreme")
    ]
    
    for min_cost, max_cost, label in cost_brackets:
        count = patients.count_documents({
            "clinical_summary.healthcare_metrics.total_expenses": {
                "$gte": min_cost, "$lt": max_cost
            }
        })
        r.hset("dashboard:cost_distribution", label, count)
    
    # 5. Timestamps and metadata
    r.set("dashboard:last_updated", datetime.now().isoformat())
    r.set("dashboard:data_version", "1.0")
    
    print("✅ Redis dashboard populated!")
    print(f"   - Total patients: {r.get('dashboard:total_patients')}")
    print(f"   - High-cost patients: {r.get('dashboard:high_cost_patients')}")
    print(f"   - Departments tracked: {r.hlen('dashboard:departments')}")
    print(f"   - Top conditions: {r.zcard('dashboard:top_conditions')}")
    print(f"   - Last updated: {r.get('dashboard:last_updated')}")

def demonstrate_redis_features():
    """Show Redis in action with live updates"""
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    print("\n🎯 REDIS REAL-TIME FEATURES DEMONSTRATION")
    print("=" * 50)
    
    # Show current state
    print("1. 📊 CURRENT DASHBOARD STATE:")
    print(f"   Total Patients: {r.get('dashboard:total_patients')}")
    print(f"   High-Cost %: {int(r.get('dashboard:high_cost_patients')) / int(r.get('dashboard:total_patients')) * 100:.1f}%")
    
    print("\n2. 🏥 TOP 5 DEPARTMENTS:")
    departments = r.hgetall("dashboard:departments")
    top_depts = sorted(departments.items(), key=lambda x: int(x[1]), reverse=True)[:5]
    for dept, count in top_depts:
        print(f"   {dept}: {count} encounters")
    
    print("\n3. 🩺 TOP 5 CONDITIONS:")
    top_conditions = r.zrevrange("dashboard:top_conditions", 0, 4, withscores=True)
    for condition, score in top_conditions:
        print(f"   {condition}: {int(score)} patients")
    
    print("\n4. 🔄 SIMULATING REAL-TIME HOSPITAL ACTIVITY...")
    print("   (This demonstrates Redis's speed for live updates)")
    
    # Simulate live hospital activity
    for i in range(5):
        time.sleep(2)
        
        # Simulate new patient registration
        r.incr("dashboard:total_patients")
        new_total = r.get("dashboard:total_patients")
        
        # Simulate new encounters
        r.incr("dashboard:today_encounters")
        today_encounters = r.get("dashboard:today_encounters")
        
        # Update timestamp
        r.set("dashboard:last_updated", datetime.now().strftime("%H:%M:%S"))
        
        print(f"   ⏰ {datetime.now().strftime('%H:%M:%S')}")
        print(f"   📈 New patient! Total: {new_total}")
        print(f"   🏥 New encounter! Today: {today_encounters}")
        
        # Simulate department activity
        if i % 2 == 0:
            r.hincrby("dashboard:departments", "Emergency Department", 1)
            print("   🚑 Emergency Department: +1 encounter")
    
    print("\n✅ REAL-TIME DEMONSTRATION COMPLETE!")
    print("   Redis enables sub-second dashboard updates")

def show_redis_performance():
    """Demonstrate Redis speed advantages"""
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    print("\n⚡ REDIS PERFORMANCE DEMONSTRATION")
    print("=" * 50)
    
    import time
    
    # Test Redis speed
    start_time = time.time()
    for i in range(1000):
        r.get("dashboard:total_patients")
    redis_time = time.time() - start_time
    
    # Test MongoDB speed (for comparison)
    mongo_client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = mongo_client['hospital_platform']
    patients = db['patient_summaries']
    
    start_time = time.time()
    for i in range(100):
        patients.count_documents({})  # Fewer iterations because MongoDB is slower
    mongo_time = time.time() - start_time
    
    print(f"✅ Redis: 1000 reads in {redis_time:.3f} seconds")
    print(f"✅ MongoDB: 100 reads in {mongo_time:.3f} seconds")
    print(f"🚀 Redis is {((mongo_time/100) / (redis_time/1000)):.0f}x faster for simple counters!")

if __name__ == "__main__":
    # Test connection first
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        
        # Run the dashboard setup
        setup_redis_dashboard()
        demonstrate_redis_features()
        show_redis_performance()
        
        print("\n🎉 REDIS DASHBOARD COMPLETE!")
        print("You now have:")
        print("✅ MongoDB (DEEP) - Complex analytics, patient records")
        print("✅ Redis (LIGHT) - Real-time dashboard, fast counters")
        print("✅ Perfect 'one deep + one light' NoSQL implementation!")
        
    except Exception as e:
        print(f"❌ Cannot connect to Redis: {e}")
        print("Make sure Redis server is running: redis-server")