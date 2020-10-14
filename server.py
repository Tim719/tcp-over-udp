#!/usr/bin/env python3

import os
import argparse
import socket
import select
from helpers import *
from typing import Tuple, List
from threading import Thread, Lock
from datetime import datetime


def handle_client(server_sock: socket, client_address: Tuple[str, int]):
    raw_data: bytes = b''
    filename: str = ""
    seq_number: int = 1

    end_of_file: bool = False

    raw_data, net_client_address = server_sock.recvfrom(BUFFER_SIZE)
    filename = raw_data.decode('utf-8').strip('\0')
    LOGGER.info("Client (%s:%d) is asking for file %s" % (client_address[0], client_address[1], filename))

    if not os.path.isfile(filename):
        LOGGER.warning("%s file does not exist." % filename)
        raw_data = b"FIN"
        server_sock.sendto(raw_data, client_address)
        return

    with open(filename, 'rb') as fd:
        while True:
            raw_data = fd.read(BUFFER_SIZE - 6)

            if not raw_data:
                break
            
            n_retries: int = 1

            while n_retries <= MAX_RETRIES:
                formatted_seq_number = "%06d" % seq_number
                LOGGER.debug("Sending sequence #%s (try %d/%d)" % (formatted_seq_number, n_retries, MAX_RETRIES))

                raw_data = formatted_seq_number.encode('ascii') + raw_data
                server_sock.sendto(raw_data, client_address)

                ready = select.select([server_sock], [], [], ACK_TIMEOUT)
                if ready[0]:
                    raw_data, net_client_address = server_sock.recvfrom(BUFFER_SIZE)

                    try:
                        received_ack_number = int(raw_data.decode('ascii').strip('\0')[3:])
                    except ValueError:
                        LOGGER.critical("Malformated ACK number")
                        raise

                    if received_ack_number == seq_number:
                        LOGGER.debug("Acknowledging sequence #%d" % received_ack_number)
                        break
                else: 
                    LOGGER.debug("ACK #%d not received. Retrying" % seq_number)

                n_retries += 1
            
            if n_retries > MAX_RETRIES:
                LOGGER.warning("ERROR sending sequence #%d (%d retries)" % (seq_number, n_retries - 1))
                break
            
            seq_number += 1

    
    LOGGER.info("End of file")

    raw_data = b"FIN"
    server_sock.sendto(raw_data, client_address)
    server_sock.close()

            

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Receiver a file using a connected transport protocol over UDP")
    parser.add_argument('-i', '--interface', required=False, help="Listening interface", default="0.0.0.0")
    parser.add_argument('port', nargs="?", help="Port used for control connection", type=int, default=1234)
    parser.add_argument('-d', '--data', required=False, help="Port used for data connection (will be incremented for each new client)", type=int, default=5500)
    parser.add_argument('-v', '--verbose', required=False, help="Give more infos by increasing verbosity", type=bool, default=False, const=True, nargs='?')

    args = parser.parse_args()

    LOGGER.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    LOGGER.info("Server started on %s:%d (data port: %d)" % (args.interface, args.port, args.data))

    server_sock: socket = socket(family=AF_INET, type=SOCK_DGRAM, proto=IPPROTO_UDP)
    server_address = (args.interface, args.port)
    server_sock.bind(server_address)

    data_port: int = args.data
    client_threads: list = []

    while True:
        data_socket, client_address = accept(server_sock, args.interface, data_port)
        LOGGER.info("New client connected")

        data_port += 1

        client_thread = Thread(target=handle_client, args=(data_socket, client_address))
        LOGGER.debug("Starting client thread")
        client_thread.start()

        client_threads.append(client_thread)
    
    LOGGER.debug("Joining client threads")
    for th in client_threads:
        th.join()
    
    server_sock.close()