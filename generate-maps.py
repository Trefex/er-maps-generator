import argparse
import requests
import os
import sys
import subprocess
import json
import tempfile
from pathlib import Path
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from io import BytesIO
from PIL import Image
from datetime import datetime

# Try to import Keeper Commander SDK
try:
    from keepercommander import api
    from keepercommander.__main__ import get_params_from_config
    KEEPER_AVAILABLE = True
except ImportError:
    KEEPER_AVAILABLE = False

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

def get_api_key_from_keeper(record_uid):
    """Fetch API key from Keeper Security using Keeper Commander SDK."""
    if not KEEPER_AVAILABLE:
        raise Exception("Keeper Commander SDK is not installed. Please run 'pip install keepercommander'.")

    config_path = os.path.expanduser('~/.keeper/config.json')
    if not os.path.exists(config_path):
        raise Exception(f"Keeper config not found at {config_path}. Please run 'keeper login' first.")

    # Load params and authenticate
    params = get_params_from_config(config_path)
    api.login(params)
    api.sync_down(params)
    
    # Get the record
    record = api.get_record(params, record_uid)
    if not record:
        raise Exception(f"Record {record_uid} not found.")

    # Try to extract the secret from various locations
    if record.password:
        return record.password
    
    if record.notes and record.notes.strip():
        return record.notes.strip()
    
    # Check custom fields (for encryptedNotes type)
    record_dict = record.to_dictionary()
    for field in record_dict.get('custom_fields', []):
        field_type = field.get('type', '')
        field_value = field.get('value', '')
        if field_type in ('note', 'text', 'multiline') and field_value:
            return str(field_value)
    
    raise Exception(f"Could not find password or note in Keeper record (type: {record.record_type})")

def get_route_and_distance(api_key, origin, destination):
    """Fetch route and distance using Google Maps Directions API."""
    response = requests.get("https://maps.googleapis.com/maps/api/directions/json", params={
        "origin": origin,
        "destination": destination,
        "mode": "driving",
        "units": "metric",
        "key": api_key
    }, timeout=30)
    
    if response.status_code != 200:
        raise Exception(f"Error fetching directions: {response.status_code} - {response.text}")
    
    data = response.json()
    if not data.get("routes"):
        raise Exception(f"No routes found. Response: {data}")
    
    leg = data["routes"][0]["legs"][0]
    distance = leg["distance"]["value"] / 1000  # Convert meters to kilometers
    duration = leg["duration"]["text"]
    polyline = data["routes"][0]["overview_polyline"]["points"]
    
    return distance, duration, polyline

def generate_map_with_route(api_key, polyline):
    """Generate a static map with the route using Google Static Maps API."""
    response = requests.get("https://maps.googleapis.com/maps/api/staticmap", params={
        "size": "1200x800",
        "scale": 2,
        "maptype": "roadmap",
        "path": f"enc:{polyline}",
        "key": api_key
    }, timeout=30)
    
    if response.status_code != 200:
        raise Exception(f"Error generating map: {response.status_code} - {response.text}")
    
    return BytesIO(response.content)
        
def create_pdf(api_key, origin, destination, output_file=None):
    """Generate a PDF with the route map, distance, duration, and estimated cost."""
    if output_file is None:
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        output_file = f"route_map_{timestamp}.pdf"
    
    # Get route data
    distance, duration, polyline = get_route_and_distance(api_key, origin, destination)
    price_per_km = 0.3
    estimated_cost = distance * price_per_km
    return_trip_cost = estimated_cost * 2
    
    # Generate map
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
    
    # Add map image using secure temp file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_map_filename = temp_file.name
        Image.open(map_image).save(temp_map_filename)
        pdf.image(temp_map_filename, x=10, y=pdf.get_y() + 10, w=190)
    os.unlink(temp_map_filename)
    
    # Add footer
    pdf.ln(200)
    pdf.set_font("Helvetica", size=8)
    footer_text = f"Generated with Python {sys.version_info.major}.{sys.version_info.minor} by Christophe Trefois ({datetime.now().strftime('%Y-%m-%d')})"
    pdf.cell(0, 10, footer_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    
    # Save PDF
    pdf.output(output_file)
    print(f"PDF generated: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Generate a PDF with a route map, distance, duration, and estimated cost.")
    parser.add_argument("--username", help="macOS username to fetch the API key from Keychain")
    parser.add_argument("--keychain_service", help="Service name in macOS Keychain to fetch the API key")
    parser.add_argument("--keeper-uid", help="Keeper Security Record UID to fetch the API key")
    parser.add_argument("--origin", required=True, help="Origin address")
    parser.add_argument("--destination", required=True, help="Destination address")
    parser.add_argument("--output", help="Output PDF filename")
    args = parser.parse_args()
    
    # Get API key from specified source
    if args.keeper_uid:
        api_key = get_api_key_from_keeper(args.keeper_uid)
    elif args.username and args.keychain_service:
        api_key = get_api_key_from_keychain(args.username, args.keychain_service)
    else:
        parser.error("You must provide either --keeper-uid OR both --username and --keychain_service to retrieve the API key.")
    
    # Prompt for output filename if not provided
    output_file = args.output
    if not output_file:
        output_file = input("Enter output PDF filename (press Enter for auto-generated name): ")
        output_file = output_file.strip() or None
    
    # Validate output filename if provided
    if output_file:
        output_path = Path(output_file)
        if output_path.suffix.lower() != '.pdf':
            output_file = str(output_path.with_suffix('.pdf'))
            print(f"Output filename changed to: {output_file}")
    
    create_pdf(api_key, args.origin, args.destination, output_file)

if __name__ == "__main__":
    main()
