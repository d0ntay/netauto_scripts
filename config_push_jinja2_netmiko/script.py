import yaml
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler

with open("devices.yaml", "r") as f:
    device_data = yaml.safe_load(f)

with open("vars.yaml", "r") as f:
    interface_data = yaml.safe_load(f)


env = Environment(
    loader=FileSystemLoader('.'),
    trim_blocks=True,
    lstrip_blocks=True,
)

template = env.get_template('config.j2')

for device in device_data['devices']:
    rendered = template.render(
        device=device,
        interfaces=interface_data['interfaces'],
    )
    config_lines = rendered.strip().splitlines()
    conn = ConnectHandler(
        device_type=device['device_type'],
        host=device['host'],
        username=device['username'],
        password=device['password'],
    )
    conn.enable()
    output = conn.send_config_set(config_lines)

    conn.set_base_prompt()

    conn.save_config()
    conn.disconnect()
    print(f"Finished {device['name']}")