import json
import time
import threading
from datetime import datetime
import random
import numpy as np
import re


class IPAddressInfo:
    def __init__(self, ip, expected_ping, packet_loss, is_timeout):
        self.ip = ip
        self.expected_ping = expected_ping
        self.packet_loss = packet_loss
        self.is_timeout = is_timeout


class LogEntry:
    def __init__(self, timestamp, ip, ping):
        self.timestamp = timestamp
        self.ip = ip
        self.ping = ping


class IntervalInfo:
    def __init__(self, generate, store):
        self.generate = generate
        self.store = store


ip_addresses = []
global_interval = IntervalInfo(0, 0)
stop = False
mtx = threading.Lock()
#cv = threading.Condition()


import re

def read_config():
    global ip_addresses, global_interval
    try:
        with open("config.json", "r") as file:
            config = json.load(file)

            interval_info = IntervalInfo(config["interval"]["generate"], config["interval"]["store"])

            timeout_switch = config.get("timeout_switch", {}) 
            print("Timeout Switch Configuration:", timeout_switch) 

            is_all_timeout = timeout_switch.get("0.0.0.0", False) 

            for item in config["ip_addresses"]:
                ip = item["ip"]
                expected_ping = item["expected_ping"]
                packet_loss = item["packet_loss"]

                is_timeout = is_all_timeout

                for ip_prefix, is_timeout_value in timeout_switch.items():
                    if ip_prefix == "0.0.0.0":
                        continue 
                    stripped_prefix = re.sub(r'\.0*$', '', ip_prefix) 
                    if ip.startswith(stripped_prefix):
                        is_timeout = is_timeout_value
                        break

                ip_info = IPAddressInfo(ip, expected_ping, packet_loss, is_timeout)
                ip_addresses.append(ip_info)

            global_interval = interval_info

    except Exception as e:
        print(f"Error reading config.json: {e}")




def generate_log_entry(ip_info):
    if ip_info.is_timeout:
        entry = LogEntry(
            timestamp=datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            ip=ip_info.ip,
            ping=-1
        )
    else:
        if random.uniform(0, 1) <= ip_info.packet_loss / 100.0:
            entry = LogEntry(
                timestamp=datetime.utcnow().strftime("%Y%m%d%H%M%S"),
                ip=ip_info.ip,
                ping=-1
            )
        else:
            entry = LogEntry(
                timestamp=datetime.utcnow().strftime("%Y%m%d%H%M%S"),
                ip=ip_info.ip,
                ping=np.random.poisson(ip_info.expected_ping)
            )

    return entry



def write_log_to_file(log):
    with open("log.dat", "a") as log_file:
        for entry in log:
            ping_value = "-" if entry.ping == -1 else str(entry.ping)
            log_file.write(f"{entry.timestamp},{entry.ip},{ping_value}\n")



def generate_logs():
    global ip_addresses, global_interval, stop
    log = []
    start_time = datetime.utcnow()

    while True:
        for ip_info in ip_addresses:
            entry = generate_log_entry(ip_info)
            log.append(entry)

            if entry.ping == -1:
                print(f"{entry.timestamp},{ip_info.ip},-")
            else:
                print(f"{entry.timestamp},{ip_info.ip},{entry.ping}")

        time.sleep(global_interval.generate)

        with mtx:
            if stop:
                break

        current_time = datetime.utcnow()
        elapsed_seconds = (current_time - start_time).total_seconds()

        if elapsed_seconds >= global_interval.store:
            write_log_to_file(log)
            log = []
            start_time = datetime.utcnow()


def stop_program():
    global stop
    with mtx:
        stop = True
        


def main():
    global ip_addresses, global_interval
    read_config()

    t = threading.Thread(target=generate_logs)
    t.start()

    time.sleep(600)

    stop_program()
    t.join()


if __name__ == "__main__":
    main()
