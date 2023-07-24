**Hospital Network Testing Tool - README**  

This repository contains a Python script that performs network tests on hospital network devices using Nornir, Netmiko, Napalm, and Jinja2 libraries. The script reads hospital information from a CSV file, creates Hospital objects based on the data, and then executes various network tests.
Prerequisites

You can install the required packages using pip:  
pip3 install -r requirements.txt

**Usage**

To use the hospital network testing tool, follow these steps:

1. Clone this repository to your local machine.

1. Ensure you have a CSV file containing hospital information, including tags, access, carrier, access interface, VLAN, ASN, LIR prefix, PtP1, and PtP2. The CSV file should be formatted with the delimiter ';' and have a header row with the column names. An example CSV file named "HOSPITALS.csv" is provided in the repository. 
1.The CSV file should be created by the last sheet of excel file: https://grnethq-my.sharepoint.com/:x:/g/personal/alioumis_noc_grnet_gr/EatRBpIG2uhCm-ucBJKarqoBJm1V4FyLDzj1BPFB2xSzXA?e=9CU99w. 
1. Update the "group.yaml" file with your device connection details (username).
1. Open a terminal or command prompt, navigate to the repository's directory, and run the Python script "hospital_testing_tool.py" with the appropriate arguments:  
  python hospital_testing_tool.py --hospital_tag <hospital_tag> e.g. python hospital_testing_tool.py --hospital_tag BENAK


**Script Overview**

The main script, "hospitals_check.py" is the entry point for running the network tests. It uses the Nornir library to execute tasks on network devices and the Pandas library to read hospital information from the CSV file.
Hospital Class

The "Hospital" class represents a hospital with various attributes such as tag, access, carrier, access interface, VLAN, ASN, LIR prefix, PtP1, and PtP2. It provides methods to perform different network tests on the hospital's network devices, including:

    Checking physical port connectivity
    Checking optical levels (diagnostics)
    Checking L3 interface information
    Checking BGP neighbors
    Checking ICMP ping connectivity

**Functions**

The script also contains several functions:

    main(): The main function of the script. It initializes Nornir, reads hospital information from the CSV file, and performs network tests based on the provided hospital tag (if any).

    nornir_napalm_getter(task, getter): A helper function to execute Nornir Napalm tasks.

    args_parser(): A function to parse command-line arguments using the argparse library.

    create_hospital_object_from_csv(csv_file, tag=None): A function to read hospital information from the CSV file and create Hospital objects based on the data.

**Network Tests**

The script performs the following network tests on each hospital (or a specific hospital, if a tag is provided):

    Physical Port Connectivity Test: Checks if the specified physical interface is UP or DOWN.

    Optical Levels Test: Retrieves optical level information for the specified interface.

    ICMP Ping Test: Pings the PtP1 (eier) IP address and checks for successful connectivity.

    BGP Neighbor Test: Checks the BGP status with the PtP1 (eier) address, received and sent prefixes.

Please note that the script uses the hospital's specific configuration details (from the CSV file) to perform the tests.
