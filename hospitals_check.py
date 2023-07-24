from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_netmiko import netmiko_send_command
from nornir_napalm.plugins.tasks import napalm_get,napalm_configure,napalm_ping
from jinja2 import Environment, FileSystemLoader
import pandas as pd
import argparse
import ipaddress

separator="----------"
def main():
    #Initialize nornir configuration files -> groups,hosts etc
    args = args_parser()
    #hospital = create_hospital_object_from_csv("HOSPITALS.csv","BENAK")
    hospital = create_hospital_object_from_csv("HOSPITALS.csv",args.hospital_tag)

    #Here we define the logic of the tests:
    print(hospital.tag)
    if (hospital.check_physical_port()):
        print(hospital.check_diagnostics_optics())
        if (hospital.check_ping()):
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
        self.iprouter1 = "eier.grnet.gr"
        self.iprouter2 = "kolettir.grnet.gr"
        self.nr =InitNornir(config_file="config.yaml")
        self.routing_instance ="hospitals-1050"

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
        return (optics[self.access_interface])
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
        get_attributes = self.nr.run(task=nornir_napalm_getter, getter=getter)
        attributes_result = get_attributes[device_name][1].result[getter]
        return attributes_result

def create_hospital_object_from_csv(csv_file, tag=None):
    df = pd.read_csv(csv_file, delimiter=';')

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
                            lir_prefix=row['LIR Prefix'].iloc[0].strip(),
                            ptp1=row['PtP1 (eier)'].iloc[0].strip(),
                            ptp2=row['PtP2 (kolettir)'].iloc[0].strip())
        else:
            raise ValueError(f"No Hospital object found with tag '{tag}' in the CSV file.")

    # If no tag is provided, create and return a list of all Hospital objects
    hospitals = []
    for index, row in df.iterrows():
        hospital = Hospital(tag=row['TAG'].strip(),
                            access=row['Carrier/Switch'].strip(),
                            carrier=row['L3_Termination_Point'].strip(),
                            access_interface=row['Interface'].strip(),
                            vlan=int(row['Vlans']),
                            asn=int(row['ASN']),
                            lir_prefix=row['LIR Prefix'].strip(),
                            ptp1=row['PtP1 (eier)'].strip(),
                            ptp2=row['PtP2 (kolettir)'].strip())
        hospitals.append(hospital)

    return hospitals

if __name__ == "__main__":
    main()
