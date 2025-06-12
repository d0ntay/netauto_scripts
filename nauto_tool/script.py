import yaml
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler
import getpass
import sys
from datetime import datetime

# only supports one account so make sure all devices have this user on them

USERNAME = input("Username: ")
PASSWORD = getpass.getpass()

# update template map with more tempplates when a new vendor is needed
#
# Currently supported vendors:
#   Cisco
#   Juniper

TEMPLATE_MAP = {
    "juniper": "juniper_config.j2",
    "cisco_ios": "cisco_config.j2",
}

OUTPUTS = {}

# logic for loading environment and templates (jinja stuff)

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
            net_connect(
                config_lines,
                device_type = device["device_type"],
                device_host = device["host"],
                device_name = device["name"],
                device_username = USERNAME,
                device_password = PASSWORD,
            )           
                    
        except Exception as e:
            print(f"Error on {device["name"]} | {device["host"]} : {e}")

# Command runner for juniper

def juniper_device(device_name ,conn, config_lines):
    pre_conf = conn.send_command("show configuration")
    output = conn.send_config_set(config_lines)
    conn.commit()
    conn.exit_config_mode()
    post_conf = conn.send_command("show configuration")
    conn.disconnect()
    generate_output(device_name, pre_conf, post_conf, output)
    print(f"Finished {device_name}")

# Command runner for cisco

def cisco_device(device_name, conn, config_lines): 
    conn.enable()
    pre_conf = conn.send_command("show run")
    output = conn.send_config_set(config_lines)
    conn.set_base_prompt()
    conn.save_config()
    post_conf = conn.send_command("show run")
    conn.disconnect()
    generate_output(device_name, pre_conf, post_conf, output)
    print(f"Finished {device_name}")

# Appends OUTPUTS map with data received from each device

def generate_output(device_name, pre_conf, post_conf, output):
    OUTPUTS[device_name] = {
        "original_config" : pre_conf,
        "new_config" : post_conf,
        "output" : output,       
    }

# Creates the output file with the contents of the OUTPUTS map

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

# Netmiko logic for ssh connection to device

def net_connect(config_lines, device_type, device_host, device_name, device_username, device_password):
    conn = ConnectHandler(
        device_type = device_type,
        host = device_host,
        username = device_username,
        password = device_password,
    )
    if device_type == "juniper":
        juniper_device(device_name, conn, config_lines)
    elif device_type == "cisco_ios":
        cisco_device(device_name, conn, config_lines)

# Dry run feature for testing output of config before running on a live device. 
#
# need to use --dry_run argument 
#
# example of how to use...    python script.py --dry_run

def dry_run(data):
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
            for line in config_lines:
                print(f"{device["name"]} # {line}")
        except Exception as e:
            print(e)
    sys.exit()

def main():
    with open("./inventory/devices.yaml", "r") as f:
        data = yaml.safe_load(f)
    if len(sys.argv) > 1:
        if sys.argv[1] == "--dry_run":
            dry_run(data)
    loader(data)
    create_output()

if __name__ == "__main__":
    main()