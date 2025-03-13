import os
import sys
import ctypes
import tkinter as tk
from tkinter import scrolledtext
import subprocess
import psutil
import time
import ftplib

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    # Re-run the program with admin rights
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, __file__, None, 1
        )
        sys.exit(0)
    except Exception as e:
        print(f"Failed to request administrator privileges: {e}")
        time.sleep(5)
        sys.exit(1)

# Rest of your program starts here
ROBOT_CONFIGS = {
    "Test": {"ip": "192.168.103.101", "subnet": "255.255.255.0", "gateway": "192.168.103.1", "target": "192.168.103.6","ftp_user": "NORD","ftp_pass": "nordadmin"},
    "PL-US OTTO1500": {"ip": "10.252.252.2", "subnet": "255.255.255.0", "gateway": "10.252.252.1", "target": "10.252.252.10","ftp_user": "NORD","ftp_pass": "nordadmin"},
    "Robot 3": {"ip": "192.168.3.101", "subnet": "255.255.255.0", "gateway": "192.168.3.1", "target": "192.168.3.200","ftp_user": "NORD","ftp_pass": "nordadmin"},
    "Robot 4": {"ip": "192.168.4.101", "subnet": "255.255.255.0", "gateway": "192.168.4.1", "target": "192.168.4.200","ftp_user": "NORD","ftp_pass": "nordadmin"},
    "Robot 5": {"ip": "192.168.5.101", "subnet": "255.255.255.0", "gateway": "192.168.5.1", "target": "192.168.5.200","ftp_user": "NORD","ftp_pass": "nordadmin"},
    "Robot 6": {"ip": "192.168.3.101", "subnet": "255.255.255.0", "gateway": "192.168.3.1", "target": "192.168.3.200","ftp_user": "NORD","ftp_pass": "nordadmin"},
    "Robot 7": {"ip": "192.168.4.101", "subnet": "255.255.255.0", "gateway": "192.168.4.1", "target": "192.168.4.200","ftp_user": "NORD","ftp_pass": "nordadmin"},
    "Robot 8": {"ip": "192.168.5.101", "subnet": "255.255.255.0", "gateway": "192.168.5.1", "target": "192.168.5.200","ftp_user": "NORD","ftp_pass": "nordadmin"},
}

NETWORK_INTERFACE = "Ethernet"

# Function to update indicator labels
def update_indicator(label, condition):
    if condition:
        label.config(bg="green")
    else:
        label.config(bg="red")

# Function to configure network settings and ping
def test_robot(robot_name):
    config = ROBOT_CONFIGS[robot_name]
    ip = config["ip"]
    subnet = config["subnet"]
    gateway = config["gateway"]
    target = config["target"]

    output_text.delete('1.0',tk.END)

    output_text.insert(tk.END, f"\nTesting {robot_name}...\n")
    output_text.insert(tk.END, f"Configuring Network: IP={ip}, Subnet={subnet}, Gateway={gateway}\n")

    try:
        result = subprocess.run(
            ["netsh", "interface", "ip", "set", "address", NETWORK_INTERFACE, "static", ip, subnet, gateway],
            capture_output=True,
            text=True,
            check=True,
        )
        output_text.insert(tk.END, f"Network configured successfully for {NETWORK_INTERFACE}\n")
    except subprocess.CalledProcessError as e:
        output_text.insert(tk.END, f"Error configuring network: {e.stderr}\n")
        return

    # Ping the target
    try:
        result = subprocess.run(
            ["ping", "-n", "4", target], capture_output=True, text=True
        )
        output_text.insert(tk.END, f"Ping Results:\n{result.stdout}\n")
        ping_time = float(result.stdout.split("Average = ")[1].split("ms")[0])
    except Exception as e:
        output_text.insert(tk.END, f"Error running ping: {e}\n")
        return

    # Display network stats
    try:
        network_stats = psutil.net_if_stats()
        for iface, stats in network_stats.items():
            if iface == NETWORK_INTERFACE:
                is_up = stats.isup
                speed = stats.speed
                duplex = stats.duplex

                output_text.insert(tk.END, f"Interface: {iface}, Duplex: {duplex}, Speed: {speed}Mbps, Is Up: {is_up}\n")

                # Update indicators based on success criteria
                update_indicator(duplex_label, duplex == psutil.NIC_DUPLEX_FULL)
                update_indicator(speed_label, speed >= 100)
                update_indicator(is_up_label, is_up)
                update_indicator(ping_label, ping_time < 20)
                
        # If ping was successful, try FTP
        if ping_time < 20:
            output_text.insert(tk.END, "Checking FTP access...\n")
            ftp_success = check_ftp_access(
                target, 
                config["ftp_user"], 
                config["ftp_pass"]
            )
            if ftp_success:
                output_text.insert(tk.END, "FTP access successful\n")
            else:
                output_text.insert(tk.END, "FTP access failed\n")
            
            update_indicator(ftp_label, ftp_success)
        else:
            update_indicator(ftp_label, False)
            
    except Exception as e:
        output_text.insert(tk.END, f"Error in network test: {e}\n")
        update_indicator(ftp_label, False)

def check_ftp_access(ip, username, password):
    try:
        output_text.insert(tk.END, f"\nTrying FTP connection to {ip}...\n")
        ftp = ftplib.FTP(ip)
        
        # Try login and capture welcome message
        welcome = ftp.getwelcome()
        output_text.insert(tk.END, f"FTP Welcome: {welcome}\n")
        
        try:
            ftp.login(username, password)
            output_text.insert(tk.END, f"Login successful with user: {username}\n")
        except ftplib.error_perm as login_error:
            output_text.insert(tk.END, f"Login failed: {str(login_error)}\n")
            return False
        
        # List root directory contents
        root_contents = ftp.nlst()
        output_text.insert(tk.END, f"Root directory contains: {', '.join(root_contents)}\n")
        
        # Try to change to the target directory
        try:
            ftp.cwd("/MEMCARD1/html")
            output_text.insert(tk.END, "Successfully accessed /MEMCARD1/html/\n")
            
            # List directory contents
            html_contents = ftp.nlst()
            output_text.insert(tk.END, f"Directory contents: {', '.join(html_contents)}\n")
            
            file_exists = "page1.htm" in html_contents
            if file_exists:
                output_text.insert(tk.END, "Found page1.htm\n")
            else:
                output_text.insert(tk.END, "page1.htm not found in directory\n")
                
        except ftplib.error_perm as dir_error:
            output_text.insert(tk.END, f"Directory access error: {str(dir_error)}\n")
            ftp.quit()
            return False
            
        ftp.quit()
        return True if file_exists else False
        
    except Exception as e:
        output_text.insert(tk.END, f"FTP connection error: {str(e)}\n")
        return False

# Create main window
root = tk.Tk()
root.title("Robot Network Tester")

# Add buttons for each robot
frame = tk.Frame(root)
frame.pack(pady=10)

for robot_name in ROBOT_CONFIGS.keys():
    btn = tk.Button(
        frame, 
        text=robot_name, 
        command=lambda r=robot_name: test_robot(r),
        width=20,  # Increased button size for touchscreen
        height=2   # Increased button height for touchscreen
    )
    btn.pack(side=tk.LEFT, padx=10, pady=10)

# Add a scrolled text widget to display output
output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20)
output_text.pack(pady=10)

# Add indicator labels
indicator_frame = tk.Frame(root)
indicator_frame.pack(pady=10)

duplex_label = tk.Label(indicator_frame, text="Duplex", bg="yellow", width=15)
duplex_label.grid(row=0, column=0, padx=5)

speed_label = tk.Label(indicator_frame, text="Speed", bg="yellow", width=15)
speed_label.grid(row=0, column=1, padx=5)

is_up_label = tk.Label(indicator_frame, text="Is Up", bg="yellow", width=15)
is_up_label.grid(row=0, column=2, padx=5)

ping_label = tk.Label(indicator_frame, text="Ping Time", bg="yellow", width=15)
ping_label.grid(row=0, column=3, padx=5)

ftp_label = tk.Label(indicator_frame, text="FTP Access", bg="yellow", width=15)
ftp_label.grid(row=0, column=4, padx=5)

# Run the Tkinter event loop
root.mainloop()
