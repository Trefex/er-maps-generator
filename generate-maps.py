import argparse
import requests
import os
import sys
import subprocess
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from io import BytesIO
from PIL import Image
from datetime import datetime

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
    """
    Fetch route and distance using Google Maps Directions API.

    Args:
        api_key (str): Your Google Maps API key.
        origin (str): The starting point for calculating travel distance and time.
        destination (str): The ending point for calculating travel distance and time.

    Returns:
        tuple: A tuple containing:
            - distance (float): The distance between origin and destination in kilometers.
            - duration (str): The estimated travel time as a human-readable string.
            - polyline (str): The encoded polyline representing the route.

    Raises:
        Exception: If no routes are found or if there is an error fetching directions.
    """
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
           raise Exception(f"No routes found. Response was: {data}")
    else:
        raise Exception(f"Error fetching directions from {response.url} with params {params}: {response.status_code} - {response.text}")

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
        
def create_pdf(api_key, origin, destination, output_file=None):
    """Generate a PDF with the route map, distance, duration, and estimated cost."""
    # Get the current timestamp in ISO format
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S") 
    
    # If no output file is provided, generate a default name
    if output_file is None:
        output_file = f"route_map_{timestamp}.pdf"
    
    # Get route and distance
    distance, duration, polyline = get_route_and_distance(api_key, origin, destination)
    price_per_km = 0.3  # Price per km in EUR
    estimated_cost = distance * price_per_km  # Calculate cost at 0.3 EUR per km
    return_trip_cost = estimated_cost * 2  # Cost for return trip
    
    # Generate map with route
    map_image = generate_map_with_route(api_key, polyline)
    
    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    
    # Add route information
    pdf.cell(0, 8, f"Origin: {origin}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"Destination: {destination}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"Distance: {distance:.2f} km", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"Estimated Travel Time: {duration}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"Estimated Cost (One-way): {estimated_cost:.2f} EUR", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"Estimated Cost (Return trip): {return_trip_cost:.2f} EUR", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Add map image
    temp_map_filename = "temp_map.png"
    map_img = Image.open(map_image)
    map_img.save(temp_map_filename)  # Save as temporary file
    pdf.image(temp_map_filename, x=10, y=pdf.get_y() + 10, w=190)
    
    # Footer
    pdf.ln(200)
    pdf.set_font("Helvetica", size=8)
    pdf.cell(0, 10, f"Generated with Python {sys.version_info.major}.{sys.version_info.minor} by Christophe Trefois ({datetime.now().strftime('%Y-%m-%d')})", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    
    # Save PDF
    pdf.output(output_file)
    print(f"PDF generated: {output_file}")
    
    # Delete the temporary PNG file
    if os.path.exists(temp_map_filename):
        os.remove(temp_map_filename)

def main():
    parser = argparse.ArgumentParser(description="Generate a PDF with a route map, distance, duration, and estimated cost.")
    parser.add_argument("--username", required=True, help="macOS username to fetch the API key from Keychain")
    parser.add_argument("--keychain_service", required=True, help="Service name in macOS Keychain to fetch the API key")
    parser.add_argument("--origin", required=True, help="Origin address")
    parser.add_argument("--destination", required=True, help="Destination address")
    parser.add_argument("--output", help="Output PDF filename")

    args = parser.parse_args()
    
    # Fetch API key securely from Keychain
    api_key = get_api_key_from_keychain(args.username, args.keychain_service)
    
    create_pdf(api_key, args.origin, args.destination, args.output)

if __name__ == "__main__":
    main()
