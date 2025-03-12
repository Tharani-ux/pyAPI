from flask import Flask, request, jsonify
import pandas as pd
from geopy.distance import geodesic
import os

app = Flask(__name__)

# Load the database file
file_path = "sample_volunteer_database.xlsx"

if os.path.exists(file_path):
    df = pd.read_excel(file_path, sheet_name="Sheet1")
else:
    df = pd.DataFrame()  # Empty DataFrame to prevent crashes if file is missing

@app.route("/")
def home():
    return "Welcome to the Volunteer Matching API!"

@app.route('/find_matches', methods=['POST'])
def find_matches():
    if df.empty:
        return jsonify({"error": "Database file not found or empty."}), 500

    data = request.json

    # Extract parameters
    location = data.get("location", "").strip()
    session = data.get("session", "").strip()
    date = data.get("date", "").strip()
    language = data.get("language", "").strip()
    qualification = data.get("qualification", "").strip()

    if not location:
        return jsonify({"error": "Location is required."}), 400

    try:
        user_coords = tuple(map(float, location.split(',')))
    except ValueError:
        return jsonify({"error": "Invalid location format. Use lat,lon"}), 400

    # Initial Filtering: Date and Language
    filtered_df = df[
        (df["Date"].astype(str) == date) &
        (df["Languages Known"].str.contains(language, na=False, case=False))
    ].copy()

    if filtered_df.empty:
        return jsonify({"message": "No volunteers found matching the criteria."}), 404

    # Compute distance
    try:
        filtered_df["Distance"] = filtered_df["Location Coordinates"].apply(
            lambda loc: geodesic(user_coords, tuple(map(float, loc.split(',')))).km
        )
    except ValueError:
        return jsonify({"error": "Invalid volunteer location format in database."}), 500

    # Further filter by session and qualification, then sort by distance
    final_df = filtered_df[
        (filtered_df["Session"].str.contains(session, na=False, case=False)) &
        (filtered_df["Qualification"].str.contains(qualification, na=False, case=False))
    ].sort_values(by="Distance").head(5)

    if final_df.empty:
        return jsonify({"message": "No volunteers found matching the criteria."}), 404

    result = final_df[["Name", "Location Coordinates", "Distance"]].to_dict(orient="records")
    return jsonify({"matches": result})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
