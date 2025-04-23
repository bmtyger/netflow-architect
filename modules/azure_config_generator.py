import json

def generate_azure_arm_template(yaml_data):
    """
    Generates an Azure ARM template based on the network requirements
    in the provided YAML data.

    Args:
        yaml_data (dict): The parsed network requirements YAML data.

    Returns:
        dict: A dictionary representing the Azure ARM template.
    """
    template = {
        "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {},
        "variables": {},
        "resources": [],
        "outputs": {}
    }

    network_section = yaml_data.get('network', {})
    location = yaml_data.get('region', 'eastus')  # Default Azure region

    # -------------------- Virtual Network --------------------
    vnet_name = network_section.get('name', 'defaultVnet').replace('-', '')
    vnet_address_space = network_section.get('ip_address_space', '10.0.0.0/16')
    template['resources'].append({
        "type": "Microsoft.Network/virtualNetworks",
        "apiVersion": "2020-11-01",
        "name": vnet_name,
        "location": location,
        "properties": {
            "addressSpace": {
                "addressPrefixes": [vnet_address_space]
            },
            "enableDnsSupport": True,
            "enableVmProtection": False,
            "subnets": []
        }
    })

    # -------------------- Network Security Group --------------------
    nsg_name = f'{vnet_name}-nsg'
    template['resources'].append({
        "type": "Microsoft.Network/networkSecurityGroups",
        "apiVersion": "2020-11-01",
        "name": nsg_name,
        "location": location,
        "properties": {
            "securityRules": []
        }
    })

    subnets = []
    if isinstance(network_section, dict):
        subnets = network_section.get('subnets', [])

    # -------------------- Public IP Address (if needed for Load Balancer) --------------------
    load_balancer_config = network_section.get('load_balancer', {})
    if load_balancer_config.get('enabled'):
        public_ip_name = f'{vnet_name}-pip'
        template['resources'].append({
            "type": "Microsoft.Network/publicIPAddresses",
            "apiVersion": "2020-11-01",
            "name": public_ip_name,
            "location": location,
            "properties": {
                "publicIPAllocationMethod": "Static"  # Or "Dynamic"
            }
        })

        # -------------------- Load Balancer --------------------
        lb_name = f'{vnet_name}-lb'
        frontend_ip_config_name = 'frontendIPConfig'
        template['resources'].append({
            "type": "Microsoft.Network/loadBalancers",
            "apiVersion": "2020-11-01",
            "name": lb_name,
            "location": location,
            "dependsOn": [
                f"Microsoft.Network/publicIPAddresses/{public_ip_name}",
                f"Microsoft.Network/virtualNetworks/{vnet_name}"
            ],
            "properties": {
                "frontendIPConfigurations": [
                    {
                        "name": frontend_ip_config_name,
                        "properties": {
                            "publicIPAddress": {
                                "id": f"[resourceId('Microsoft.Network/publicIPAddresses', '{public_ip_name}')]"
                            }
                        }
                    }
                ],
                "backendAddressPools": [],
                "loadBalancingRules": [],
                "probes": []
            }
        })

        # -------------------- Load Balancing Rules --------------------
        listeners = load_balancer_config.get('listeners', [])
        for i, listener in enumerate(listeners):
            listener_port = listener.get('port', 80)
            listener_protocol = listener.get('protocol', 'TCP').upper()
            lb_rule_name = f'LBRule{listener_port}'
            template['resources'][3]['properties']['loadBalancingRules'].append({
                "name": f'{lb_rule_name}',
                "properties": {
                    "frontendIPConfiguration": {
                        "id": f"[resourceId('Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations', '{frontend_ip_config_name}')]"
                    },
                    "frontendPort": listener_port,
                    "backendPort": listener_port,
                    "protocol": listener_protocol,
                    "enableFloatingIP": False,
                    "idleTimeoutInMinutes": 4,
                    "backendAddressPool": {
                        "id": f"[resourceId('Microsoft.Network/loadBalancers/{lb_name}/backendAddressPools', 'backendPool')]"
                    },
                    "enableTcpReset": False
                }
            })

        # -------------------- Backend Address Pool --------------------
        template['resources'][3]['properties']['backendAddressPools'].append({
            "name": "backendPool",
            "properties": {}
        })

        # -------------------- Probe --------------------
        health_check_path = load_balancer_config.get('health_check_path', '/')
        probe_name = 'httpProbe'
        template['resources'][3]['properties']['probes'].append({
            "name": probe_name,
            "properties": {
                "protocol": "Http",
                "port": 80,  # Default probe port
                "path": health_check_path,
                "intervalInSeconds": 15,
                "numberOfProbes": 2
            }
        })

    # -------------------- Security Rules --------------------
    firewall_rules = network_section.get('firewall', {}).get('rules', [])
    nsg_index = 1 # NSG is now the second resource (index 1)
    for rule in firewall_rules:
        rule_name = rule.get('name', 'defaultRule').replace('-', '')
        ports = rule.get('ports', [])
        protocol = rule.get('protocol', 'TCP').upper()
        source = rule.get('source', '*')  # Azure uses '*' for any
        destination = rule.get('destination', '*') # Needs more specific mapping later
        priority = 100 + len(template['resources'][nsg_index]['properties']['securityRules']) # Basic priority

        for port in ports:
            template['resources'][nsg_index]['properties']['securityRules'].append({
                "name": f'{rule_name}-{port}',
                "properties": {
                    "priority": priority,
                    "direction": "Inbound",
                    "access": "Allow",
                    "protocol": protocol,
                    "sourcePortRange": "*",
                    "destinationPortRange": str(port),
                    "sourceAddressPrefix": source,
                    "destinationAddressPrefix": destination
                }
            })

    # -------------------- Subnet Association with NSG --------------------
    for subnet_config in subnets: # <--- Line 170 where the error occurred
        subnet_name = subnet_config.get('name', 'defaultSubnet').replace('-', '')
        template['resources'].append({
            "type": "Microsoft.Network/virtualNetworks/subnets",
            "apiVersion": "2020-11-01",
            "name": f"{vnet_name}/{subnet_name}",
            "location": location,
            "dependsOn": [
                f"Microsoft.Network/virtualNetworks/{vnet_name}",
                f"Microsoft.Network/networkSecurityGroups/{nsg_name}"
            ],
            "properties": {
                "addressPrefix": subnet_config.get('cidr'),
                "networkSecurityGroup": {
                    "id": f"[resourceId('Microsoft.Network/networkSecurityGroups', '{nsg_name}')]"
                }
            }
        })

    return template

if __name__ == '__main__':
    # Example usage for testing
    example_requirements = {
        'application': 'TestApp',
        'region': 'westeurope',
        'network': {
            'name': 'testVnet',
            'ip_address_space': '10.0.0.0/16',
            'subnets': [
                {'name': 'frontendSubnet', 'cidr': '10.0.1.0/24', 'purpose': 'Frontend'},
                {'name': 'backendSubnet', 'cidr': '10.0.2.0/24', 'purpose': 'Backend'}
            ],
            'load_balancer': {'enabled': True, 'listeners': [{'port': 80}, {'port': 443}], 'health_check_path': '/'},
            'firewall': {
                'rules': [
                    {'name': 'allowHttp', 'ports': [80], 'protocol': 'TCP', 'source': 'Internet', 'destination': 'frontendSubnet'},
                    {'name': 'allowHttps', 'ports': [443], 'protocol': 'TCP', 'source': 'Internet', 'destination': 'frontendSubnet'},
                    {'name': 'allowBackend', 'ports': [8080], 'protocol': 'TCP', 'source': '10.0.1.0/24', 'destination': 'backendSubnet'}
                ]
            },
            'security': {'network_segmentation': True}
        }
    }
    azure_template = generate_azure_arm_template(example_requirements)
    print(json.dumps(azure_template, indent=2))

    example_requirements_no_lb = {
        'application': 'TestAppNoLB',
        'region': 'westeurope',
        'network': {
            'name': 'testVnetNoLB',
            'ip_address_space': '10.0.0.0/16',
            'load_balancer': {'enabled': False},
            'firewall': {
                'rules': []
            },
            'security': {'network_segmentation': True},
            'subnets': [
                {'name': 'subnetA', 'cidr': '10.0.1.0/24'}
            ]
        }
    }
    azure_template_no_lb = generate_azure_arm_template(example_requirements_no_lb)
    print("\nNo Load Balancer:")
    print(json.dumps(azure_template_no_lb, indent=2))