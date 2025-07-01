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
        
    ]

    username = "dcicciarelli"
    password = getpass.getpass()
    for ip in devices:
        if check_ssh(ip, username, password):
            print(f"{ip} : yes")
        else:
            print(f"{ip} : no")