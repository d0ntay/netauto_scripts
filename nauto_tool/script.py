import json
import yaml
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler
import getpass
import sys
from datetime import datetime

USERNAME = input("Username: ")
PASSWORD = getpass.getpass()

TEMPLATE_MAP = {
    "juniper": "juniper_config.j2",
    "cisco_ios": "cisco_config.j2",
}

OUTPUTS = {}

def loader(data):
    env = Environment(
        loader=FileSystemLoader("./templates"),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    
    for device in data['devices']:
        try:
            if device["device_type"] not in TEMPLATE_MAP:
                print(f"Skipping {device["name"]}, device type not supported : {device["device_type"]}")
                continue
            template_name = TEMPLATE_MAP[device["device_type"]]
            template = env.get_template(template_name)
            rendered = template.render(device=device)
            config_lines = rendered.strip().splitlines()
            if len(sys.argv) > 1:
                if sys.argv[1] == "--dry_run":
                    dry_run(device['name'], config_lines)
                    continue

            conn = ConnectHandler(
                device_type = device["device_type"],
                host = device["host"],
                username = USERNAME,
                password = PASSWORD,
            )
            if device["device_type"] == "juniper":
                juniper_device(device, conn, config_lines)
            elif device["device_type"] == "cisco_ios":
                cisco_device(device, conn, config_lines)
        except Exception as e:
            print(f"Error on {device["name"]} | {device["host"]} : {e}")

def juniper_device(device ,conn, config_lines):
    output = conn.send_config_set(config_lines)
    conn.commit()
    conn.exit_config_mode()
    conn.disconnect()
    OUTPUTS[device['name']] = output
    print(f"Finished {device['name']}")

def cisco_device(device, conn, config_lines):
    conn.enable()
    output = conn.send_config_set(config_lines)
    conn.set_base_prompt()
    conn.save_config()
    conn.disconnect()
    OUTPUTS[device['name']] = output
    print(f"Finished {device['name']}")

def dry_run(device, config_lines):
    for line in config_lines:
        print(f"{device} - {line}")

def main():
    with open("./inventory/devices.yaml", "r") as f:
        data = yaml.safe_load(f)
    loader(data)
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"./output/output-{timestamp}.txt"
    with open(filename, "w") as f:
        json.dump(OUTPUTS, f, indent=2)

if __name__ == "__main__":
    main()