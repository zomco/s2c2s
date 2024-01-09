import sys
import logging
import socket
import time
import json

import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp

logger = modbus_tk.utils.create_logger("console")

master = None

CONFIG_FILE = 'config.json'

config_data = {
    "deviceIP": "192.168.1.100",
    "cloudIP": "192.168.1.101"
}

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        return config_data

def forward_to_cloud(data, cloud_server_ip, cloud_server_port):
    try:
        cloud_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cloud_socket.connect((cloud_server_ip, cloud_server_port))
        cloud_socket.sendall(data.encode())
        cloud_socket.close()
    except Exception as e:
        logger.error("Error forwarding data to cloud server:", e)

def start_forwarder(device_ip, cloud_ip):
    global master
    try:
        master = modbus_tcp.TcpMaster(host=device_ip)
        logger.info("Modbus device connected")
        while master:
            data = master.execute(1, cst.READ_HOLDING_REGISTERS, 3, 10)
            if data:
                logger.info(data)
                data_str = ','.join(str(val) for val in data)
                forward_to_cloud(data_str, cloud_server_ip=cloud_ip, cloud_server_port=11502)
            else:
                logger.info("Could not poll data from device")
            time.sleep(5000 / 1000)

    except modbus_tk.modbus.ModbusError as e:
        logger.error("%s- Code=%d" % (e, e.get_exception_code()))


if __name__ == "__main__":
    config_data = load_config()
    start_forwarder(config_data['deviceIP'], config_data['cloudIP'])
