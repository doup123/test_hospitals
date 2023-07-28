**Hospital Network Testing Tool - README**  

This repository contains a Python script that performs network tests on hospital network devices using Nornir, Netmiko, Napalm, and Jinja2 libraries. The script reads hospital information from a downloaded XLSZ file, creates Hospital objects based on the data, and then executes various network tests.

**Prerequisites**

You can install the required packages using pip (tested on python3.8.10):  
pip3 install -r requirements.txt

**Usage**

To use the hospital network testing tool, follow these steps:

1. Clone this repository to your local machine.

1. Update the "group.yaml" file with your device connection details (username) or provide username and password through the prompt. If you have a key that has access to the devices the password can be ignored.

**Script Overview**

The main script, "hospitals_check.py" is the entry point for running the network tests. It uses the Nornir library to execute tasks on network devices and the Pandas library to read hospital information from the downloaded XLSX file.

**Hospital Class**

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

    create_hospital_object_from_xlsx(xls_file, tag=None): A function to read hospital information from an excel file and create Hospital objects based on the data.

**Network Tests**

The script performs the following network tests on each hospital (or a specific hospital, if a tag is provided):

    Physical Port Connectivity Test: Checks if the specified physical interface is UP or DOWN.

    Optical Levels Test: Retrieves optical level information for the specified interface.

    ICMP Ping Test: Pings the PtP1 (eier) IP address and checks for successful connectivity.

    BGP Neighbor Test: Checks the BGP status with the PtP1 (eier) address, received and sent prefixes.

Please note that the script uses the hospital's specific configuration details to perform the tests.

**Example output** 

(nornir-venv) ➜  hospitals_check git:(main) ✗ python3 hospitals_check.py --hospital_tag BENAK
    
    Downloading recent HOSPITALS file from sharepoint
    File downloaded successfully.
    Enter your new username: mdimolianis
    Enter your new password:
    BENAK
    ----------Physical-connectivity----------
    Physical interface xe-0/0/3 of eie2-asw.grnet.gr is UP
    ----------Optical-levels----------
    {'physical_channels': {'channel': [{'index': 0, 'state': {'input_power': {'instant': -12.15, 'avg': 0.0, 'max': 0.0, 'min': 0.0}, 'output_power': {'instant': -2.06, 'avg': 0.0, 'max': 0.0, 'min': 0.0}, 'laser_bias_current': {'instant': 30.782, 'avg': 0.0, 'max': 0.0, 'min': 0.0}}}]}}
    ----------PING----------
    Ping to p2p 62.217.77.173 OK
    ----------BGP----------
    BGP with 62.217.77.173 is up
    We receive IP prefix
    We announce IP prefix