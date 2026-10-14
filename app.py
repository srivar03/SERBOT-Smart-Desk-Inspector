from flask import Flask, render_template, jsonify, request
from threading import Lock

app = Flask(__name__)

data_lock = Lock()

robot_data = {
    "status": "Waiting",
    "mode": "Autonomous",
    "battery": 85,
    "location": "Unknown",
    "speed": "Medium",
    "distance": 0,
    "obstacle": "Waiting",
    "action": "Waiting",

    "lights": "OFF",
    "fans": "OFF",

    "detections": [],

    "activity": [
        "🤖 SERBOT started",
        "📷 Waiting for YOLO data"
    ]
}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/status")
def status():
    with data_lock:
        return jsonify(robot_data)


@app.route("/api/update", methods=["POST"])
def update():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    with data_lock:

        if "status" in data:
            robot_data["status"] = data["status"]

        if "mode" in data:
            robot_data["mode"] = data["mode"]

        if "battery" in data:
            robot_data["battery"] = data["battery"]

        if "location" in data:
            robot_data["location"] = data["location"]

        if "speed" in data:
            robot_data["speed"] = data["speed"]

        if "distance" in data:
            robot_data["distance"] = data["distance"]

        if "obstacle" in data:
            robot_data["obstacle"] = data["obstacle"]

        if "action" in data:
            robot_data["action"] = data["action"]

        if "lights" in data:
            robot_data["lights"] = data["lights"]

        if "fans" in data:
            robot_data["fans"] = data["fans"]

        if "detections" in data:
            robot_data["detections"] = data["detections"]

        if "activity" in data:
            robot_data["activity"] = data["activity"]

    return jsonify({
        "success": True
    })


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )