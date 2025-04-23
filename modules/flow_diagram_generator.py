from graphviz import Digraph
import subprocess
import platform
import os  # Import the os module for path manipulation

def generate_textual_flow_diagram(yaml_data):
    """Generates a textual representation of the network flow."""
    flow = "Network Flow:\n"
    network = yaml_data.get('network', {})
    subnets = network.get('subnets', [])
    firewall_rules = network.get('firewall', {}).get('rules', [])
    load_balancer = network.get('load_balancer', {})

    if network.get('name'):
        flow += f"  Network: {network['name']}\n"
    if subnets:
        flow += "  Subnets:\n"
        for subnet in subnets:
            flow += f"    - {subnet.get('name', 'Unnamed')} ({subnet.get('cidr', 'No CIDR')})\n"
    if load_balancer.get('enabled'):
        flow += f"  Load Balancer ({load_balancer.get('type', 'Generic')}):\n"
        for listener in load_balancer.get('listeners', []):
            flow += f"    - Listener on Port {listener.get('port', '?')} ({listener.get('protocol', 'Unknown')})\n"
    if firewall_rules:
        flow += "  Firewall Rules:\n"
        for rule in firewall_rules:
            flow += f"    - Allow {rule.get('protocol', 'Any')} from {rule.get('source', 'Any')} to {rule.get('destination', 'Any')} on ports {rule.get('ports', 'Any')}\n"
    return flow

def generate_graphical_flow_diagram(yaml_data, output_path="network_flow.png"):
    """Generates a graphical representation of the network flow using Graphviz with icons."""
    dot = Digraph(comment='Network Flow', format='png')
    network = yaml_data.get('network', {})
    subnets = network.get('subnets', [])
    firewall_rules = network.get('firewall', {}).get('rules', [])
    load_balancer = network.get('load_balancer', {})

    # Define icon paths
    icons_dir = 'icons'
    network_icon = os.path.join(icons_dir, 'network.png')
    subnet_icon = os.path.join(icons_dir, 'subnet.png')
    load_balancer_icon = os.path.join(icons_dir, 'load_balancer.png')
    firewall_icon = os.path.join(icons_dir, 'firewall.png')
    internet_icon = os.path.join(icons_dir, 'internet.png')

    # Add Network Node with Icon
    network_name = network.get('name', 'Network')
    dot.node('network', shape='none', image=network_icon, labelloc='b', label=network_name, fixedsize='true', width='1.5', height='1.5')

    # Add Subnet Nodes with Icons
    for subnet in subnets:
        subnet_name = subnet.get('name', 'Subnet')
        subnet_id = subnet_name.replace('-', '_')
        dot.node(subnet_id, shape='none', image=subnet_icon, labelloc='b', label=subnet_name, fixedsize='true', width='1.0', height='1.0')
        dot.edge('network', subnet_id, style='dashed')

    # Add Load Balancer Node with Icon and Listeners
    if load_balancer.get('enabled'):
        lb_name = load_balancer.get('type', 'LB')
        lb_id = 'load_balancer'
        dot.node(lb_id, shape='none', image=load_balancer_icon, labelloc='b', label=f"{lb_name} LB", fixedsize='true', width='1.5', height='1.5')
        dot.edge('network', lb_id)
        for i, listener in enumerate(load_balancer.get('listeners', [])):
            port = listener.get('port', '?')
            protocol = listener.get('protocol', 'Unknown')
            listener_label = f"Listener\n{protocol}:{port}"
            listener_id = f'listener_{i}'
            dot.node(listener_id, listener_label, shape='box', style='rounded') # Using a box with text for listeners
            dot.edge(lb_id, listener_id)
            for subnet in subnets:
                if subnet.get('purpose', '').lower() == 'frontend':
                    dot.edge(listener_id, subnet.get('name', '').replace('-', '_')) # Basic Frontend to LB connection

    # Add Firewall Rules with Icons (using edges with labels for flow)
    if firewall_rules:
        for rule in firewall_rules:
            source = rule.get('source', 'Internet').replace('-', '_')
            destination = rule.get('destination', 'Target').replace('-', '_')
            ports = rule.get('ports', 'Any')
            protocol = rule.get('protocol', 'Any')
            label = f"Allow {protocol}:{ports}"

            # Source Node with Icon
            source_node = 'internet' if 'internet' in source.lower() else source
            if source_node not in dot.body:
                source_label = source.replace('_', ' ').title()
                source_icon_path = internet_icon if 'internet' in source.lower() else firewall_icon
                dot.node(source_node, shape='none', image=source_icon_path, labelloc='b', label=source_label, fixedsize='true', width='1.0', height='1.0')

            # Destination Node with Icon
            dest_node = destination
            if dest_node not in dot.body:
                dest_subnet = next((s for s in subnets if s.get('name', '').replace('-', '_') == dest_node), None)
                dest_node_label = dest_subnet['name'] if dest_subnet else dest_node.replace('_', ' ').title()
                dest_node_icon_path = subnet_icon if dest_subnet else firewall_icon # Assuming non-subnet destinations might be firewalls
                dot.node(dest_node, shape='none', image=dest_node_icon_path, labelloc='b', label=dest_node_label, fixedsize='true', width='1.0', height='1.0')

            dot.edge(source_node, dest_node, label=label, arrowhead='vee')

    try:
        dot.render(output_path, view=False, cleanup=True)
        print(f"Graphical network flow with icons saved to: {output_path}")

        # Open the generated PNG file
        if platform.system() == "Windows":
            subprocess.run(["start", output_path], check=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", output_path], check=True)
        else:  # Linux and other Unix-like
            subprocess.run(["xdg-open", output_path], check=True)
        print(f"Opened the graphical network flow with icons: {output_path}")

    except Exception as e:
        print(f"Error generating or opening graphical flow with icons: {e}")
        print("Make sure Graphviz is installed and in your system's PATH, and icons are in the 'icons' directory.")

if __name__ == '__main__':
    # Example usage for testing
    example_requirements = {
        'application': 'TestApp',
        'network': {
            'name': 'test-network',
            'ip_address_space': '10.0.0.0/16',
            'subnets': [
                {'name': 'frontend-subnet', 'cidr': '10.0.1.0/24', 'purpose': 'Frontend'},
                {'name': 'backend-subnet', 'cidr': '10.0.2.0/24', 'purpose': 'Backend'}
            ],
            'load_balancer': {'enabled': True, 'type': 'Application', 'listeners': [{'port': 80, 'protocol': 'HTTP'}, {'port': 443, 'protocol': 'HTTPS'}]},
            'firewall': {
                'rules': [
                    {'name': 'allow-http', 'ports': [80], 'protocol': 'TCP', 'source': 'Internet', 'destination': 'frontend-subnet'},
                    {'name': 'allow-https', 'ports': [443], 'protocol': 'TCP', 'source': 'Internet', 'destination': 'frontend-subnet'},
                    {'name': 'allow-backend', 'ports': [8080], 'protocol': 'TCP', 'source': 'frontend-subnet', 'destination': 'backend-subnet'}
                ]
            }
        }
    }
    # Create an 'icons' directory and place dummy PNG files for testing
    if not os.path.exists('icons'):
        os.makedirs('icons')
        open(os.path.join('icons', 'network.png'), 'a').close()
        open(os.path.join('icons', 'subnet.png'), 'a').close()
        open(os.path.join('icons', 'load_balancer.png'), 'a').close()
        open(os.path.join('icons', 'firewall.png'), 'a').close()
        open(os.path.join('icons', 'internet.png'), 'a').close()

    generate_graphical_flow_diagram(example_requirements)
    print("\nTextual Flow:")
    print(generate_textual_flow_diagram(example_requirements))