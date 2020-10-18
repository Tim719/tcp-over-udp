#!/usr/bin/env python3

import os
import argparse
import socket
import select
import time
from helpers import *
from typing import Tuple, List
from threading import Thread, Lock
from datetime import datetime
import collections


def handle_client(server_sock: socket, client_address: Tuple[str, int], filename: str):
    raw_data: bytes = b''
    seq_number: int = 1
    end_of_file: bool = False
    TIMER = 0.0180

    rtt_list: List[float] = [ESTIMATE_RTT]
    srtt_list: List[float] = [ESTIMATE_RTT]

    sent_seq = collections.deque(maxlen=WINDOW_SIZE)

    if not os.path.isfile(filename):
        LOGGER.warning("%s file does not exist." % filename)
        raw_data = b"FIN"
        server_sock.sendto(raw_data, client_address)
        return

    file_size = os.path.getsize(filename)
    start = time.time()
    time_armed = time.time()
    time_resent = time.time()

    begin_time: int = time.time_ns()

    with open(filename, 'rb') as fd:
        while True:
            ready = select.select([server_sock], [], [], srtt_list[-1])
            if ready[0]:
                raw_data, net_client_address = server_sock.recvfrom(BUFFER_SIZE)

                try:
                    received_ack_number = int(raw_data.decode('ascii').strip('\0')[3:])
                except ValueError:
                    LOGGER.critical("Malformated ACK number")
                    raise

                oldest_seq_number, sent_data = sent_seq[0]

                # LOGGER.debug("Received ACK %d" % received_ack_number)
                # list_to_str = ''.join(str(l)+', ' for (l, _) in sent_seq)
                # LOGGER.debug("Sequences in list: %s" % (list_to_str))

                if received_ack_number + 1 < oldest_seq_number :
                    last_rtt = (time.time_ns() - begin_time) / (10**9)
                    rtt_list.append(last_rtt)
                    srtt_push(srtt_list, rtt_list)
                    continue
                if received_ack_number + 1 == oldest_seq_number:
                    # LOGGER.debug("Duplicate ACK for sequence %d %f" % (received_ack_number, time.time() - time_resent))
                    if  time.time() - time_resent > TIMER:  #avoid resending too many times while we can't see effect of the resending
                        LOGGER.debug("Duplicate ACK for sequence %d" % received_ack_number)
                        for seq in sent_seq:
                            number, data = seq
                            LOGGER.debug("Resending sequence #%d" % number)
                            server_sock.sendto(data, client_address)
                        time_armed = time.time()
                        time_resent = time.time()
                    continue

                while True:
                    sent_seq_number, sent_data = sent_seq.popleft() 
                    # Normalement on ne devrait pas être dans le cas où on pop un tableau vide

                    if received_ack_number <= sent_seq_number:
                        break
                time_armed = time.time()
                time_resent = 0.0

            if time.time() - time_armed > TIMER :
                LOGGER.debug("Timeout for sequence %d" % sent_seq[0][0])
                for seq in sent_seq:
                    number, data = seq
                    LOGGER.debug("Resending sequence #%d" % number)
                    server_sock.sendto(data, client_address)
                time_armed = time.time()

            # TODO: read next data befora having empty space but append and send it only when space is free
            if len(sent_seq) < WINDOW_SIZE:
                raw_data = fd.read(BUFFER_SIZE - 6)

                if not raw_data :
                    if len(sent_seq) == 0 :
                        break
                    continue

                formatted_seq_number = "%06d" % seq_number
                LOGGER.debug("Sending sequence #%s" % formatted_seq_number)
                raw_data = formatted_seq_number.encode('ascii') + raw_data

                sent_seq.append((seq_number, raw_data)) # On  ajoute le paquet au tableau

                begin_time = time.time_ns()
                server_sock.sendto(raw_data, client_address)
                seq_number += 1
    
    LOGGER.info("End of file")

    raw_data = b"FIN"
    server_sock.sendto(raw_data, client_address)
    server_sock.close()
    LOGGER.info("Data rate : %d KB/s" % ((file_size / ( time.time() - start )) / 1000) )
    LOGGER.info("Avg SRTT: %f s, Avg. RTT: %f s" % (sum(srtt_list)/len(srtt_list), sum(rtt_list)/len(rtt_list)))

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
        LOGGER.info("New client connected")

        data_port += 1

        client_thread = Thread(target=handle_client, args=(data_socket, client_address, filename))
        LOGGER.debug("Starting client thread")
        client_thread.start()

        client_threads.append(client_thread)
    
    LOGGER.debug("Joining client threads")
    for th in client_threads:
        th.join()
    
    server_sock.close()