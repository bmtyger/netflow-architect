import argparse
import yaml
import json
import os
import requests
from modules.flow_diagram_generator import generate_graphical_flow_diagram, generate_textual_flow_diagram
from modules.aws_config_generator import generate_aws_cloudformation
import cloud_deployer  # Import the new module

DEFAULT_REQUIREMENTS_FILE = "network_requirements.yaml"
OUTPUT_CLOUDFORMATION_FILE = "output.json"
SUGGESTED_AWS_REGION_EUROPE = "eu-central-1"

def get_approximate_location():
    try:
        response = requests.get("https://ipinfo.io/json", timeout=5)
        response.raise_for_status()
        data = response.json()
        country = data.get("country")
        return country
    except requests.exceptions.RequestException:
        return None

def main():
    parser = argparse.ArgumentParser(description="Generate network flow diagrams and configurations.")
    parser.add_argument("--visualize", action="store_true", help="Generate a graphical network flow diagram.")
    parser.add_argument("--apply", action="store_true", help="Apply the generated configuration to a cloud provider.")
    parser.add_argument("requirements", nargs='?', default=DEFAULT_REQUIREMENTS_FILE, help="Path to the YAML requirements file.")
    args = parser.parse_args()

    requirements_file = args.requirements

    if not os.path.exists(requirements_file):
        print(f"Error: Requirements file '{requirements_file}' not found.")
        return

    with open(requirements_file, 'r') as f:
        yaml_data = yaml.safe_load(f)

    if args.visualize:
        generate_graphical_flow_diagram(yaml_data)

    if args.apply:
        provider = input("Apply configuration for which provider (aws/azure/gcp)? ").lower()
        if provider == 'aws':
            cloudformation_template = generate_aws_cloudformation(yaml_data)

            # Save the generated CloudFormation template to output.json
            with open(OUTPUT_CLOUDFORMATION_FILE, 'w') as outfile:
                json.dump(cloudformation_template, outfile, indent=2)
            print(f"\nGenerated AWS CloudFormation Template saved to '{OUTPUT_CLOUDFORMATION_FILE}'.")

            confirm_apply = input("Do you want to apply this AWS configuration? (yes/no): ").lower()
            if confirm_apply == 'yes':
                suggested_region = None
                location = get_approximate_location()
                if location == "RO":
                    suggested_region = SUGGESTED_AWS_REGION_EUROPE
                    ask_region = input(f"Do you want to specify a specific AWS region? (yes/no, default: {suggested_region} based on your location): ").lower()
                    if ask_region == 'yes':
                        region = input("Enter the AWS region to deploy to (e.g., us-east-1): ")
                    else:
                        region = suggested_region
                else:
                    ask_region = input("Do you want to specify a specific AWS region? (yes/no, default: uses environment configuration): ").lower()
                    region = None
                    if ask_region == 'yes':
                        region = input("Enter the AWS region to deploy to (e.g., us-east-1): ")

                print("\nAttempting to apply AWS configuration...")
                if cloud_deployer.apply_aws_configuration(cloudformation_template, region=region):
                    print("AWS configuration application process initiated successfully.")
                else:
                    print("Failed to initiate AWS configuration application.")
            else:
                print("AWS configuration application skipped.")
        elif provider == 'azure':
            print("Azure configuration application not yet implemented.")
        elif provider == 'gcp':
            print("GCP configuration application not yet implemented.")
        else:
            print("Invalid cloud provider specified.")
    elif not args.visualize and not args.apply:
        textual_flow = generate_textual_flow_diagram(yaml_data)
        print("\nTextual Network Flow:\n", textual_flow)

if __name__ == "__main__":
    main()