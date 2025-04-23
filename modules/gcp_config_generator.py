import yaml

def generate_gcp_config(yaml_data):
    """
    Generates a basic GCP network configuration based on the network
    requirements in the provided YAML data.

    Args:
        yaml_data (dict): The parsed network requirements YAML data.

    Returns:
        dict: A dictionary representing the GCP network configuration.
    """
    config = {}
    network_section = yaml_data.get('network', {})
    project_id = "your-gcp-project-id"  # Replace with your actual GCP project ID
    region = yaml_data.get('region', 'us-central1') # Default GCP region

    config['network'] = {
        'name': network_section.get('name', 'default-network').replace('-', ''),
        'autoCreateSubnetworks': False # We will define subnets explicitly
    }

    config['subnetworks'] = []
    subnets = network_section.get('subnets', [])
    for subnet_config in subnets:
        config['subnetworks'].append({
            'name': subnet_config.get('name', 'default-subnet').replace('-', ''),
            'ipCidrRange': subnet_config.get('cidr'),
            'region': region,
            'network': f"projects/{project_id}/global/networks/{config['network']['name']}"
        })

    config['firewall'] = {'rules': []}
    firewall_rules = network_section.get('firewall', {}).get('rules', [])
    for rule in firewall_rules:
        direction = 'INGRESS'
        if rule.get('source') == 'Internet':
            source_ranges = ['0.0.0.0/0']
            source_tags = None
        elif rule.get('source') == 'frontend-subnet': # Basic mapping, needs refinement
            source_ranges = None
            source_tags = [f"{config['subnetworks'][0]['name']}-tag"] # Assuming first subnet is frontend
        elif rule.get('source') == 'backend-subnet': # Basic mapping, needs refinement
            source_ranges = None
            source_tags = [f"{config['subnetworks'][1]['name']}-tag"] # Assuming second subnet is backend
        else:
            source_ranges = [rule.get('source')]
            source_tags = None

        destination = rule.get('destination')
        if destination == 'frontend-subnet':
            destination_tags = [f"{config['subnetworks'][0]['name']}-tag"]
            destination_ranges = None
        elif destination == 'backend-subnet':
            destination_tags = [f"{config['subnetworks'][1]['name']}-tag"]
            destination_ranges = None
        else:
            destination_tags = None
            destination_ranges = None # Needs more sophisticated mapping

        ports = rule.get('ports', [])
        protocol = rule.get('protocol', 'TCP').lower()
        action = rule.get('action', 'Allow').upper()

        for port in ports:
            config['firewall']['rules'].append({
                'name': rule.get('name', 'default-rule').replace('-', '') + f"-{protocol}-{port}",
                'direction': direction,
                'priority': 1000, # Default priority
                'match': {
                    'config': {
                        'ipProtocol': protocol,
                        'ports': [str(port)]
                    }
                },
                'sourceRanges': source_ranges,
                'sourceTags': source_tags,
                'destinationRanges': destination_ranges,
                'destinationTags': destination_tags,
                'action': action,
                'network': f"projects/{project_id}/global/networks/{config['network']['name']}"
            })

    # Basic Load Balancer configuration (HTTP only for simplicity)
    load_balancer_config = network_section.get('load_balancer', {})
    if load_balancer_config.get('enabled'):
        lb_name = f"{config['network']['name']}-lb".replace('-', '')
        config['compute'] = {
            'forwardingRules': [{
                'name': f"{lb_name}-forwarding-rule",
                'region': region,
                'target': f"projects/{project_id}/global/backendServices/{lb_name}-backend-service",
                'ports': [listener.get('port', 80) for listener in load_balancer_config.get('listeners', []) if listener.get('protocol', 'HTTP').upper() == 'HTTP'],
                'ipProtocol': 'TCP',
                'loadBalancingScheme': 'EXTERNAL'
            }],
            'backendServices': [{
                'name': f"{lb_name}-backend-service",
                'protocol': 'HTTP',
                'healthChecks': [f"projects/{project_id}/global/healthChecks/{lb_name}-health-check"],
                'backends': [] # Instances will be added later
            }],
            'healthChecks': [{
                'name': f"{lb_name}-health-check",
                'httpHealthCheck': {
                    'port': 80, # Default health check port
                    'requestPath': load_balancer_config.get('health_check_path', '/')
                }
            }]
        }

    return config

if __name__ == '__main__':
    # Example usage for testing
    example_requirements = {
        'application': 'TestGCPApp',
        'region': 'us-central1',
        'network': {
            'name': 'test-network',
            'ip_address_space': '10.0.0.0/16',
            'subnets': [
                {'name': 'frontend-subnet', 'cidr': '10.0.1.0/24', 'purpose': 'Frontend'},
                {'name': 'backend-subnet', 'cidr': '10.0.2.0/24', 'purpose': 'Backend'}
            ],
            'load_balancer': {'enabled': True, 'listeners': [{'port': 80}, {'port': 443, 'protocol': 'HTTPS'}], 'health_check_path': '/health'},
            'firewall': {
                'rules': [
                    {'name': 'allow-http', 'ports': [80], 'protocol': 'TCP', 'source': 'Internet', 'destination': 'frontend-subnet'},
                    {'name': 'allow-https', 'ports': [443], 'protocol': 'TCP', 'source': 'Internet', 'destination': 'frontend-subnet'},
                    {'name': 'allow-backend', 'ports': [8080], 'protocol': 'TCP', 'source': 'frontend-subnet', 'destination': 'backend-subnet'}
                ]
            },
            'security': {'network_segmentation': True}
        }
    }
    gcp_config = generate_gcp_config(example_requirements)
    print(yaml.dump(gcp_config, indent=2))