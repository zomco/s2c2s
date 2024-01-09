import sys
import logging
import socket
import time
import json

from flask import Flask, render_template, request
app = Flask(__name__)

# 默认的配置文件路径
CONFIG_FILE = 'config.json'

# 初始默认配置
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

def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/config', methods=['POST'])
def config():
    data = request.get_json()
    config_data['deviceIP'] = data['deviceIP']
    config_data['cloudIP'] = data['cloudIP']
    save_config(config_data)
    return "Configuration updated"

@app.route('/status', methods=['GET'])
def status():
    return json.dumps(config_data)


@app.route('/restart', methods=['GET'])
def restart():
    return json.dumps(config_data)

if __name__ == "__main__":
    config_data = load_config()
    app.run(debug=True)

