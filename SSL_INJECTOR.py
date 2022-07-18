#!/bin/env python3

import subprocess
import socket
import threading
import sys,os,re
import select
import configparser
import ssl
from multiprocessing import Process

settings = configparser.ConfigParser()
settings.read('settings.ini')
SNI_HOST = settings['SETTINGS']['SNI_HOST']
SSL_SERVER = settings['SETTINGS']['SSL_SERVER']
PORT = settings['SETTINGS']['PORT']
USERNAME = settings['SETTINGS']['USERNAME']
PASSWORD = settings['SETTINGS']['PASSWORD']

def tunneling(client,sockt):
    connected = True
    while connected == True:
        r, w, x = select.select([client,sockt], [], [client,sockt],3)
        if x: connected = False; break
        for i in r:
            try:
                data = i.recv(8192)
                if not data: connected = False; break
                if i is sockt:
                    client.send(data)
                else:
                    sockt.send(data)
            except:
                connected = False;break
    client.close()
    sockt.close()
    print('Disconnected')
def destination(client,address):
    try:
        request = client.recv(9124).decode()
        host = request.split(':')[0].split()[-1]
        port = request.split(':')[-1].split()[0]
        proxip = host
        proxport = port
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((proxip,int(proxport)))
        print(f'connected to {proxip}:{proxport}')
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        s = context.wrap_socket(s,server_hostname=str(SNI_HOST))
        client.send(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        tunneling(client,s)
    except Exception as e:
        print(e)

ssl_connection = subprocess.Popen((f'sshpass -p {PASSWORD} ssh -o ProxyCommand="nc -X CONNECT -x 127.0.0.1:9092 %h %p" {USERNAME}@{SSL_SERVER} -p {PORT} -CND 1080 -o StrictHostKeyChecking=no'),shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
try:
    sockt = socket.socket()
    sockt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sockt.bind(('', 9092))
    sockt.listen(0)
except OSError:
    print('Port already used by another process\nRun script again')
while True:
    try:
        client, address = sockt.accept()
        thr = threading.Thread(target=destination, args=(client, address))
        thr.start()
    except KeyboardInterrupt:
        sockt.close()
