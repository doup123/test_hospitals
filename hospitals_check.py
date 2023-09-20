from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_netmiko import netmiko_send_command
from nornir_napalm.plugins.tasks import napalm_get,napalm_configure,napalm_ping
from jinja2 import Environment, FileSystemLoader
import pandas as pd
import argparse
import ipaddress
from download_hospitals_info import download_file
from getpass import getpass
import yaml


separator="----------"
def main():
    #Initialize nornir configuration files -> groups,hosts etc
    args = args_parser()
    print("Downloading recent HOSPITALS file from sharepoint")
    url = "https://grnethq-my.sharepoint.com/:x:/g/personal/alioumis_noc_grnet_gr/EatRBpIG2uhCm-ucBJKarqoBJm1V4FyLDzj1BPFB2xSzXA?download=1"
    output_file = "HOSPITALS.xlsx"
    download_file(url, output_file)
    hospital = create_hospital_object_from_xlsx(output_file,args.hospital_tag)

    # Get the new credentials from the user
    new_username, new_password = get_credentials()
    hospital.username = new_username
    hospital.password = new_password
    # Here we define the logic of the tests:
    print(hospital.tag)
    #L2 connectivity

    if (hospital.check_physical_port()):
        #Optical levels
        print(hospital.check_diagnostics_optics())
        #L3 connectivity
        if (hospital.check_ping()):
            #BGP
            hospital.check_bgp_neighbors()

def nornir_napalm_getter(task,getter):
    result = task.run(task=napalm_get, getters=[getter])

def args_parser():
    parser = argparse.ArgumentParser(description='hospitals check')
    parser.add_argument('--hospital_tag', help='hospital tag')
    args = parser.parse_args()
    return(args)


class Hospital():
    def __init__(self, tag, access,carrier, access_interface, vlan, asn, lir_prefix, ptp1, ptp2):
        self.tag = tag
        self.access = access
        self.carrier = carrier
        self.access_interface = access_interface
        self.vlan = vlan
        self.asn = asn
        self.lir_prefix = lir_prefix
        self.ptp1 = ptp1
        self.ptp2 = ptp2
        self.nr =InitNornir(config_file="config.yaml")
        self.routing_instance ="hospitals-1050"
        self.username=''
        self.password=''

        if self.access=="0" or self.carrier=="0" or self.access_interface=="0":
            exit("Problem with the values of the HOSPITAL "+self.tag+" in the source file")
        # Validate PTP1 (IPv4 address or network)
        try:
            ptp1_net = ipaddress.IPv4Network(ptp1)
            self.ptp1 = ptp1_net
        except ipaddress.AddressValueError:
            raise ValueError("Invalid PTP1 address. Please provide a valid IPv4 address or network.")

        # Validate PTP2 (IPv4 address or network)
        # try:
        #     ptp2_net = ipaddress.IPv4Network(ptp2)
        #     self.ptp2 = ptp2_net
        # except ipaddress.AddressValueError:
        #     raise ValueError("Invalid PTP2 address. Please provide a valid IPv4 address or network.")

        # Validate lir_prefix (IPv4 address or network)
        try:
            lir_prefix_net = ipaddress.IPv4Network(lir_prefix)
            self.lir_prefix = lir_prefix_net
        except ipaddress.AddressValueError:
            raise ValueError("Invalid PTP2 address. Please provide a valid IPv4 address or network.")

        self.ptp1_grnet = str(self.ptp1.network_address)
        self.ptp1_hospital =str (self.ptp1.broadcast_address)

    def check_physical_port(self):
        ports = self.retrieve_results_from_nornir("get_interfaces",self.access)
        physical_interface = ports[self.access_interface]
        print(separator+"Physical-connectivity"+separator)
        if physical_interface["is_up"]:
            print("Physical interface "+str(self.access_interface)+" of "+self.access+" is UP")
            return(True)
        else:
            print("Physical interface "+str(self.access_interface)+" of "+self.access+" is DOWN")
            return(False)
    def check_diagnostics_optics(self):
        print(separator+"Optical-levels"+separator)
        optics = self.retrieve_results_from_nornir("get_optics",self.access)
        if self.access_interface in optics.keys():
            return (optics[self.access_interface])
        else:
            return("No optics available")
    def check_ping(self):
        pass
    def check_l3_interface(self):
        ip_intf = self.retrieve_results_from_nornir("get_interfaces_ip", self.carrier)
        return (ip_intf)

    def check_asn(self):
        pass

    def check_ping(self):
        self.nr = InitNornir(config_file="config.yaml")
        self.nr = self.nr.filter(hostname=self.carrier)
        self.update_passwords()
        res = self.nr.run(task=napalm_ping, dest=self.ptp1_hospital)
        print(separator+"PING"+separator)
        if(res[self.carrier][0].result["success"]):
            print("Ping to p2p "+self.ptp1_hospital+" OK")
            return(True)
        else:
            print("Ping to p2p " + self.ptp1_hospital + " PROBLEM")
            return (False)

    def check_bgp_neighbors(self):
        bgp_neighbors = self.retrieve_results_from_nornir("get_bgp_neighbors", self.carrier)
        bgp_details = bgp_neighbors[self.routing_instance]['peers'][self.ptp1_hospital]
        print(separator+"BGP"+separator)
        if bgp_details["is_up"]:
            print("BGP with "+self.ptp1_hospital+" is up")
        else:
            print("BGP with "+self.ptp1_hospital+" is down")
            return

        received_prefixes = bgp_details["address_family"]["ipv4"]["received_prefixes"]
        sent_prefixes = bgp_details["address_family"]["ipv4"]["sent_prefixes"]
        if received_prefixes>0:
            print("We receive IP prefix")
        else:
            print("We do not receive any IP prefix and we should")

        if sent_prefixes>0:
            print("We announce IP prefix")
        else:
            print("We do not announce any IP prefix and we should")
        return(bgp_details)


    def retrieve_results_from_nornir(self,getter,device_name):
        self.nr = InitNornir(config_file="config.yaml")
        self.nr = self.nr.filter(hostname=device_name)
        self.update_passwords()
        get_attributes = self.nr.run(task=nornir_napalm_getter, getter=getter)
        attributes_result = get_attributes[device_name][1].result[getter]
        return attributes_result

    def update_passwords(self):
        for hostname, host_obj in self.nr.inventory.hosts.items():
            host_obj.username = self.username
            host_obj.password = self.password
def create_hospital_object_from_xlsx(xls_file, tag=None):
    df = pd.read_excel(xls_file, sheet_name="Hospitals_Auto_Checks")

    # If a specific tag is provided, create and return a single Hospital object
    if tag is not None:
        row = df[df['TAG'].str.strip() == tag.strip()]
        if not row.empty:
            return Hospital(tag=row['TAG'].iloc[0].strip(),
                            access=row['Carrier/Switch'].iloc[0].strip(),
                            carrier=row['L3_Termination_Point'].iloc[0].strip(),
                            access_interface=row['Interface'].iloc[0].strip(),
                            vlan=int(row['Vlans'].iloc[0]),
                            asn=int(row['ASN'].iloc[0]),
                            lir_prefix=str(row['LIR Prefix'].iloc[0]).strip(),
                            ptp1=str(row['PtP1 (eier)'].iloc[0]).strip(),
                            ptp2=str(row['PtP2 (kolettir)'].iloc[0]).strip())
        else:
            raise ValueError(f"No Hospital object found with tag '{tag}' in the xlsx file.")


def get_credentials():
    username = input("Enter your new username: ")
    password = getpass("Enter your new password: ")
    return username, password

if __name__ == "__main__":
    main()
