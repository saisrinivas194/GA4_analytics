#!/usr/bin/env python3
"""
Helper script to convert service-account-key.json to Streamlit secrets TOML format.

Usage:
    python convert_to_toml.py [property_id]

This will read service-account-key.json and output the TOML format
for Streamlit Cloud secrets.
"""

import json
import sys
import os

def convert_json_to_toml(json_path='service-account-key.json', property_id=None):
    """Convert service account JSON to TOML format for Streamlit secrets."""
    
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found!", file=sys.stderr)
        sys.exit(1)
    
    with open(json_path, 'r') as f:
        sa_data = json.load(f)
    
    # Get property ID from argument or prompt
    if not property_id:
        property_id = input("Enter your GA4 Property ID (numeric): ").strip()
    
    if not property_id:
        print("Error: Property ID is required!", file=sys.stderr)
        sys.exit(1)
    
    # Build TOML output
    toml_lines = [
        "[ga4]",
        f'property_id = "{property_id}"',
        "date_range_days = 30",
        "",
        "[ga4.service_account]",
        f'type = "{sa_data["type"]}"',
        f'project_id = "{sa_data["project_id"]}"',
        f'private_key_id = "{sa_data["private_key_id"]}"',
        "",
        "# Private key (using triple quotes for multi-line)",
        'private_key = """' + sa_data["private_key"] + '"""',
        "",
        f'client_email = "{sa_data["client_email"]}"',
        f'client_id = "{sa_data["client_id"]}"',
        f'auth_uri = "{sa_data["auth_uri"]}"',
        f'token_uri = "{sa_data["token_uri"]}"',
        f'auth_provider_x509_cert_url = "{sa_data["auth_provider_x509_cert_url"]}"',
        f'client_x509_cert_url = "{sa_data["client_x509_cert_url"]}"',
    ]
    
    # Add universe_domain if present
    if "universe_domain" in sa_data:
        toml_lines.append(f'universe_domain = "{sa_data["universe_domain"]}"')
    
    return "\n".join(toml_lines)


if __name__ == "__main__":
    property_id = sys.argv[1] if len(sys.argv) > 1 else None
    toml_output = convert_json_to_toml(property_id=property_id)
    
    print("\n" + "="*60)
    print("Copy the following TOML and paste into Streamlit Cloud Secrets:")
    print("="*60 + "\n")
    print(toml_output)
    print("\n" + "="*60)
    print("Steps:")
    print("1. Copy the TOML above")
    print("2. Go to Streamlit Cloud → Your App → Settings → Secrets")
    print("3. Paste the TOML into the secrets editor")
    print("4. Save and redeploy")
    print("="*60 + "\n")

