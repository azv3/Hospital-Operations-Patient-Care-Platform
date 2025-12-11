from flask import Flask, render_template, jsonify, request
import pymongo
from datetime import datetime
import json

app = Flask(__name__)

# Connect to MongoDB
client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['hospital_platform']

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🏥 Hospital Operations Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .dashboard { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .metric-card { background: #e8f4fd; padding: 15px; margin: 10px; border-radius: 8px; display: inline-block; width: 200px; }
            .alert { background: #ffebee; color: #c62828; padding: 10px; border-radius: 5px; margin: 10px 0; }
            .success { background: #e8f5e8; color: #2e7d32; padding: 10px; border-radius: 5px; margin: 10px 0; }
            button { background: #2196f3; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer; margin: 5px; }
            button:hover { background: #1976d2; }
            .results { background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1>🏥 Hospital Operations Dashboard</h1>
        
        <div class="dashboard">
            <h2>📊 Quick Analytics</h2>
            
            <div class="metric-card">
                <h3>Total Patients</h3>
                <div id="total-patients">Loading...</div>
            </div>
            
            <div class="metric-card">
                <h3>High-Cost Patients</h3>
                <div id="high-cost">Loading...</div>
            </div>
            
            <div class="metric-card">
                <h3>Hypertension Cases</h3>
                <div id="hypertension">Loading...</div>
            </div>

            <div style="clear: both;"></div>

            <h2>🔍 Patient Search</h2>
            <input type="text" id="condition-search" placeholder="Enter condition (e.g., Hypertension, Diabetes)" style="padding: 8px; width: 300px;">
            <button onclick="searchPatients()">Search Patients</button>
            
            <div id="search-results" class="results"></div>

            <h2>📈 Department Analysis</h2>
            <button onclick="loadDepartmentStats()">Show Department Utilization</button>
            <div id="department-results" class="results"></div>

            <h2>💰 Cost Analysis</h2>
            <button onclick="loadCostAnalysis()">Show Cost Distribution</button>
            <div id="cost-results" class="results"></div>

            <h2>🚨 Critical Alerts</h2>
            <div id="alerts"></div>
        </div>

        <script>
            // Load initial metrics
            function loadMetrics() {
                fetch('/api/metrics')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('total-patients').textContent = data.total_patients;
                        document.getElementById('high-cost').textContent = data.high_cost_patients + ' (' + data.high_cost_percentage + '%)';
                        document.getElementById('hypertension').textContent = data.hypertension_count + ' patients';
                        
                        // Show alerts
                        let alertsHtml = '';
                        if (data.high_cost_percentage > 80) {
                            alertsHtml += '<div class="alert">⚠️ CRITICAL: Over 80% of patients are high-cost (>$50K)</div>';
                        }
                        if (data.va_boston_encounters > 50) {
                            alertsHtml += '<div class="alert">⚠️ ALERT: VA Boston has extremely high patient utilization</div>';
                        }
                        document.getElementById('alerts').innerHTML = alertsHtml;
                    });
            }

            // Search patients by condition
            function searchPatients() {
                const condition = document.getElementById('condition-search').value;
                if (!condition) return;
                
                fetch('/api/search?condition=' + encodeURIComponent(condition))
                    .then(response => response.json())
                    .then(data => {
                        let html = '<h3>Patients with ' + condition + ': ' + data.count + ' found</h3>';
                        if (data.sample_patients && data.sample_patients.length > 0) {
                            html += '<ul>';
                            data.sample_patients.forEach(patient => {
                                html += '<li>' + patient.name + ' - ' + patient.encounters + ' encounters, $' + patient.costs.toLocaleString() + ' total costs</li>';
                            });
                            html += '</ul>';
                        }
                        document.getElementById('search-results').innerHTML = html;
                    });
            }

            // Load department statistics
            function loadDepartmentStats() {
                fetch('/api/departments')
                    .then(response => response.json())
                    .then(data => {
                        let html = '<h3>Top Departments by Utilization</h3><ul>';
                        data.departments.forEach(dept => {
                            html += '<li><strong>' + dept.name + '</strong>: ' + dept.encounters + ' encounters, $' + dept.revenue.toLocaleString() + ' revenue</li>';
                        });
                        html += '</ul>';
                        document.getElementById('department-results').innerHTML = html;
                    });
            }

            // Load cost analysis
            function loadCostAnalysis() {
                fetch('/api/cost-analysis')
                    .then(response => response.json())
                    .then(data => {
                        let html = '<h3>Patient Cost Distribution</h3>';
                        data.cost_brackets.forEach(bracket => {
                            html += '<div>' + bracket.range + ': ' + bracket.count + ' patients (' + bracket.percentage + '%)</div>';
                        });
                        document.getElementById('cost-results').innerHTML = html;
                    });
            }

            // Load metrics when page loads
            loadMetrics();
        </script>
    </body>
    </html>
    """

@app.route('/api/metrics')
def api_metrics():
    patients = db['patient_summaries']
    
    total_patients = patients.count_documents({})
    high_cost_count = patients.count_documents({
        "clinical_summary.healthcare_metrics.total_expenses": {"$gt": 50000}
    })
    hypertension_count = patients.count_documents({
        "conditions.description": {"$regex": "Hypertension", "$options": "i"}
    })
    
    # Check for VA Boston extreme utilization
    va_boston_patients = list(patients.aggregate([
        {"$unwind": "$encounters"},
        {"$match": {"encounters.providers.organization": "VA Boston Healthcare System  Jamaica Plain Campus"}},
        {"$group": {"_id": "$_id", "encounter_count": {"$sum": 1}}},
        {"$match": {"encounter_count": {"$gt": 50}}}
    ]))
    
    return jsonify({
        'total_patients': total_patients,
        'high_cost_patients': high_cost_count,
        'high_cost_percentage': round((high_cost_count / total_patients) * 100, 1),
        'hypertension_count': hypertension_count,
        'va_boston_encounters': len(va_boston_patients)
    })

@app.route('/api/search')
def api_search():
    condition = request.args.get('condition', '')
    patients = db['patient_summaries']
    
    count = patients.count_documents({
        "conditions.description": {"$regex": condition, "$options": "i"}
    })
    
    # Get sample patients
    sample_patients = list(patients.find({
        "conditions.description": {"$regex": condition, "$options": "i"}
    }).limit(5))
    
    formatted_patients = []
    for patient in sample_patients:
        formatted_patients.append({
            'name': f"{patient['demographics']['name']['first']} {patient['demographics']['name']['last']}",
            'encounters': patient['clinical_summary']['total_encounters'],
            'costs': patient['clinical_summary']['healthcare_metrics']['total_expenses']
        })
    
    return jsonify({
        'count': count,
        'sample_patients': formatted_patients
    })

@app.route('/api/departments')
def api_departments():
    patients = db['patient_summaries']
    
    departments = list(patients.aggregate([
        {"$unwind": "$encounters"},
        {"$group": {
            "_id": "$encounters.providers.organization",
            "encounters": {"$sum": 1},
            "revenue": {"$sum": "$encounters.financial.total_claim_cost"}
        }},
        {"$sort": {"encounters": -1}},
        {"$limit": 5}
    ]))
    
    formatted_depts = []
    for dept in departments:
        formatted_depts.append({
            'name': dept['_id'],
            'encounters': dept['encounters'],
            'revenue': round(dept['revenue'], 2)
        })
    
    return jsonify({'departments': formatted_depts})

@app.route('/api/cost-analysis')
def api_cost_analysis():
    patients = db['patient_summaries']
    total_patients = patients.count_documents({})
    
    cost_brackets = [
        (0, 10000, "Under $10K"),
        (10000, 50000, "$10K-$50K"),
        (50000, 100000, "$50K-$100K"), 
        (100000, 1000000, "$100K-$1M"),
        (1000000, 5000000, "Over $1M")
    ]
    
    brackets_data = []
    for min_cost, max_cost, label in cost_brackets:
        count = patients.count_documents({
            "clinical_summary.healthcare_metrics.total_expenses": {
                "$gte": min_cost, "$lt": max_cost
            }
        })
        percentage = round((count / total_patients) * 100, 1)
        brackets_data.append({
            'range': label,
            'count': count,
            'percentage': percentage
        })
    
    return jsonify({'cost_brackets': brackets_data})

if __name__ == '__main__':
    print("🚀 Starting Hospital Web Dashboard...")
    print("📊 Open your web browser and go to: http://localhost:5000")
    print("🏥 Hospital staff can now use the system!")
    app.run(debug=True, port=5000)