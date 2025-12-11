import redis

def test_redis_connection():
    print("🔍 Testing Redis Connection...")
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Test basic connection
        response = r.ping()
        print(f"✅ Redis ping: {response}")
        
        # Test setting and getting values
        r.set("test:hospital", "Redis is working!")
        value = r.get("test:hospital")
        print(f"✅ Test value: {value}")
        
        # Test counters
        r.set("test:patient_count", 990)
        count = r.get("test:patient_count")
        print(f"✅ Patient count: {count}")
        
        print("\n🎉 Redis is properly installed and working!")
        return True
        
    except Exception as e:
        print(f"❌ Redis error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure Redis service is running")
        print("2. Try: redis-server (in Command Prompt)")
        print("3. Check Windows Services for 'Redis'")
        return False

if __name__ == "__main__":
    test_redis_connection()