import sys
import logging
import socket
import time
import json

from pymodbus.client.sync import ModbusTcpClient
from pymodbus.exceptions import ModbusIOException, ConnectionException

# 设置日志记录器的名称
logger = logging.getLogger(__name__)

# 设置日志记录器的等级
logger.setLevel(logging.DEBUG)  # 或者其他等级，如 logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL

# 创建一个日志处理器（例如，输出到控制台）
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # 设置处理器的等级

# 创建一个格式化程序
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)  # 应用格式化程序到处理器

# 将处理器添加到记录器
logger.addHandler(console_handler)

def load_config():
    try:
        with open('config.json', 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        return config_data


def connect_to_server(ip, port):
    while True:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((ip, port))
            return client_socket
        except Exception as e:
            logger.error(f"Connection error: {e}")
            logger.info("Retrying in 5 seconds...")
            time.sleep(5)


def forward_data(data):
    try:
        client1_socket = connect_to_server('192.168.1.101', 500)
        client1_socket.sendall(json.dumps(data).encode("utf-8"))
    except Exception as e:
        logger.error("Error forwarding data to cloud server:", e)


def encode_machine_data(client, slave, index):
    address = (index<<8) + 10
    # 0x0010 ~ 0x0017, 8 x 1 words 
    r0x0010 = client.read_discrete_inputs(address=address, count=8, unit=slave)
    if r0x0010.isError():
        logger.error(f"Poll machine[{index}](0x0010) error：{r0x0010}")
    d0x0010 = "" if r0x0010.isError() else r0x0010.bits

    # 0x0030 ~ 0x14c, 285 x 2 words
    r0x0030 = client.read_holding_registers(address=30, count=285, unit=slave)
    if r0x0030.isError():
        logger.error(f"Poll machine[{index}](0x0030) error：{r0x0030}")
    d0x0030 = "" if r0x0030.isError() else r0x0030.registers
    return { "0x10": d0x0010, "0x30": d0x0030 }


def encode_storage_data(client, slave, index):
    address = (index<<8) + 10
    # 0x0010 ~ 0x0020, 11 x 1 words
    r0x0010 = client.read_discrete_inputs(address=address, count=11, unit=slave)
    if r0x0010.isError():
        logger.error(f"Poll storage[{index}](0x0010) error：{r0x0010}")
    d0x0010 = "" if r0x0010.isError() else r0x0010.bits

    # 0x0030 ~ 0x005a, 43 x 2 words
    r0x0030 = client.read_holding_registers(address=30, count=43, unit=slave)
    if r0x0030.isError():
        logger.error(f"Poll storage[{index}](0x0030) error：{r0x0030}")
    d0x0030 = "" if r0x0030.isError() else r0x0030.registers
    return { "0x10": d0x0010, "0x30": d0x0030 }


def encode_monitor_data(client, slave):
    address = (200<<8) + 10
    # 0x0010 ~ 0x0018, 12 x 1 words 
    r0x0010 = client.read_discrete_inputs(address=address, count=12, unit=slave)
    if r0x0010.isError():
        logger.error(f"Poll monitor error：{r0x0010}")
    d0x0010 = "" if r0x0010.isError() else r0x0010.bits
    return { "0x10": d0x0010 }


def encode_data(client, slave):
    data = {}
    for i in range(0, 56):
        name = "machine" + str(i)
        data[name] = encode_machine_data(client, slave, i)
    for i in range(101, 108):
        name = "storage" + str(i - 101)
        data[name] = encode_machine_data(client, slave, i)
    data["monitor"] = encode_monitor_data(client, slave)
    return data


def pool_data(device):
    data = ""
    try:
        client = ModbusTcpClient(host=device["ip"], strict=False)
        data = encode_data(client, device["slave"])
    except Exception as exc:
        logger.error(f"Error when polling data {exc}")
    finally:
        client.close()
        return data


def start_forwarder(devices):
    while True:
        data = {}
        for device in devices:
            name = "slave" + str(device["slave"])
            data[name] = pool_data(device)

        forward_data(data)
        time.sleep(5000 / 1000)


if __name__ == "__main__":
    config_data = load_config()
    if config_data is None or "devices" not in config_data:
        logger.error("Config invalid, exiting..")
        pass 
    start_forwarder(config_data['devices'])
