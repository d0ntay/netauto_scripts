from datetime import datetime
import yaml
from netmiko import ConnectHandler
import getpass
from concurrent.futures import ThreadPoolExecutor, as_completed

USERNAME = input("Username: ")
PASSWORD = getpass.getpass()

OUTPUTS = {}

def net_connect (device):
        try:
            conn = ConnectHandler(
                device_type = device["device_type"],
                host = device["host"],
                username = USERNAME,
                password = PASSWORD,
            )
            if device["device_type"] == "juniper":
                juniper_device(conn, conn.host)
            elif device["device_type"] == "cisco_ios":
                cisco_device(conn, conn.host)
        except Exception:
            print(f'{device["host"]} - Failed')


def juniper_device(conn, host):
    output = conn.send_command("show version | match JUNOS")
    generate_output(output, host)
    conn.disconnect()
    print(f"{host} - Done!")

def cisco_device(conn, host):
    output = conn.send_command("show version | include Version")
    generate_output(output, host)
    conn.disconnect()
    print(f"{host} - Done!")

def generate_output(output, host):
    final_output = output.strip().splitlines()[0]
    OUTPUTS[host] = {
        "output": final_output,
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
        for device in data["devices"]:
            futures.append(executor.submit(net_connect, device))
        for future in as_completed(futures):
            future.result()
    create_output()

if __name__ == "__main__":
    main()