from socket import htons, ntohs, socket, AF_INET, SOCK_DGRAM, IPPROTO_UDP
from typing import Tuple
import logging

BUFFER_SIZE = 2 ** 8
RECV_BUFFER_SIZE = BUFFER_SIZE + 8
FORMAT = '%(asctime)-15s %(levelname)-10s %(message)s'
logging.basicConfig(format=FORMAT)
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)

def checksum(data: bytes) -> int:
    chk: int = 0
    for byte in data:
        chk += byte
    
    return -chk & 0xffffffff

def create_frame(data: bytes, seq_number: int) -> Tuple[int, bytes]:
    data_size: int = len(data)
    net_data_length: int = htons(data_size)
    net_seq_number: int = htons(seq_number + data_size)

    chksum: int = checksum(data)

    frame: bytes = net_seq_number.to_bytes(length=2, byteorder='big', signed=False)\
         + net_data_length.to_bytes(length=2, byteorder='big', signed=False)\
         + data\
         + chksum.to_bytes(length=4, byteorder='big', signed=False)
    
    return data_size + 8, data_size, frame

def decode_frame(frame: bytes, seq_number: int) -> Tuple[bool, bool, int, bytes]:
    received_seq_number: int = ntohs(int.from_bytes(frame[:2], byteorder='big'))
    data_length: int = ntohs(int.from_bytes(frame[2:4], byteorder='big'))
    data:bytes = frame[4:-4]
    net_chksum: int = int.from_bytes(frame[-4:], byteorder='big')
    chksum: int = checksum(data)

    chksum_is_correct: bool = net_chksum == chksum
    sequence_number_is_correct: bool = (seq_number + data_length) == received_seq_number

    return chksum_is_correct, sequence_number_is_correct, received_seq_number, data 

def create_ack(seq_number: int) -> bytes:
    LOGGER.debug(f"Creating ACK ({seq_number})")
    net_seq_number: int = htons(seq_number)

    frame: bytes = "AACK".encode('ascii')
    frame +=  net_seq_number.to_bytes(length=2, byteorder='big')

    return frame

def create_nack(seq_number: int) -> bytes:
    LOGGER.debug(f"Creating NACK ({seq_number})")
    net_seq_number: int = htons(seq_number)

    frame: bytes = "NACK".encode('ascii')
    frame +=  net_seq_number.to_bytes(length=2, byteorder='big')

    return frame

def parse_ack(ack_data: bytes, sequence_number: int) -> Tuple[bool, bool, int]:
    status: str = ack_data[:4].decode('ascii')
    seq_number: int = ntohs(int.from_bytes(ack_data[4:], byteorder='big') )

    ack_received: bool = (status == "AACK")

    sequence_number_is_correct: bool = (seq_number == sequence_number)

    LOGGER.debug(f"Parsing ACK: {ack_received} (is_ack), {sequence_number_is_correct} (correct seq. number), {sequence_number} (seq.number)")

    return ack_received, sequence_number_is_correct, seq_number

def get_end_frame() -> bytes:
    return "FIN".encode('ascii')

def is_end_frame(frame: bytes) -> bool:
    try:
        return frame.decode('ascii') == "FIN"
    except UnicodeDecodeError:
        return False

def connect(server_socket: socket, server_ip: str, port: int) -> Tuple[str, int]:
    raw_data: bytes = b''
    data_port: int = 0

    server_address = (server_ip, port)

    server_socket.sendto("SYN".encode('ascii'), server_address)

    LOGGER.debug("SYN sent")

    raw_data, net_server_address = server_socket.recvfrom(BUFFER_SIZE)
    data: str = raw_data.decode('ascii')

    if data[:8] != "SYN-ACK-":
        raise ConnectionError("Error receiving SYN-ACK")

    LOGGER.debug("SYN-ACK received: %s" % data)

    try:
        data_port = int(data[8:])
    except ValueError:
        raise ValueError("Received port must be an integer")

    server_socket.sendto("ACK".encode('ascii'), server_address)

    LOGGER.debug("ACK sent")
    
    return (server_ip, data_port)

def accept(server_socket: socket, server_ip: str, data_port: int) -> Tuple[socket, Tuple[str, int]]:
    raw_data: bytes = b''
    nbytes: int = 0

    raw_data, client_address = server_socket.recvfrom(BUFFER_SIZE)

    if raw_data.decode('ascii') != "SYN":
        LOGGER.debug("First frame must be a SYN")
        return

    LOGGER.debug("SYN received")

    syn_ack: bytes = f"SYN-ACK-{data_port}".encode('ascii')

    nbytes = server_socket.sendto(syn_ack, client_address)
    if nbytes != len(syn_ack):
        raise ConnectionError("Error sending SYN-ACK")

    LOGGER.debug("Opening a data connection on port %d" % data_port)

    raw_data, client_address2 = server_socket.recvfrom(BUFFER_SIZE)

    if raw_data.decode('ascii') != "ACK":
        raise ConnectionError("Third frame must be ACK")

    if client_address2 != client_address:
        raise ConnectionError("ACK received from another client")

    LOGGER.debug("ACK received")
    
    data_sock: socket = socket(family=AF_INET, type=SOCK_DGRAM, proto=IPPROTO_UDP)

    address = (server_ip, data_port)

    data_sock.bind(address)

    return data_sock, client_address
