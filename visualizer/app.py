from flask import Flask, render_template, request, jsonify
import subprocess
import re

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run-hey", methods=["POST"])
def run_hey():
    url = request.json.get("url")
    n = str(request.json.get("n", 100))
    c = str(request.json.get("c", 10))

    if not url:
        return jsonify({"error": "Missing URL"}), 400

    try:
        result = subprocess.run(
            ["hey", "-n", n, "-c", c, url],
            capture_output=True, text=True, timeout=15
        )
        output = result.stdout

        # Histogram
        hist_pattern = re.compile(r"^\s+([\d\.]+) \[(\d+)\]")
        histogram = {}
        for line in output.splitlines():
            match = hist_pattern.match(line)
            if match:
                time_bin, count = match.groups()
                histogram[time_bin] = int(count)

        # Latency
        latency_data = {}
        latency_pattern = re.compile(r"(\d+)% in ([\d\.]+) secs")
        for line in output.splitlines():
            match = latency_pattern.search(line)
            if match:
                latency_data[match.group(1)] = float(match.group(2))

        # Summary
        summary = {}
        for line in output.splitlines():
            if line.startswith("  Total:"):
                summary["total"] = float(line.split()[1])
            elif line.startswith("  Slowest:"):
                summary["slowest"] = float(line.split()[1])
            elif line.startswith("  Fastest:"):
                summary["fastest"] = float(line.split()[1])
            elif line.startswith("  Average:"):
                summary["average"] = float(line.split()[1])
            elif line.startswith("  Requests/sec:"):
                summary["rps"] = float(line.split()[1])
            elif line.strip().startswith("Total data:"):
                summary["total_data"] = line.split(":")[1].strip()
            elif line.strip().startswith("Size/request:"):
                summary["size_per_request"] = line.split(":")[1].strip()

        # Status Codes
        status_code_dist = {}
        status_pattern = re.compile(r"\[(\d+)\]\s+(\d+)\sresponses")
        for line in output.splitlines():
            match = status_pattern.search(line)
            if match:
                code, count = match.groups()
                status_code_dist[code] = int(count)

        return jsonify({
            "histogram": histogram,
            "latency": latency_data,
            "summary": summary,
            "status_codes": status_code_dist
        })

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Command timed out"}), 500

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5055)
    args = parser.parse_args()

    app.run(debug=True, host=args.host, port=args.port)
