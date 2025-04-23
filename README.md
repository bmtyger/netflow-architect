# netflow-architect
some tests for a freeware solution

Basic Architect flow :

+-----------------------+
|    User (YAML File)   |
+-----------------------+
          | (YAML Input)
          v
+-----------------------+
|   NetFlow Architect   |
|   (Python Application)|
+-----------------------+
          |
          v
+-----------------------------------------------------+
|             Cloud Configuration Modules             |
+-----------------------------------------------------+
| +-----------------+   +-----------------+   +-----------------+ |
| |   Azure Module  |---|   GCP Module    |---|   AWS Module    | |
| +-----------------+   +-----------------+   +-----------------+ |
+-----------------------------------------------------+
          | (YAML Output)
          v
+-----------------------+
|   Cloud Provider      |
|   (Azure, GCP, AWS)   |
+-----------------------+

## files details

1. # yaml_parser.py
    ### read_yaml_file(filepath): 
        - This function takes the path to a YAML file, reads its content using yaml.safe_load() (for security), and returns the data as a Python dictionary. It also includes basic error handling for file not found and YAML parsing errors.
    ### validate_yaml_structure(yaml_data): 
        - This function checks if the parsed YAML data is a dictionary and if it contains the essential top-level keys application and network. You can extend this validation later to check the structure of the network section.
    ### if __name__ == '__main__':
        - This block provides a simple example of how to use the functions for testing purposes. It creates a dummy example_requirements.yaml file, reads it, and validates its structure.
2. # yaml_generator.py
    ### generate_generic_yaml(): 
        - This function creates a Python dictionary that represents the generic YAML configuration we discussed. The values are placeholders or common defaults.
    ### if __name__ == '__main__':: 
        - This block demonstrates how to use the function. It calls generate_generic_yaml() and then uses the PyYAML library to print the dictionary as a formatted YAML string.
3. # flow_diagram_generator.py
    ### generate_textual_flow_diagram(yaml_data): 
        - This function takes the parsed YAML data as input and generates a simple string representing the network flow.
        - It starts with [User].
        - It checks if a load balancer is enabled in the YAML and adds -> Load Balancer if it is.
        - It tries to identify "frontend" and "backend" subnets based on their purpose and includes them in the flow. If subnets are present but not identified as frontend or backend, it defaults to [Application].
        - If the type of the application is "database", it adds -> [Database] at the end.
    ### __name__ == '__main__': 
        - block provides examples of how to use the function with different YAML structures.
    ### Import Digraph: 
        - We import the Digraph class from the graphviz library.
    ### generate_graphical_flow_diagram function:
        - It takes yaml_data and an optional output_path.
        - It creates a Digraph object.
        - It extracts network components (network, subnets, load balancer, firewall rules) from the YAML data.
        - Nodes: It adds nodes to the graph for the network, subnets, and the load balancer.
        - Edges: It adds edges to represent relationships (e.g., network contains subnet, load balancer in network, listener on load balancer, basic frontend to load balancer connection, firewall rules as connections between source and destination). The mapping of sources and destinations in firewall rules to graph nodes is basic and might need refinement based on more complex scenarios.
        - Rendering: It uses dot.render() to save the graph to the specified output_path (defaulting to network_flow.png). view=False prevents it from automatically opening, and cleanup=True removes the intermediate DOT source file.
        - Error Handling: It includes a try...except block to catch potential errors during graph generation, especially if Graphviz is not installed or in the system's PATH.
    ### Example Usage: 
        - The if __name__ == '__main__': block now includes a call to generate_graphical_flow_diagram with the example data.
4. # aws_config_generator.py
    ### generate_aws_cloudformation(yaml_data): 
        - This function takes the parsed YAML data and starts building an AWS CloudFormation template as a Python dictionary.
    ### VPC: 
        - It creates a basic VPC resource using the ip_address_space and name from the YAML.
    ### Subnets: 
        - It iterates through the subnets defined in the YAML and creates an AWS::EC2::Subnet resource for each, associating them with the VPC and assigning a basic Availability Zone. It also makes a basic assumption that subnets named "frontend" should have public IP auto-assignment.
    ### Internet Gateway: 
        - It creates an Internet Gateway and attaches it to the VPC if any subnet is marked as "frontend" (a basic assumption for public access).
    ### Load Balancer: 
        - If load_balancer.enabled is true, it creates a basic Application Load Balancer, a security group for it (allowing traffic on the specified listener ports), a listener (currently very basic, assuming forwarding to a target group), and a target group.
    ### Security Groups: 
        - It creates a basic security group for the application instances, allowing all outbound traffic.
    ### Firewall Rules to Security Group Ingress: 
        - It iterates through the firewall.rules in the YAML and translates them into SecurityGroupIngress rules for the application security group. It attempts to match the destination subnet name to the AWS subnet resource names.
    ### Return Template: 
        - The function returns the complete AWS CloudFormation template as a Python dictionary.
    ## Example Usage: The if __name__ == '__main__': 
        - block demonstrates how to use the function with an example yaml_data and prints the resulting CloudFormation template as a JSON string.
5. # azure_config_generator.py
    ### generate_azure_arm_template(yaml_data): 
        - This function takes the parsed YAML data and constructs an Azure ARM template as a Python dictionary.
    ### Basic Structure: 
        - It sets up the basic ARM template schema, content version, and placeholders for parameters, variables, resources, and outputs.
    ### Virtual Network: 
        - It creates an Azure Virtual Network resource using the name and ip_address_space from the YAML.
    ### Subnets: 
        - It iterates through the subnets and adds them to the Virtual Network's properties.
    ### Public IP and Load Balancer: 
        - If a load balancer is enabled in the YAML, it creates a Public IP Address and an Azure Load Balancer resource. It also sets up basic load balancing rules based on the listeners defined in the YAML.
    ### Network Security Group (NSG): 
        - It creates a Network Security Group to control inbound and outbound traffic.
    ### Security Rules: 
        - It translates the firewall.rules from the YAML into Azure Network Security Group rules. It maps the source to sourceAddressPrefix and destination to destinationAddressPrefix. Note: More sophisticated mapping of the destination to specific network interfaces or IP configurations might be needed in more complex scenarios.
    ### Subnet Association with NSG: 
        - It associates the created Network Security Group with each of the subnets.
    ### Return Template: 
        - The function returns the complete Azure ARM template as a Python dictionary.
    ### Example Usage: The if __name__ == '__main__': 
        - block demonstrates how to use the function with an example yaml_data and prints the resulting ARM template as a JSON string.
6. # gcp_config_generator.py
    ### generate_gcp_config(yaml_data): 
        - This function takes the parsed YAML data and constructs a Python dictionary representing the GCP network configuration.
    ### Network: 
        - It creates a basic GCP network with autoCreateSubnetworks set to False as we are defining them explicitly.
    ### Subnetworks: 
        - It iterates through the subnets and creates corresponding GCP subnetwork configurations, associating them with the network and region.
    ### Firewall Rules: 
        - It translates the firewall.rules into GCP firewall rules. It performs a basic mapping of the source and destination based on the subnet names. Note: This mapping is rudimentary and might need more sophisticated logic based on network tags or IP ranges in real-world scenarios.
    ### Load Balancer (Basic HTTP): 
        - It includes a basic configuration for an external HTTP load balancer if enabled. It creates a forwarding rule, a backend service, and a health check. HTTPS listeners are currently not fully implemented in this basic example.
    ### Project ID and Region: 
        - Remember to replace "your-gcp-project-id" with your actual GCP project ID. The region defaults to us-central1 but can be overridden in the YAML.
    ### Output Format: 
        - The function returns a Python dictionary, which can be easily serialized into YAML or JSON for use with GCP tools.