import argparse
import logging
import socket
from helpers import *

FORMAT = '%(asctime)-15s %(levelname)-10s %(message)s'
logging.basicConfig(format=FORMAT)
LOGGER = logging.getLogger()
BUFFER_SIZE = 2 ** 10  # 1024. Keep buffer size as power of 2.

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a file using a connected transport protocol over UDP")
    parser.add_argument('-i', '--ip', required=True, help="Receiver IP address")
    parser.add_argument('-p', '--port', required=False, help="Port", type=int, default=1234)
    parser.add_argument('-f', '--file', required=True, help="File to send")

    args = parser.parse_args()

    print("Sending %s to %s:%d" % (args.file, args.ip, args.port))

    server_sock: socket = socket(family=AF_INET, type=SOCK_DGRAM, proto=IPPROTO_UDP)

    server_address = connect(server_sock, args.ip, args.port)

    inp: str = ""
    bytes_sent: int = 0
    bytes_to_send: int = 0
    data_length: int = 0

    raw_data: bytes = b''

    sequence_number: int = 1

    while inp.lower() != 'end':
        inp = input('> ')
        print(f"Sequence number: {sequence_number}")
        bytes_to_send, data_length, frame = create_frame(inp.encode('utf-8'), sequence_number)
        print("Frame sent (packet:%d, data:%d):\n" % (bytes_to_send, data_length), ''.join(format(x, '02x') for x in frame))
        bytes_sent = server_sock.sendto(frame, server_address)
        sequence_number += data_length

        raw_data, _ = server_sock.recvfrom(BUFFER_SIZE)
        ack_status, sequence_number_is_correct, net_seq_number = parse_ack(raw_data, sequence_number)

        print(f"ACK: {ack_status}. Valid seq. number: {sequence_number_is_correct}. Next byte: {net_seq_number}")
    
    server_sock.sendto(get_end_frame(), server_address)
    
    server_sock.close()