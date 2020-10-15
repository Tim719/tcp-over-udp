from socket import htons, ntohs, socket, AF_INET, SOCK_DGRAM, IPPROTO_UDP
from typing import Tuple, List
import logging

BUFFER_SIZE = 2 ** 10 - 6
MAX_SEQ_NUMBER = 999999
FORMAT = '%(asctime)-15s %(levelname)-10s %(message)s'

logging.basicConfig(format=FORMAT)
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)

ESTIMATE_RTT: float = 0.01
CONVERGENCE_FACTOR: float = 0.2

def srtt(seq_number, srtt_list, rtt_list):
    global CONVERGENCE_FACTOR

    if seq_number < len(srtt_list):
        return srtt_list[seq_number]
    else:
        calc_srtt: float = CONVERGENCE_FACTOR * srtt(seq_number - 1, srtt_list, rtt_list) + (1 - CONVERGENCE_FACTOR) * rtt_list[seq_number - 1]
        srtt_list.append(calc_srtt)
        return calc_srtt

def accept(server_socket: socket, server_ip: str, data_port: int) -> Tuple[socket, Tuple[str, int]]:
    raw_data: bytes = b''
    nbytes: int = 0

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

    try:
        raw_data, _ = data_sock.recvfrom(BUFFER_SIZE)
    except BlockingIOError as e:
        LOGGER.critical("Blocking IO error. Please retry.", e)
        data_sock.sendto( b"FIN", client_address)
        data_sock.close()
        return None, None, None
    
    filename = raw_data.decode('utf-8').strip('\0')
    LOGGER.info("Client (%s:%d) is asking for file %s" % (client_address[0], client_address[1], filename))

    return data_sock, client_address, filename
