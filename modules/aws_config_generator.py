import yaml

def generate_aws_cloudformation(requirements):
    """
    Generates an AWS CloudFormation template based on the network requirements.

    Args:
        requirements (dict): A dictionary containing the network requirements.

    Returns:
        dict: A dictionary representing the AWS CloudFormation template.
    """
    template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": f"Network infrastructure for {requirements.get('application', 'YourApp')}",
        "Resources": {}
    }

    network = requirements.get("network", {})
    vpc_config = network.get("ip_address_space", "10.0.0.0/16")
    network_name = network.get("name", "your-network-name")
    subnets_config = network.get("subnets", [])
    load_balancer_config = network.get("load_balancer", {})
    security_config = network.get("security", {})
    firewall_rules = network.get("firewall", {}).get("rules", [])

    # VPC
    template["Resources"]["VPC"] = {
        "Type": "AWS::EC2::VPC",
        "Properties": {
            "CidrBlock": vpc_config,
            "EnableDnsSupport": True,
            "EnableDnsHostnames": True,
            "Tags": [{"Key": "Name", "Value": network_name}]
        }
    }

    # Subnets
    for i, subnet in enumerate(subnets_config):
        logical_resource_id = subnet["name"].replace("-", "").lower()
        az_selector = 0 if i == 0 else 1  # Simple AZ selection for two subnets
        template["Resources"][logical_resource_id] = {
            "Type": "AWS::EC2::Subnet",
            "Properties": {
                "VpcId": {"Ref": "VPC"},
                "CidrBlock": subnet["cidr"],
                "AvailabilityZone": {"Fn::Select": [az_selector, {"Fn::GetAZs": {"Ref": "AWS::Region"}}]},
                "MapPublicIpOnLaunch": subnet.get("purpose", "").lower() == "frontend",
                "Tags": [{"Key": "Name", "Value": subnet["name"]}]
            }
        }

    # Internet Gateway
    template["Resources"]["InternetGateway"] = {
        "Type": "AWS::EC2::InternetGateway",
        "Properties": {
            "Tags": [{"Key": "Name", "Value": f"{network_name}-igw"}]
        }
    }

    # VPC Gateway Attachment
    template["Resources"]["VPCGatewayAttachment"] = {
        "Type": "AWS::EC2::VPCGatewayAttachment",
        "Properties": {
            "VpcId": {"Ref": "VPC"},
            "InternetGatewayId": {"Ref": "InternetGateway"}
        }
    }

    # Application Security Group (even if LB is disabled, we might need it for instances)
    template["Resources"]["ApplicationSecurityGroup"] = {
        "Type": "AWS::EC2::SecurityGroup",
        "Properties": {
            "GroupDescription": "Security group for application instances",
            "VpcId": {"Ref": "VPC"},
            "SecurityGroupIngress": [],
            "SecurityGroupEgress": [
                {
                    "IpProtocol": "-1",
                    "CidrIpRanges": ["0.0.0.0/0"]
                }
            ],
            "Tags": [{"Key": "Name", "Value": f"{network_name}-app-sg"}]
        }
    }

    # Load Balancer (if enabled)
    if load_balancer_config.get("enabled", False):
        lb_name = f"{network_name}-lb".replace("-", "").lower()
        template["Resources"][lb_name] = {
            "Type": "AWS::ElasticLoadBalancingV2::LoadBalancer",
            "Properties": {
                "Scheme": "internet-facing",
                "Subnets": [
                    {"Ref": "frontendsubnet"}
                ],
                "SecurityGroups": [{"Ref": "ApplicationSecurityGroup"}],
                "Tags": [{"Key": "Name", "Value": lb_name}]
            }
        }

        listeners = []
        for listener_config in load_balancer_config.get("listeners", []):
            listeners.append({
                "Port": listener_config["port"],
                "Protocol": listener_config["protocol"],
                "DefaultActions": [{
                    "Type": "forward",
                    "TargetGroupArn": {"Ref": f"{lb_name}TargetGroup"}
                }]
            })
        template["Resources"][f"{lb_name}Listener"] = {
            "Type": "AWS::ElasticLoadBalancingV2::Listener",
            "Properties": {
                "LoadBalancerArn": {"Ref": lb_name},
                "DefaultActions": [{
                    "Type": "forward",
                    "TargetGroupArn": {"Ref": f"{lb_name}TargetGroup"}
                }],
                "Port": load_balancer_config["listeners"][0]["port"], # Default to first listener port/protocol
                "Protocol": load_balancer_config["listeners"][0]["protocol"]
            }
        }
        if listeners:
            template["Resources"][f"{lb_name}Listener"]["Properties"]["DefaultActions"] = listeners[0]["DefaultActions"]
            template["Resources"][f"{lb_name}Listener"]["Properties"]["Port"] = listeners[0]["Port"]
            template["Resources"][f"{lb_name}Listener"]["Properties"]["Protocol"] = listeners[0]["Protocol"]
            # Handle multiple listeners (simplified for now)
            for i, listener_config in enumerate(listeners):
                listener_resource_id = f"{lb_name}Listener{i+1}"
                template["Resources"][listener_resource_id] = {
                    "Type": "AWS::ElasticLoadBalancingV2::Listener",
                    "Properties": {
                        "LoadBalancerArn": {"Ref": lb_name},
                        "DefaultActions": [{
                            "Type": "forward",
                            "TargetGroupArn": {"Ref": f"{lb_name}TargetGroup"}
                        }],
                        "Port": listener_config["port"],
                        "Protocol": listener_config["protocol"]
                    }
                }


        template["Resources"][f"{lb_name}TargetGroup"] = {
            "Type": "AWS::ElasticLoadBalancingV2::TargetGroup",
            "Properties": {
                "Port": load_balancer_config.get("listeners", [{}])[0].get("port", 80),
                "Protocol": load_balancer_config.get("listeners", [{}])[0].get("protocol", "HTTP").upper(),
                "VpcId": {"Ref": "VPC"},
                "HealthCheckPath": load_balancer_config.get("health_check_path", "/"),
                "Tags": [{"Key": "Name", "Value": f"{lb_name}-tg"}]
            }
        }

    return template

if __name__ == '__main__':
    # Example usage:
    requirements_data = {
        "application": "MyWebApp",
        "network": {
            "name": "my-network",
            "ip_address_space": "10.10.0.0/16",
            "subnets": [
                {"name": "public-subnet-a", "cidr": "10.10.1.0/24", "purpose": "Frontend"},
                {"name": "private-subnet-b", "cidr": "10.10.2.0/24", "purpose": "Backend"}
            ],
            "load_balancer": {
                "enabled": True,
                "type": "Application",
                "listeners": [
                    {"port": 80, "protocol": "HTTP"},
                    {"port": 443, "protocol": "HTTPS"}
                ],
                "health_check_path": "/health"
            },
            "security": {
                "network_segmentation": True
            },
            "firewall": {
                "rules": [
                    {"action": "Allow", "source": "Internet", "destination": "public-subnet-a", "protocol": "TCP", "ports": [80, 443], "name": "allow-web-access"}
                ]
            }
        },
        "type": "web",
        "region": "eu-west-1"
    }

    cloudformation_template = generate_aws_cloudformation(requirements_data)
    import json
    print(json.dumps(cloudformation_template, indent=2))