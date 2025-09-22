# File: mcp_server.py

import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)

# Get the Google Maps API key from environment variables
API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")


@app.route('/find_doctors', methods=['POST'])
def find_doctors():
    """
    API endpoint that receives a request from the agent, calls the
    Google Maps Places API, and returns real-time doctor information.
    """
    if not API_KEY:
        return jsonify({"error": "Google Maps API key is not configured on the server."}), 500

    # Get the specialty and location from the agent's request
    data = request.get_json()
    if not data or 'specialty' not in data or 'location' not in data:
        return jsonify({"error": "Invalid request. 'specialty' and 'location' are required."}), 400

    specialty = data['specialty']
    location = data['location']

    print(f"---MCP Server---: Received request to find '{specialty}' in '{location}'")

    # Define the Google Maps API endpoint and parameters
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    query = f"{specialty} in {location}"
    params = {
        'query': query,
        'key': API_KEY
    }

    try:
        # Make the live API request to Google
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        results = response.json().get('results', [])

        if not results:
            return jsonify([])  # Return an empty list instead of an error

        # Format the real results into a clean list
        formatted_results = []
        for place in results[:5]:  # Return the top 5 results
            formatted_results.append({
                "name": place.get('name', 'N/A'),
                "address": place.get('formatted_address', 'N/A'),
                "rating": place.get('rating', 'N/A')
            })

        print(f"---MCP Server---: Returning {len(formatted_results)} results.")
        return jsonify(formatted_results)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to connect to Google Maps API: {e}"}), 500


if __name__ == '__main__':
    # --- FIX: Changed port to 5001 to avoid conflict with the main app ---
    app.run(debug=True, port=5001)

