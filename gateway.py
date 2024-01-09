import sys
import logging
import socket
import time
import json


def connect_to_server(ip, port):
    while True:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((ip, port))
            return client_socket
        except Exception as e:
            print(f"Connection error: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)

def forward_message(client1_socket, ip, cmd):
    try:
        client2_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client2_socket.settimeout(1)
        client2_socket.connect((ip, 502))
        client2_socket.send(bytes.fromhex(cmd))
        response_message = client2_socket.recv(1024)
        if response_message:
            print("Receive from server2: {}".format(response_message.hex()))
            response_data = {"ip":ip,"data":response_message.hex()}
            client1_socket.send(json.dumps(response_data).encode("utf-8"))
    except Exception as e:
        response_data = {"ip":ip,"error":"device unreachable"}
        client1_socket.send(json.dumps(response_data).encode("utf-8"))

def start_gateway():
    try:
        while True:
            client1_socket = connect_to_server('192.168.1.101', 12345)
            while True:
                request_message = client1_socket.recv(1024).decode("utf-8")
                if not request_message:
                    break
                print("Receive from server1: {}".format(request_message))
                try:
                    request_data = json.loads(request_message)
                    ip = request_data["ip"]
                    cmd = request_data["cmd"]
                    if ip and cmd:
                        forward_message(client1_socket, ip, cmd)
                    else:
                        response_data = {"error":"invalid params"}
                        client1_socket.send(json.dumps(response_data).encode("utf-8"))
                except Exception as e:
                     print("Decoding JSON has failed: {}".format(e))
                     response_data = {"error":"invalid format"}
                     client1_socket.send(json.dumps(response_data).encode("utf-8"))
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        client1_socket.close()


if __name__ == "__main__":
    start_gateway()
