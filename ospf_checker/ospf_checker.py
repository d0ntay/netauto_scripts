from datetime import datetime
import yaml
from netmiko import ConnectHandler
import getpass
from concurrent.futures import ThreadPoolExecutor, as_completed

USERNAME = input("Username: ")
PASSWORD = getpass.getpass()
DEVICE_MAP = {
    "Cisco": "cisco_ios",
    "Juniper Networks, Inc.": "juniper_junos"
}
OUTPUTS = {}

def net_connect (device):
        name = device["DisplayName"]
        try:
            conn = ConnectHandler(
                device_type=DEVICE_MAP.get(device["Vendor"]),
                host = device["IPAddress"],
                username = USERNAME,
                password = PASSWORD,
            )
            if device["Vendor"] == "Juniper Networks, Inc.":
                juniper_device(conn, conn.host, name)
            elif device["Vendor"] == "Cisco":
                cisco_device(conn, conn.host, name)
        except Exception:
            print(f'{name} | {device["IPAddress"]} - Failed')


def juniper_device(conn, host, name):
    output = conn.send_command("show ospf neighbor")
    generate_output(output, host)
    conn.disconnect()
    print(f"{name} | {host} - Done!")

def cisco_device(conn, host, name):
    output = conn.send_command("show ip ospf neighbor")
    generate_output(output, host)
    conn.disconnect()
    print(f"{name} | {host} - Done!")

def generate_output(output, host):
    OUTPUTS[host] = {
        "output": output,
    }

def create_output():
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"./output/output-{timestamp}.txt"
    with open(filename, "w") as f:
        for device, output in OUTPUTS.items():
            f.write(f"{device}:\n")
            for section, content in output.items():
                f.write(f"  {section}:\n")
                for line in content.strip().splitlines():
                    f.write(f"    {line}\n")
            f.write("\n")
            
def main():
    with open("./inventory/devices.yaml", "r") as f:
        data = yaml.safe_load(f)
    futures = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        for device in data:
            futures.append(executor.submit(net_connect, device))
        for future in as_completed(futures):
            future.result()
    create_output()

if __name__ == "__main__":
    main()