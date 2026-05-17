import csv
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

def get_coordinates(address, geolocator):
    try:
        location = geolocator.geocode(address)
        if location:
            return (location.latitude, location.longitude)
        else:
            print(f"Could not find coordinates for: {address}")
            return None
    except Exception as e:
        print(f"Error geocoding {address}: {e}")
        return None

def main():
    geolocator = Nominatim(user_agent="distance_calculator_denys")
    
    home_address = "Willem Gijsselsstraat 16, 2050 Antwerpen, Belgium"
    projects = [
        {"name": "Rumst (Bostoen)", "address": "Veerstraat, 2840 Rumst, Belgium"},
        {"name": "LA Esploro (Wilrijk)", "address": "Boombekelaan, 2610 Wilrijk, Belgium"}
    ]
    
    print(f"Geocoding home address: {home_address}")
    home_coords = get_coordinates(home_address, geolocator)
    if not home_coords:
        return

    results = []
    for project in projects:
        print(f"Geocoding project: {project['name']} - {project['address']}")
        time.sleep(1) # Respect Nominatim usage policy
        project_coords = get_coordinates(project['address'], geolocator)
        
        if project_coords:
            distance_km = geodesic(home_coords, project_coords).km
            results.append({
                "Project": project["name"],
                "Address": project["address"],
                "Distance (one-way, km)": round(distance_km, 2),
                "Distance (round-trip, km)": round(distance_km * 2, 2)
            })

    if results:
        csv_file = "distances_report.csv"
        with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"\nReport saved to {csv_file}")
        
        print("\nSummary:")
        for res in results:
            print(f"- {res['Project']}: {res['Distance (one-way, km)']} km one-way ({res['Distance (round-trip, km)']} km total)")

if __name__ == "__main__":
    main()
