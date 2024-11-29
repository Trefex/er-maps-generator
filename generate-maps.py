import argparse
import requests
from fpdf import FPDF
from io import BytesIO
from PIL import Image
import subprocess

def get_api_key_from_keychain(username, service_name):
    """Fetch API key securely from macOS Keychain."""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-a", username, "-s", service_name, "-w"],
            check=True,
            text=True,
            capture_output=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to retrieve API key: {e.stderr.strip()}")

def get_route_and_distance(api_key, origin, destination):
    """Fetch route and distance using Google Maps Directions API."""
    directions_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "mode": "driving",
        "units": "metric",  # Use metric units for kilometers
        "key": api_key
    }
    response = requests.get(directions_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["routes"]:
            leg = data["routes"][0]["legs"][0]
            distance = leg["distance"]["value"] / 1000  # Convert meters to kilometers
            duration = leg["duration"]["text"]
            polyline = data["routes"][0]["overview_polyline"]["points"]
            return distance, duration, polyline
        else:
            raise Exception("No routes found.")
    else:
        raise Exception(f"Error fetching directions: {response.status_code} - {response.text}")

def generate_map_with_route(api_key, polyline):
    """Generate a static map with the route using Google Static Maps API."""
    static_map_url = "https://maps.googleapis.com/maps/api/staticmap"
    params = {
        "size": "1200x800",  # Higher resolution map
        "scale": 2,  # Increased scale for better quality
        "maptype": "roadmap",
        "path": f"enc:{polyline}",
        "key": api_key
    }
    response = requests.get(static_map_url, params=params)
    if response.status_code == 200:
        return BytesIO(response.content)  # Return image as byte stream
    else:
        raise Exception(f"Error generating map: {response.status_code} - {response.text}")

def create_pdf(api_key, origin, destination, output_file):
    """Generate a PDF with the route map, distance, duration, and estimated cost."""
    # Get route and distance
    distance, duration, polyline = get_route_and_distance(api_key, origin, destination)
    estimated_cost = distance * 0.3  # Calculate cost at 0.3 EUR per km
    
    # Generate map with route
    map_image = generate_map_with_route(api_key, polyline)
    
    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    
    # Add route information
    pdf.cell(0, 10, f"Origin: {origin}", ln=True)
    pdf.cell(0, 10, f"Destination: {destination}", ln=True)
    pdf.cell(0, 10, f"Distance: {distance:.2f} km", ln=True)
    pdf.cell(0, 10, f"Estimated Travel Time: {duration}", ln=True)
    pdf.cell(0, 10, f"Estimated Cost: {estimated_cost:.2f} EUR", ln=True)
    
    # Add map image
    map_img = Image.open(map_image)
    map_img.save("temp_map.png")  # Save as temporary file
    pdf.image("temp_map.png", x=10, y=60, w=190)  # Add image to PDF

    # Save PDF
    pdf.output(output_file)
    print(f"PDF generated: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Generate a PDF with a route map, distance, duration, and estimated cost.")
    parser.add_argument("--username", required=True, help="macOS username to fetch the API key from Keychain")
    parser.add_argument("--keychain_service", required=True, help="Service name in macOS Keychain to fetch the API key")
    parser.add_argument("--origin", required=True, help="Origin address")
    parser.add_argument("--destination", required=True, help="Destination address")
    parser.add_argument("--output", default="route_map.pdf", help="Output PDF filename")

    args = parser.parse_args()
    
    # Fetch API key securely from Keychain
    api_key = get_api_key_from_keychain(args.username, args.keychain_service)
    
    create_pdf(api_key, args.origin, args.destination, args.output)

if __name__ == "__main__":
    main()
