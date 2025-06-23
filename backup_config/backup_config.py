import datetime
from netmiko import ConnectHandler
import yaml
import getpass

def net_connect(data, username, password):
    good = 0
    bad = 0
    for device in data["devices"]:
        try:
            conn = ConnectHandler(
                device_type = device["device_type"],
                host = device["host"],
                username = username,
                password = password,
            )
            if device["device_type"] == "juniper":
                juniper_device(conn, conn.host)
            elif device["device_type"] == "cisco_ios":
                cisco_device(conn, conn.host)
                
            good += 1
            print(f"{conn.host} | Done!")
        except Exception:
            bad += 1
            print(f"{device.get('host')} | Failed!")

    report(good, bad)
    
def report(good, bad):
    print("Backup Complete")
    print("---------------")
    print(f"Successful backups - {good}")
    print(f"Failed backups - {bad}")

def juniper_device(conn, host):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"backups/{host}_{timestamp}.txt"
    output = conn.send_command("show configuration")
    with open(filename,"w") as file:
        file.write(output)
    conn.disconnect()

def cisco_device(conn, host):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"backups/{host}_{timestamp}.txt"
    output = conn.send_command("show run")
    with open(filename,"w") as file:
        file.write(output)
    conn.disconnect()

if __name__ == "__main__":
    username = input("Enter Username: ")
    password = getpass.getpass()
    with open("./inventory/devices.yaml", "r") as f:
        data = yaml.safe_load(f)
        net_connect(data, username, password)
