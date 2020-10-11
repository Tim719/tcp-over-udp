import argparse
import logging
import socket
from helpers import *
from typing import Tuple
from threading import Thread

FORMAT = '%(asctime)-15s %(levelname)-10s %(message)s'
logging.basicConfig(format=FORMAT)
LOGGER = logging.getLogger()
BUFFER_SIZE = 2 ** 10  # 1024. Keep buffer size as power of 2.

def handle_client(server_sock: socket, client_address: Tuple[str, int]):
    raw_data: bytes = b''
    chksum_succes: bool = False
    sequence_number_success: bool = False
    received_data: bytes = b''
    received_seq_number: int = 0
    seq_number: int = 1

    while True:
        print("Next byte expected: %d" % seq_number)
        raw_data, client_addr = server_sock.recvfrom(BUFFER_SIZE)

        if client_addr != client_address:
            print("Data received from wrong client")
            break

        if is_end_frame(raw_data):
            print("Terminating connection from client")
            break

        chksum_succes, sequence_number_success, received_seq_number, received_data = decode_frame(raw_data, seq_number)
        print(f"State: {chksum_succes} (chksum) - {sequence_number_success} (seq. number), Seq: {received_seq_number}\nData:{received_data.decode('utf-8')}")

        if chksum_succes and sequence_number_success:
            raw_data = create_ack(received_seq_number)
            seq_number = received_seq_number
        else:
            raw_data = create_nack(seq_number)    

        server_sock.sendto(raw_data, client_address)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Receiver a file using a connected transport protocol over UDP")
    parser.add_argument('-i', '--interface', required=False, help="Listening interface", default="0.0.0.0")
    parser.add_argument('-p', '--port', required=False, help="Port used for control connection", type=int, default=1234)
    parser.add_argument('-d', '--data', required=False, help="Port used for data connection (will be incremented for each new client)", type=int, default=5500)

    args = parser.parse_args()

    print("Listening to connections on %s:%d (data port: %d)" % (args.interface, args.port, args.data))

    server_sock: socket = socket(family=AF_INET, type=SOCK_DGRAM, proto=IPPROTO_UDP)

    server_address = (args.interface, args.port)

    server_sock.bind(server_address)

    data_port: int = args.data

    while True:
        data_socket, client_address = accept(server_sock, args.interface, data_port)
        print("New client connected")

        data_port += 1

        handle_client(data_socket, client_address)
    
    server_sock.close()