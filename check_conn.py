import socket
import argparse
import time
import sys


parser = argparse.ArgumentParser(description='Test services')

parser.add_argument('--service-name', required=True)
parser.add_argument('--port', required=True)
parser.add_argument('--ip', required=True)

args = parser.parse_args()

service = str(args.service_name)
port = int(args.port)
ip = str(args.ip)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


for _ in range(100):
    erro = sock.connect_ex((ip, port))
    if erro == 0:
        print('Service %s connect!' % service)
        break
    else:
        print('Service %s error %s' % (service, erro), file=sys.stderr)
    time.sleep(5)