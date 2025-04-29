from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow Electron app to connect

# Store current data
current_data = {
    "capacity": 0,
    "temperature": 24.0
}

@app.route("/update", methods=["POST"])
def update():
    data = request.get_json()
    if "capacity" in data:
        current_data["capacity"] = data["capacity"]
    if "temperature" in data:
        current_data["temperature"] = data["temperature"]
    return jsonify({"status": "success"})

@app.route("/data", methods=["GET"])
def get_data():
    return jsonify(current_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
