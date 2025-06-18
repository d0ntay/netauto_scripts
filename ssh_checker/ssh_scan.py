from netmiko import ConnectHandler
import getpass

def check_ssh(ip, username, password):
    try:
        ConnectHandler(
            device_type= "autodetect",
            host=ip,
            username=username,
            password=password,
        )
        return True
    except Exception:
        return False 

if __name__ == "__main__":
    devices = [
        "10.249.0.1",
        "10.249.0.20",
        "10.248.1.1",
        "172.17.74.3",
        "172.17.74.5",
        "192.168.60.3",
        "192.168.60.4",
        "10.250.4.1",
        "10.250.4.36",
        "10.246.0.1",
        "10.246.10.5",
        "172.17.74.11",
    ]

    username = "dcicciarelli"
    password = getpass.getpass()
    for ip in devices:
        if check_ssh(ip, username, password):
            print(f"{ip} : yes")
        else:
            print(f"{ip} : no")