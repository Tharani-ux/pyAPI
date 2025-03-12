from flask import Flask, request, jsonify
import pandas as pd
from geopy.distance import geodesic

app = Flask(__name__)

# Load the database
file_path = "sample_volunteer_database.xlsx"
df = pd.read_excel(file_path, sheet_name="Sheet1")

@app.route('/find_matches', methods=['POST'])
def find_matches():
    data = request.json
    location = data.get("location")
    session = data.get("session")
    date = data.get("date")
    language = data.get("language")
    qualification = data.get("qualification")

    try:
        user_coords = tuple(map(float, location.split(',')))
    except ValueError:
        return jsonify({"error": "Invalid location format. Use lat,lon"}), 400

    # Initial Filtering: Date and Language
    filtered_df = df[
        (df["Date"].astype(str) == date) &
        (df["Languages Known"].str.contains(language, na=False, case=False))
    ]

    if filtered_df.empty:
        return jsonify({"message": "No volunteers found matching the criteria."}), 404

    # Create a copy to avoid SettingWithCopyWarning
    filtered_df = filtered_df.copy()

    # Compute distance
    filtered_df["Distance"] = filtered_df["Location Coordinates"].apply(
        lambda loc: geodesic(user_coords, tuple(map(float, loc.split(',')))).km
    )

    # Further filter by session and qualification, then sort by distance
    final_df = filtered_df[
        (filtered_df["Session"].str.contains(session, na=False, case=False)) &
        (filtered_df["Qualification"].str.contains(qualification, na=False, case=False))
    ].sort_values(by="Distance").head(5)

    if not final_df.empty:
        result = final_df[["Name", "Location Coordinates", "Distance"]].to_dict(orient="records")
        return jsonify({"matches": result})
    else:
        return jsonify({"message": "No volunteers found matching the criteria."}), 404

if __name__ == '__main__':
    app.run(debug=True)
