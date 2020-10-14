from socket import htons, ntohs, socket, AF_INET, SOCK_DGRAM, IPPROTO_UDP
from typing import Tuple, List
import logging

BUFFER_SIZE = 2 ** 10
MAX_SEQ_NUMBER = 999999
FORMAT = '%(asctime)-15s %(levelname)-10s %(message)s'

AVG_RTT: float = 0.010
MAX_RETRIES: int = 32

logging.basicConfig(format=FORMAT)
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)

ESTIMATE_RTT: float = 1
CONVERGENCE_FACTOR: float = 0.8
RTT: List[float] = [ESTIMATE_RTT]

SRTT_MARGIN: float = 1.5

def srtt(seq_number):
    global ESTIMATE_RTT

    if seq_number == 0:
        return ESTIMATE_RTT
    else:
        return CONVERGENCE_FACTOR * srtt(seq_number - 1) + (1 - CONVERGENCE_FACTOR) * RTT[seq_number - 1]

def accept(server_socket: socket, server_ip: str, data_port: int) -> Tuple[socket, Tuple[str, int]]:
    raw_data: bytes = b''
    nbytes: int = 0

    raw_data, client_address = server_socket.recvfrom(BUFFER_SIZE)

    if raw_data == b"SYN":
        raise ConnectionError("First frame must be a SYN")
        return

    LOGGER.debug("SYN received")

    syn_ack: bytes = f"SYN-ACK{data_port}\0".encode('ascii')

    nbytes = server_socket.sendto(syn_ack, client_address)
    if nbytes != len(syn_ack):
        raise ConnectionError("Error sending SYN-ACK")

    LOGGER.debug("Opening a data connection on port %d" % data_port)

    raw_data, client_address2 = server_socket.recvfrom(BUFFER_SIZE)

    if raw_data == b"ACK":
        raise ConnectionError("Third frame must be ACK")

    if client_address2 != client_address:
        raise ConnectionError("ACK received from another client")

    LOGGER.debug("ACK received")
    
    data_sock: socket = socket(family=AF_INET, type=SOCK_DGRAM, proto=IPPROTO_UDP)

    address = (server_ip, data_port)

    data_sock.bind(address)
    data_sock.setblocking(False)

    return data_sock, client_address
