import json
import os

mock_data = {
    "cards": {
        "Meta Redbus Data": 62184,
        "Meta Response Rate %": "31.44%",
        "Overall Redbus Data": 51873,
        "Organic": 17360,
        "Organic (Average)": 4.56,
        "Organic + Not Connected": 19108,
        "Organic + InOrganic": 26468,
        "Average (Overall Redbus)": 4.50,
        "Organic + InOrganic Response Rate %": "42.5%",
        "Data Assigned": 32765,
        "InOrganic Ratings": 9108,
        "Difference (Organic / Inorganic)": "8252",
        "InOrganic Average": 4.38,
        "InOrganic Response Rate %": "27.8%",
        "Data Loss MMT": 1240,
        "Data Loss IBIBO": 890
    },
    "routes": [
        {"route": "VIJAYAWADA - VISAKHAPATNAM", "travel_count": 1500, "rating_count": 450, "avg_rating": 4.2, "response_rate": "30.0%"},
        {"route": "VISAKHAPATNAM - VIJAYAWADA", "travel_count": 1450, "rating_count": 435, "avg_rating": 4.1, "response_rate": "30.0%"},
        {"route": "VIJAYAWADA - HYDERABAD", "travel_count": 3200, "rating_count": 960, "avg_rating": 4.4, "response_rate": "30.0%"},
        {"route": "HYDERABAD - VIJAYAWADA", "travel_count": 3150, "rating_count": 940, "avg_rating": 4.3, "response_rate": "29.8%"},
        {"route": "BANGALORE - TIRUPATI", "travel_count": 2100, "rating_count": 600, "avg_rating": 4.5, "response_rate": "28.5%"},
        {"route": "TIRUPATI - BANGALORE", "travel_count": 2050, "rating_count": 590, "avg_rating": 4.5, "response_rate": "28.7%"},
        {"route": "CHENNAI - BANGALORE", "travel_count": 4100, "rating_count": 1300, "avg_rating": 4.0, "response_rate": "31.7%"},
        {"route": "BANGALORE - CHENNAI", "travel_count": 4200, "rating_count": 1350, "avg_rating": 4.1, "response_rate": "32.1%"}
    ],
    "tls": [
        {"tl": "Uma", "count": 4805, "avg": 4.6, "response_rate": "32.1%"},
        {"tl": "Krishan Priya", "count": 3408, "avg": 4.5, "response_rate": "29.8%"},
        {"tl": "Manideep", "count": 3607, "avg": 4.7, "response_rate": "34.2%"}
    ]
}

backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
with open(os.path.join(backend_dir, 'redbus_mock.json'), 'w') as f:
    json.dump(mock_data, f, indent=4)
print("Mock data written successfully.")
