#!/usr/bin/env python3

import os
import argparse
import socket
import select
from helpers import *
from typing import Tuple, List
from threading import Thread, Lock
from datetime import datetime
import time

def handle_client(server_sock: socket, client_address: Tuple[str, int], filename: str):
    raw_data: bytes = b''
    raw_data_with_seq_number: bytes = b''
    recv_data: bytes = b''
    seq_number: int = 1

    rtt_list: List[float] = [ESTIMATE_RTT]
    srtt_list: List[float] = [ESTIMATE_RTT]
    avg_retries: List[int] = []

    end_of_file: bool = False

    begin_transmission_time: float = time.time()
    begin_time: int = 0

    last_rtt: float = ESTIMATE_RTT

    if not os.path.isfile(filename):
        LOGGER.warning("%s file does not exist." % filename)
        raw_data = b"FIN"
        server_sock.sendto(raw_data, client_address)
        return

    file_size: int = os.path.getsize(filename)

    with open(filename, 'rb') as fd:
        while True:
            raw_data = fd.read(BUFFER_SIZE)

            if not raw_data:
                break
            
            n_retries: int = 1
            formatted_seq_number = "%06d" % seq_number
            raw_data_with_seq_number = formatted_seq_number.encode('ascii') + raw_data
            begin_time = time.time_ns()

            while True:
                LOGGER.debug("Sending sequence #%s (trying %d)" % (formatted_seq_number, n_retries))

                server_sock.sendto(raw_data_with_seq_number, client_address)

                ready = select.select([server_sock], [], [], srtt(seq_number, srtt_list, rtt_list))
                if ready[0]:
                    recv_data, net_client_address = server_sock.recvfrom(BUFFER_SIZE)

                    last_rtt = (time.time_ns() - begin_time) / (10**9)
                    rtt_list.append(last_rtt)

                    received_ack_number = int(recv_data.decode('ascii').strip('\0')[3:])

                    if received_ack_number >= seq_number:
                        LOGGER.debug("Acknowledging sequence #%d" % received_ack_number)
                        avg_retries.append(n_retries)
                        break
        
                n_retries += 1
            
            seq_number = (seq_number + 1) % 999999

    transmission_duration: float = time.time() - begin_transmission_time
    transmission_rate: float = file_size /transmission_duration

    LOGGER.info("End of file transmission")
    LOGGER.info("Avg SRTT: %f s, Avg. RTT: %f s" % (sum(srtt_list)/len(srtt_list), sum(rtt_list)/len(rtt_list)))
    LOGGER.info("Avg retries : %f" % (sum(avg_retries) / len(avg_retries)))
    LOGGER.info("Total size: %d bytes" % file_size)
    LOGGER.info("Duration: %02fs" % transmission_duration)
    LOGGER.info("Data rate : %f bytes/s (%f kbytes/s)" % (transmission_rate, transmission_rate / 1000))

    server_sock.sendto( b"FIN", client_address)
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
        data_socket, client_address, filename = accept(server_sock, args.interface, data_port)

        if data_socket is None:
            continue

        data_port += 1

        client_thread = Thread(target=handle_client, args=(data_socket, client_address, filename))
        LOGGER.debug("Starting client thread")
        client_thread.start()

        client_threads.append(client_thread)
    
    LOGGER.debug("Joining client threads")
    for th in client_threads:
        th.join()
    
    server_sock.close()