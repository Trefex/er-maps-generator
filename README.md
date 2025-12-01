# er-maps-generator

A Python script to generate a PDF route map with distance, duration, and estimated cost using the Google Maps API.

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

You can provide the Google Maps API key either via macOS Keychain or Keeper Security.

### Option 1: Using macOS Keychain

1. Store your API key in the macOS Keychain.
2. Run the script:

```bash
python generate-maps.py \
  --username $USER \
  --keychain_service GoogleMapsAPIKey \
  --origin "6, avenue des Hauts-Fourneaux L-4362 Esch-sur-Alzette" \
  --destination "Luxembourg Airport" \
  --output route_map.pdf
```

### Option 2: Using Keeper Security

1. Log in to Keeper Security (required once):
    ```bash
    keeper login
    ```
    **Note:** You may be prompted for your password on each script run depending on your Keeper Security settings. To avoid repeated password prompts, ensure your Keeper session is configured with persistent login. The script uses the cached session from `~/.keeper/config.json`.

2. Find the **Record UID** of your Google Maps API Key in Keeper (visible in the Web Vault URL or via `keeper search`).
3. Run the script:

```bash
python generate-maps.py \
  --keeper-uid <YOUR_RECORD_UID> \
  --origin "6, avenue des Hauts-Fourneaux L-4362 Esch-sur-Alzette" \
  --destination "Luxembourg Airport" \
  --output route_map.pdf
```
