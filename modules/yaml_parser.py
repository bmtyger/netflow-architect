import yaml

def read_yaml_file(filepath):
    """
    Reads a YAML file and returns its content as a Python dictionary.

    Args:
        filepath (str): The path to the YAML file.

    Returns:
        dict: The content of the YAML file, or None if an error occurs.
    """
    try:
        with open(filepath, 'r') as file:
            yaml_content = yaml.safe_load(file)
        return yaml_content
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {filepath}: {e}")
        return None

def validate_yaml_structure(yaml_data):
    """
    Validates the basic structure of the parsed YAML data.

    Args:
        yaml_data (dict): The parsed YAML content.

    Returns:
        bool: True if the basic structure is valid, False otherwise.
    """
    if not isinstance(yaml_data, dict):
        print("Error: The YAML file should contain a top-level dictionary.")
        return False
    if 'application' not in yaml_data or 'network' not in yaml_data:
        print("Error: The YAML file should contain 'application' and 'network' sections.")
        return False
    return True

if __name__ == '__main__':
    # Example usage for testing
    yaml_file = 'example_requirements.yaml'  # Create a dummy file for testing
    example_content = {
        'application': 'TestApp',
        'region': 'us-east-1',
        'network': {
            'name': 'test-network'
        }
    }
    with open(yaml_file, 'w') as f:
        yaml.dump(example_content, f)

    parsed_data = read_yaml_file(yaml_file)
    if parsed_data:
        print("Parsed YAML Data:")
        print(parsed_data)
        if validate_yaml_structure(parsed_data):
            print("YAML structure is valid.")
        else:
            print("YAML structure is invalid.")