from __future__ import print_function
import datetime, time, os
import P17_003, P17_022R2_A
from flask import Flask, abort, render_template
from flask import url_for, redirect, request, make_response, session, send_from_directory
from flask_app_pi import pi_blueprint
import parse_iwlist

import os
dBase32 = '0123456789ABCDEFGHJKLMNPRSTUVWXY'

app = Flask(__name__, static_url_path='/static')
app.register_blueprint(pi_blueprint)
app.secret_key = "not a secret key"


@app.route('/')
def index():
    return render_template('base.html', name = "base")

@app.route('/download_log',methods=['GET'])
def download_log():
    filename = "userLog.txt"
    with open(filename, 'w') as f:
        f.truncate()
    with open('tmp1.out') as f:
        lines = f.readlines()
        output_content = (request.cookies.get('Output Content') if(request.cookies.get('Output Content')) else "")
        with open(filename, 'w') as f:
            f.write(output_content)
            f.writelines(lines)
    #return flask_app.app.send_static_file('userLog.txt')

    return send_from_directory(directory=app.root_path, filename=filename, as_attachment=True)

@app.route('/wifi_config', methods = ['GET'])
def wifi_page():
    os.system("sudo iwlist wlan0 scan")
    wifi_list = parse_iwlist.get_interfaces(interface = "wlan0");
    return render_template('wifi_config.html', name = "wifi", wifi_list = wifi_list)

@app.route('/select_wifi', methods = ['GET', 'POST'])
def select():
    ssid, password = request.form.get('ap_info'), request.form.get('psw')
    print(ssid)
    print("\n")
    print(password)
    if(not password):
        password = ""
    with open("wpa_supplicant.conf", 'a') as f:
        f.write("\nnetwork = {\n")
        f.write("\tssid=\""+ssid+"\"\n")
        f.write("\tpsk=\""+password+"\"\n")
        f.write("}")
    os.system("sudo cp wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf")
    os.system("sudo ifdown wlan0")
    os.system("sudo ifup wlan0")
    return render_template('wifi_config.html', name = "wifi")

@app.route('/refresh', methods = ['GET', 'POST'])
def refresh():
    os.system("sudo iwlist wlan0 scan")
    wifi_list = parse_iwlist.get_interfaces(interface = "wlan0");
    return render_template('wifi_config.html', name = "wifi", wifi_list = wifi_list)
    
if __name__ == '__main__': 
    app.run()
