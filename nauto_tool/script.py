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

def juniper_device(device_name ,conn, config_lines):
    pre_conf = conn.send_command("show configuration")
    output = conn.send_config_set(config_lines)
    conn.commit()
    conn.exit_config_mode()
    post_conf = conn.send_command("show configuration")
    conn.disconnect()
    OUTPUTS[device_name] = {
        "original_config" : pre_conf,
        "new_config" : post_conf,
        "output" : output,
    }
    print(f"Finished {device_name}")

def cisco_device(device_name, conn, config_lines):
    conn.enable()
    pre_conf = conn.send_command("show run")
    output = conn.send_config_set(config_lines)
    conn.set_base_prompt()
    conn.save_config()
    post_conf = conn.send_command("show run")
    conn.disconnect()
    OUTPUTS[device_name] = {
        "original_config" : pre_conf,
        "new_config" : post_conf,
        "output" : output,       
    }
    print(f"Finished {device_name}")

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
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"./output/output-{timestamp}.txt"
    with open(filename, "w") as f:
        yaml.dump(OUTPUTS, f)

if __name__ == "__main__":
    main()