#!/usr/bin/env python3
"""Setup script for Google Cloud Secret Manager.

This script checks if required secrets exist in Google Secret Manager
and prompts the user to create them if missing.
"""

import os
import sys
from google.cloud import secretmanager
from google.api_core import exceptions

# Required secrets
REQUIRED_SECRETS = {
    "alpaca-key": {
        "description": "Alpaca API Key",
        "env_var": "ALPACA_KEY or ALPACA_API_KEY"
    },
    "alpaca-secret": {
        "description": "Alpaca API Secret",
        "env_var": "ALPACA_SECRET or ALPACA_SECRET_KEY"
    },
    "supabase-url": {
        "description": "Supabase Project URL",
        "env_var": "SUPABASE_URL"
    },
    "supabase-key": {
        "description": "Supabase Anon Key",
        "env_var": "SUPABASE_KEY"
    },
    "api-ninjas-key": {
        "description": "API Ninjas Earnings Calendar API Key",
        "env_var": "API_NINJAS_KEY",
        "optional": True
    }
}

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
if not PROJECT_ID:
    PROJECT_ID = input("Enter your GCP Project ID: ").strip()


def check_secret_exists(client, secret_id):
    """Check if a secret exists in Secret Manager."""
    try:
        secret_path = f"projects/{PROJECT_ID}/secrets/{secret_id}"
        client.get_secret(request={"name": secret_path})
        return True
    except exceptions.NotFound:
        return False
    except Exception as e:
        print(f"Error checking secret {secret_id}: {e}")
        return False


def create_secret(client, secret_id, description):
    """Create a new secret in Secret Manager."""
    try:
        parent = f"projects/{PROJECT_ID}"
        secret = client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )
        print(f"✓ Created secret: {secret_id}")
        return secret
    except Exception as e:
        print(f"✗ Error creating secret {secret_id}: {e}")
        return None


def add_secret_version(client, secret_id, secret_value):
    """Add a version to an existing secret."""
    try:
        parent = f"projects/{PROJECT_ID}/secrets/{secret_id}"
        version = client.add_secret_version(
            request={
                "parent": parent,
                "payload": {"data": secret_value.encode("UTF-8")},
            }
        )
        print(f"✓ Added version to secret: {secret_id}")
        return version
    except Exception as e:
        print(f"✗ Error adding version to secret {secret_id}: {e}")
        return None


def get_secret_value(client, secret_id):
    """Get the latest version of a secret."""
    try:
        name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error accessing secret {secret_id}: {e}")
        return None


def main():
    """Main function to set up secrets."""
    print("=" * 80)
    print("Google Cloud Secret Manager Setup")
    print("=" * 80)
    print(f"Project ID: {PROJECT_ID}")
    print("")
    
    # Initialize Secret Manager client
    try:
        client = secretmanager.SecretManagerServiceClient()
    except Exception as e:
        print(f"Error initializing Secret Manager client: {e}")
        print("Make sure you have:")
        print("1. Installed google-cloud-secret-manager: pip install google-cloud-secret-manager")
        print("2. Set up application default credentials: gcloud auth application-default login")
        sys.exit(1)
    
    # Check each required secret
    secrets_to_create = []
    secrets_to_update = []
    
    for secret_id, secret_info in REQUIRED_SECRETS.items():
        description = secret_info["description"]
        env_var = secret_info["env_var"]
        is_optional = secret_info.get("optional", False)
        
        print(f"Checking secret: {secret_id} ({description})...")
        
        if check_secret_exists(client, secret_id):
            # Secret exists, check if user wants to update it
            current_value = get_secret_value(client, secret_id)
            if current_value:
                masked_value = current_value[:4] + "*" * (len(current_value) - 8) + current_value[-4:] if len(current_value) > 8 else "*" * len(current_value)
                print(f"  ✓ Secret exists (current value: {masked_value})")
                
                update = input(f"  Update {secret_id}? (y/N): ").strip().lower()
                if update == 'y':
                    secrets_to_update.append(secret_id)
            else:
                print(f"  ⚠ Secret exists but has no value")
                secrets_to_update.append(secret_id)
        else:
            # Secret doesn't exist
            print(f"  ✗ Secret not found")
            if not is_optional:
                secrets_to_create.append(secret_id)
            else:
                create_optional = input(f"  Create optional secret {secret_id}? (y/N): ").strip().lower()
                if create_optional == 'y':
                    secrets_to_create.append(secret_id)
    
    print("")
    
    # Create missing secrets
    if secrets_to_create:
        print("Creating new secrets...")
        for secret_id in secrets_to_create:
            secret_info = REQUIRED_SECRETS[secret_id]
            description = secret_info["description"]
            env_var = secret_info["env_var"]
            
            # Try to get value from environment first
            env_value = None
            for env_key in env_var.split(" or "):
                env_value = os.getenv(env_key.strip())
                if env_value:
                    break
            
            if env_value:
                use_env = input(f"  Use value from {env_key}? (Y/n): ").strip().lower()
                if use_env != 'n':
                    secret_value = env_value
                else:
                    secret_value = input(f"  Enter {description}: ").strip()
            else:
                secret_value = input(f"  Enter {description}: ").strip()
            
            if secret_value:
                secret = create_secret(client, secret_id, description)
                if secret:
                    add_secret_version(client, secret_id, secret_value)
            else:
                print(f"  ⚠ Skipping {secret_id} (no value provided)")
        print("")
    
    # Update existing secrets
    if secrets_to_update:
        print("Updating existing secrets...")
        for secret_id in secrets_to_update:
            secret_info = REQUIRED_SECRETS[secret_id]
            description = secret_info["description"]
            env_var = secret_info["env_var"]
            
            # Try to get value from environment first
            env_value = None
            for env_key in env_var.split(" or "):
                env_value = os.getenv(env_key.strip())
                if env_value:
                    break
            
            if env_value:
                use_env = input(f"  Use value from {env_key}? (Y/n): ").strip().lower()
                if use_env != 'n':
                    secret_value = env_value
                else:
                    secret_value = input(f"  Enter new {description}: ").strip()
            else:
                secret_value = input(f"  Enter new {description}: ").strip()
            
            if secret_value:
                add_secret_version(client, secret_id, secret_value)
            else:
                print(f"  ⚠ Skipping {secret_id} (no value provided)")
        print("")
    
    # Summary
    print("=" * 80)
    print("Setup Complete!")
    print("=" * 80)
    print("")
    print("Secrets configured in Secret Manager:")
    for secret_id in REQUIRED_SECRETS.keys():
        if check_secret_exists(client, secret_id):
            print(f"  ✓ {secret_id}")
        else:
            print(f"  ✗ {secret_id} (missing)")
    print("")
    print("Next steps:")
    print("1. Run gcp_deploy.sh to deploy the Cloud Run Job")
    print("2. The deployment script will link these secrets to the job")
    print("")


if __name__ == "__main__":
    main()

