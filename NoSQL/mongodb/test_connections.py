import mysql.connector
import pymongo

print("🔍 Testing Database Connections...")

# Test MySQL Connection
try:
    mysql_conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',    # First try empty password
        database='hospital_operations'
    )
    print("✅ MySQL Connection: SUCCESS")
    mysql_conn.close()
except Exception as e:
    print(f"❌ MySQL Connection: FAILED - {e}")

# Test MongoDB Connection  
try:
    mongo_client = pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=3000)
    mongo_client.admin.command('ismaster')
    print("✅ MongoDB Connection: SUCCESS")
    mongo_client.close()
except Exception as e:
    print(f"❌ MongoDB Connection: FAILED - {e}")

print("💡 If MySQL failed, try these common passwords:")
print("   - '' (empty)")
print("   - 'root'") 
print("   - 'password'")

print("   - '1234'")
