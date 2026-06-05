# er-maps-generator

A Python script to generate a PDF route map with distance, duration, and estimated cost using the Google Maps API.

## Prerequisites

- [mise](https://mise.jdx.dev/) — used to manage the Python version and virtual environment
- macOS Keychain **or** [Keeper Security](https://www.keepersecurity.com/) CLI (`keeper`)

## Setup

This project uses [mise](https://mise.jdx.dev/) to manage the Python version (3.14.0) and create the virtual environment automatically (`.venv`).

1. Install mise: <https://mise.jdx.dev/getting-started.html>
2. Install the configured runtime(s):

```bash
mise install
```

3. Install Python packages into the project virtualenv:

```bash
mise run setup
```

`mise install` installs runtimes (like Python). `mise run setup` installs pip packages from `requirements.txt`.

## Configuration (Optional)

You can avoid passing credential lookup options on every run by creating a local config file named `.er-maps-generator.json` in the project directory.

Example using macOS Keychain:

```json
{
  "username": "your-macos-username",
  "keychain_service": "GoogleMapsAPIKey"
}
```

Example using Keeper:

```json
{
  "keeper_uid": "YOUR_RECORD_UID"
}
```

CLI arguments always override config file values.

## Usage

Activate the mise-managed environment (e.g. via shell hook or `mise activate`), then run the script directly:

```bash
python generate-maps.py \
  --origin "6, avenue des Hauts-Fourneaux L-4362 Esch-sur-Alzette" \
  --destination "Luxembourg Airport" \
  --output route_map.pdf
```

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

1. On a new machine, install Keeper Commander CLI:
  ```bash
  pipx install keepercommander
  ```

2. Log in to Keeper Security (required once):
    ```bash
    keeper login
    ```
    **Note:** You may be prompted for your password on each script run depending on your Keeper Security settings. To avoid repeated password prompts, ensure your Keeper session is configured with persistent login. The script uses the cached session from `~/.keeper/config.json`.

3. Find the **Record UID** of your Google Maps API Key in Keeper (visible in the Web Vault URL or via `keeper search`).
4. Run the script:

```bash
python generate-maps.py \
  --keeper-uid <YOUR_RECORD_UID> \
  --origin "6, avenue des Hauts-Fourneaux L-4362 Esch-sur-Alzette" \
  --destination "Luxembourg Airport" \
  --output route_map.pdf
```
