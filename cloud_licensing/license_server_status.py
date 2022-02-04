import re
import time
import paramiko

import pprint
pp = pprint.PrettyPrinter(indent=2)

def process_ls_status(status):
    # status
    # IP Address: 10.180.109.190 (0050569c22cc) (dhcp)
    # Flex ID: No USB dongle found
    # UUID: 421C9FD5-687D-E5AA-0EFB-ED0C2BACF020

    # License Feature Name                          Total     In Use   Remaining
    # ------------------------------------------  ---------  --------  ---------
    # VIRTUAL_PORT_MINI                              1024       0         1024  
    # VIRTUAL_PORT_DCL_5G                            1024       0         1024  
    # VIRTUAL_TESTCENTER_FUNCTIONAL                  1024       0         1024  
    # VIRTUAL_TESTCENTER                             1024       0         1024  
    # VIRTUAL_PORT_CONTAINER                         1024       0         1024  
    # VIRTUAL_PORT_FNCT_1G                           1024       39        985   
    # VIRTUAL_PORT_PERF_50G                          1024       0         1024  
    # VIRTUAL_PORT_DCH_25G                           1024       0         1024  

    # admin>> 

    m = re.search("IP Address: (^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$) \((?:(0-9a-fA-F):?{12})\)", status)
    ls_ip = m.group(1)
    ls_mac = m.group(2)
    
    m = re.search("Flex ID: (.+)", status)
    ls_flex_id = m.group(1)

    m = re.search("UUID: (.+)", status)
    ls_uuid = m.group(1)

    # Build a dictionary with each of the features as a key.
    licenses = {}
    found_header = False
    for line in status.split("\n"):
        line = line.strip()
        if re.match("License Feature Name", line):
            found_header = True
            continue

        if found_header:
            if re.match("-------", line):
                # This the line that comes after the header.
                continue

            if line == "":
                # This means that there are no additional licenses.
                break

            feature_name = line.split()[0]
            total_licenses = line.split()[1]
            licenses_in_use = line.split()[2]            
            licenses_remaining = line.split()[3]            

            licenses[feature_name] = {}
            licenses[feature_name]["Total"] = total_licenses
            licenses[feature_name]["InUse"] = licenses_in_use
            licenses[feature_name]["Remaining"] = licenses_remaining

    return licenses


hostname = "license.cal.ci.spirentcom.com"
username = "admin"
password = "spt_admin"

ssh = paramiko.SSHClient()

#ssh.load_system_host_keys()

# add SSH host key automatically if needed.
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh.connect(hostname, username=username, password=password)
device_connection = ssh.invoke_shell()

# Flush the login status from the buffer. The sleep is important. 
# The login status will not be cleared properly if you do not wait.
time.sleep(1)
device_connection.recv(12000).decode("utf-8")   

# Issue the "status" command. You must specify the \n, or the command will not be sent.
device_connection.send("status\n")

# The sleep is very important. If you don't wait long enough, not all of the output will be captured.
time.sleep(1)

# Read the response and decode in to UTF-8 (ASCII) text.
response = device_connection.recv(12000).decode("utf-8")

licenses = process_ls_status(response)

pp.pprint(licenses)

ssh.close()
