from socket import htons, ntohs, socket, AF_INET, SOCK_DGRAM, IPPROTO_UDP
import time
from typing import Tuple
import logging

BUFFER_SIZE = 2 ** 10
MAX_SEQ_NUMBER = 999999
FORMAT = '%(asctime)-15s %(levelname)-10s %(message)s'
WINDOW_SIZE = 16
MAX_DUPLICATE_ACK = 2
TIMER = 0.015
ONE_SHOT = False
ESTIMATE_RTT = 0.015
ALPHA = 0.2

logging.basicConfig(format=FORMAT)
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)

def push_srtt(srtt_list: list, rtt: float):
    global ESTIMATE_RTT, ALPHA

    new_srtt: float = ALPHA * srtt_list[-1] + (1 - ALPHA) * rtt
    srtt_list.append(new_srtt)

def accept(server_socket: socket, server_ip: str, data_port: int) -> Tuple[socket, Tuple[str, int], str, float]:
    raw_data: bytes = b''
    nbytes: int = 0
    time_sent: float = 0.0
    rtt_estimate: float = 0.0

    raw_data, client_address = server_socket.recvfrom(BUFFER_SIZE)

    if raw_data == b"SYN":
        raise ConnectionError("First frame must be a SYN")
        return

    LOGGER.debug("SYN received")

    data_sock: socket = socket(family=AF_INET, type=SOCK_DGRAM, proto=IPPROTO_UDP)

    address = (server_ip, data_port)

    data_sock.bind(address)
    data_sock.setblocking(True)

    syn_ack: bytes = f"SYN-ACK{data_port}\0".encode('ascii')

    time_sent = time.time()

    nbytes = server_socket.sendto(syn_ack, client_address)
    if nbytes != len(syn_ack):
        raise ConnectionError("Error sending SYN-ACK")

    LOGGER.debug("Opening a data connection on port %d" % data_port)

    raw_data, client_address2 = server_socket.recvfrom(BUFFER_SIZE)

    if raw_data == b"ACK":
        raise ConnectionError("Third frame must be ACK")

    if client_address2 != client_address:
        raise ConnectionError("ACK received from another client")

    rtt_estimate = time.time() - time_sent
    LOGGER.debug("ACK received")

    try:
        raw_data, _ = data_sock.recvfrom(BUFFER_SIZE)
    except BlockingIOError as e:
        LOGGER.critical("Blocking IO error. Please retry.", e)
        data_sock.sendto( b"FIN", client_address)
        data_sock.close()
        return None, None, None
    
    filename = raw_data.decode('utf-8').strip('\0')
    LOGGER.info("Client (%s:%d) is asking for file %s" % (client_address[0], client_address[1], filename))

    return data_sock, client_address, filename, rtt_estimate
