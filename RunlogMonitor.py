import json
import os
import re
from datetime import datetime, timedelta

timeout_times_threshold = 5
timeout_ping_threshold = 100
dat_file_path = "./log_normal.dat"
output_file_path = "./output/monitorlog.dat"
config_file_path = "./monitor_config.json"


def read_log_file(file_path):
    log_entries = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                timestamp, ip, ping = line.strip().split(',')
                log_entries.append({
                    'timestamp': timestamp,
                    'ip': ip,
                    'ping': int(ping) if ping != '-' else None,
                })
    except Exception as e:
        print(f"Error reading log file: {e}")
    return log_entries


def read_config_file(config_path):
    global timeout_times_threshold, timeout_ping_threshold, dat_file_path, output_file_path, switch_to_check
    try:
        with open(config_path, 'r') as file:
            config = json.load(file)
            timeout_times_threshold = config["runtime_parameter"]["timeout_times_threshold"]
            timeout_ping_threshold = config["runtime_parameter"]["timeout_ping_threshold"]

            dat_file_path = config["dat_file"]
            output_path = config["output"]["path"]
            output_filename = config["output"]["filename"]
            output_file_path = os.path.join(output_path, output_filename)

    except Exception as e:
        print(f"Error reading config file: {e}")
    
def write_to_output_file(output_path, content):
    try:
        with open(output_path, 'a') as file:
            file.write(content + '\n')
    except Exception as e:
        print(f"Error writing to output file: {e}")



menu_structure = {
    '1': {'label': 'Run in 1 time timeout mode', 'submenu': None},
    '2': {'label': 'Run in N times timeout mode', 'submenu': None},
    '3': {'label': 'Run in continuous N times over M ms mode', 'submenu': None},
    '4': {'label': 'Run in switch check mode', 'submenu': None},
    'q': {'label': 'Quit', 'submenu': None}
}


def get_user_input(menu):
    
    print("Available options:")
    for option in menu:
        print(f"{option}. {menu[option]['label']}")
    user_input = None
    user_input = input("Enter option: ")

    while user_input not in menu:
        print("Invalid option. Please try again.")
        print("Available options:")
        for option in menu:
            print(f"{option}. {menu[option]['label']}")

        user_input = input("Enter option: ")

    return user_input




def analyze_logs(log_entries, mode):

    mode_input = int(mode)

    with open(output_file_path, 'w'):
        pass

    if mode_input == 1:
        analyze_mode_1(log_entries, output_file_path)
    elif mode_input == 2:
        analyze_mode_2(log_entries, output_file_path)
    elif mode_input == 3:
        analyze_mode_3(log_entries, output_file_path)
    elif mode_input == 4:
        analyze_mode_4(log_entries, output_file_path)

def analyze_mode_1(log_entries, output_path):
    timeouts = {}

    for entry in log_entries:
        ip = entry["ip"]
        timestamp = datetime.strptime(entry["timestamp"], "%Y%m%d%H%M%S")

        if entry["ping"] is None:
            if ip not in timeouts:
                timeouts[ip] = {"start": timestamp, "end": None}
        else:
            if ip in timeouts and timeouts[ip]["end"] is None:
                timeouts[ip]["end"] = timestamp
                output_content = f"Timeout for {ip} from {timeouts[ip]['start']} to {timeouts[ip]['end']}"
                write_to_output_file(output_path, output_content)
                print(output_content)  
                timeouts.pop(ip)

    for ip, timeout_info in timeouts.items():
        output_content = f"Timeout for {ip} from {timeout_info['start']} to end of log"
        write_to_output_file(output_path, output_content)
        print(output_content)    

def analyze_mode_2(log_entries, output_path):
    consecutive_timeouts = {}

    for entry in log_entries:
        ip = entry["ip"]
        timestamp = datetime.strptime(entry["timestamp"], "%Y%m%d%H%M%S")

        if entry["ping"] is None:
            if ip not in consecutive_timeouts:
                consecutive_timeouts[ip] = {"count": 1, "start_time": timestamp}
            else:
                consecutive_timeouts[ip]["count"] += 1
        else:
            if ip in consecutive_timeouts and consecutive_timeouts[ip]["count"] >= timeout_times_threshold:
                end_timestamp = timestamp
                output_content = f"Consecutive timeouts for {ip} from {consecutive_timeouts[ip]['start_time']} to {end_timestamp} over {timeout_times_threshold} times"
                write_to_output_file(output_path, output_content)
                print(output_content) 

            consecutive_timeouts.pop(ip, None)

    for ip, timeout_info in consecutive_timeouts.items():
        output_content = f"Consecutive timeouts for {ip} from {timeout_info['start_time']} to end of log over {timeout_times_threshold} times"
        write_to_output_file(output_path, output_content)
        print(output_content) 

def analyze_mode_3(log_entries, output_path):
    timeouts_count = {}

    for entry in log_entries:
        ip = entry["ip"]
        timestamp = datetime.strptime(entry["timestamp"], "%Y%m%d%H%M%S")

        if entry["ping"] is None or entry["ping"] > timeout_ping_threshold:
            if ip not in timeouts_count:
                timeouts_count[ip] = {"count": 1, "start_time": timestamp}
            else:
                timeouts_count[ip]["count"] += 1
        else:
            if ip in timeouts_count and timeouts_count[ip]["count"] >= timeout_times_threshold:
                end_timestamp = timestamp
                output_content = f"High ping timeouts for {ip} from {timeouts_count[ip]['start_time']} to {end_timestamp}"
                write_to_output_file(output_path, output_content)
                print(output_content) 

            timeouts_count.pop(ip, None)

    for ip, timeout_info in timeouts_count.items():
        output_content = f"High ping timeouts for {ip} from {timeout_info['start_time']} to end of log"
        write_to_output_file(output_path, output_content)
        print(output_content) 

def analyze_mode_4(log_entries, output_path):
    switch_timeouts = {}

    for entry in log_entries:
        switch_ip = ".".join(entry["ip"].split(".")[:-1] + ["0"])
        timestamp = datetime.strptime(entry["timestamp"], "%Y%m%d%H%M%S")

        if entry["ping"] is None:
            if switch_ip not in switch_timeouts:
                switch_timeouts[switch_ip] = {"count": 1, "start_time": timestamp, "consecutive_time": entry["timestamp"]}
            elif entry["timestamp"] != switch_timeouts[switch_ip]["consecutive_time"]:
                switch_timeouts[switch_ip]["consecutive_time"] = entry["timestamp"]
                switch_timeouts[switch_ip]["count"] += 1
        else:
            if switch_ip in switch_timeouts:
                if switch_timeouts[switch_ip]["count"] >= timeout_times_threshold:
                    output_content = f"Switch {switch_ip} timeouts from {switch_timeouts[switch_ip]['start_time']} to {timestamp}"
                    write_to_output_file(output_path, output_content)
                    print(output_content) 
                        
                switch_timeouts.pop(switch_ip, None)

    for switch_ip, timeout_info in switch_timeouts.items():
        
        if timeout_info["count"] >= timeout_times_threshold:
            end_timestamp = datetime.strptime(log_entries[-1]["timestamp"], "%Y%m%d%H%M%S")
            output_content = f"Switch {switch_ip} timeouts from {timeout_info['start_time']} to {end_timestamp}"
            write_to_output_file(output_path, output_content)
            print(output_content) 

def main():
    read_config_file(config_file_path)
    log_entries = read_log_file(dat_file_path)
    while True:
        
        print("\nMain Menu:")
        print(f"The timeout times threthold N is {timeout_times_threshold}\nThe timeout ping threthold M is {timeout_ping_threshold}")
        user_choice = get_user_input(menu_structure)
        print("")
    
        if user_choice == 'q':
            break 
        analyze_logs(log_entries, user_choice)



if __name__ == "__main__":
    main()
