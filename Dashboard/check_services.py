import pymongo
import redis
import mysql.connector
from datetime import datetime

def check_all_services():
    print("🔍 CHECKING ALL DATABASE SERVICES")
    print("=" * 50)
    
    # 1. Check MongoDB
    try:
        mongo_client = pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=3000)
        mongo_client.admin.command('ismaster')
        mongo_db = mongo_client['hospital_platform']
        patient_count = mongo_db['patient_summaries'].count_documents({})
        print(f"✅ MongoDB: RUNNING - {patient_count} patients in hospital_platform")
        mongo_client.close()
    except Exception as e:
        print(f"❌ MongoDB: NOT RUNNING - {e}")
    
    # 2. Check Redis
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True, socket_connect_timeout=3)
        r.ping()
        
        # Check if dashboard data exists
        keys = r.keys("dashboard:*")
        if keys:
            total_patients = r.get("dashboard:total_patients")
            print(f"✅ Redis: RUNNING - {len(keys)} dashboard keys, {total_patients} patients")
        else:
            print(f"✅ Redis: RUNNING - But no dashboard data (need to run setup)")
        r.close()
    except Exception as e:
        print(f"❌ Redis: NOT RUNNING - {e}")
    
    # 3. Check MySQL (optional)
    try:
        mysql_conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',  # Your MySQL password
            database='hospital_operations',
            connect_timeout=3
        )
        cursor = mysql_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patients")
        mysql_count = cursor.fetchone()[0]
        print(f"✅ MySQL: RUNNING - {mysql_count} patients in hospital_operations")
        cursor.close()
        mysql_conn.close()
    except Exception as e:
        print(f"❌ MySQL: NOT RUNNING or no connection - {e}")
    
    print("\n🎯 RECOMMENDED ACTIONS:")
    
    # Give specific instructions based on status
    if 'RUNNING' in locals() and 'RUNNING' in locals():
        print("✅ Both MongoDB and Redis are running! You can:")
        print("   1. Run: python ultimate_hospital_dashboard.py")
        print("   2. Visit: http://localhost:5001")
    else:
        if '❌ MongoDB' in locals():
            print("🔧 For MongoDB: Run 'mongod' in Command Prompt")
        if '❌ Redis' in locals():
            print("🔧 For Redis: Run 'redis-server' in Command Prompt or start Redis service")

def quick_start_guide():
    print("\n🚀 QUICK START GUIDE:")
    print("1. If MongoDB isn't running, open NEW Command Prompt and run: mongod")
    print("2. If Redis isn't running, open NEW Command Prompt and run: redis-server") 
    print("3. Keep those running, then in your main Command Prompt run: python ultimate_hospital_dashboard.py")
    print("4. Open browser to: http://localhost:5001")

if __name__ == "__main__":
    check_all_services()
    quick_start_guide()