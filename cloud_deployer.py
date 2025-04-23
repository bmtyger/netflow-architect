# cloud_deployer.py
import boto3
import json
from botocore.exceptions import ClientError

def apply_aws_configuration(cloudformation_template, region=None):
    """Applies the generated CloudFormation template to AWS."""
    cf_client = boto3.client('cloudformation', region_name=region)
    stack_name = "NetflowArchitectStack"  # Define a consistent stack name

    try:
        print(f"Initiating CloudFormation stack creation for '{stack_name}' in region '{region if region else 'default'}'...")
        response = cf_client.create_stack(
            StackName=stack_name,
            TemplateBody=json.dumps(cloudformation_template),
            Capabilities=['CAPABILITY_IAM']  # If your template creates IAM roles
            # Add other parameters as needed (e.g., Parameters)
        )
        print(f"CloudFormation stack '{stack_name}' creation initiated successfully.")
        print(f"Stack ID: {response['StackId']}")
        return True
    except cf_client.exceptions.AlreadyExistsException:
        print(f"CloudFormation stack '{stack_name}' already exists. Attempting to update...")
        try:
            response = cf_client.update_stack(
                StackName=stack_name,
                TemplateBody=json.dumps(cloudformation_template),
                Capabilities=['CAPABILITY_IAM']  # If your template creates/updates IAM roles
                # Add other parameters as needed
            )
            print(f"CloudFormation stack '{stack_name}' update initiated successfully.")
            print(f"Stack ID: {response['StackId']}")
            return True
        except ClientError as e:
            print(f"Error updating stack '{stack_name}': {e}")
            return False
    except cf_client.exceptions.InsufficientCapabilitiesException as e:
        print(f"Error creating stack '{stack_name}': {e}")
        print("You might need to acknowledge IAM capabilities.")
        return False
    except ClientError as e:
        print(f"Error creating stack '{stack_name}': {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during CloudFormation deployment: {e}")
        return False

# You can add functions for Azure and GCP deployment here later