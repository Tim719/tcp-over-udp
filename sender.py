import argparse
import socket
import os
from helpers import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a file using a connected transport protocol over UDP")
    parser.add_argument('-i', '--ip', required=True, help="Receiver IP address")
    parser.add_argument('-p', '--port', required=False, help="Port", type=int, default=1234)
    parser.add_argument('-f', '--file', required=True, help="File to send")

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"{args.file} must be an existing file")
        exit(-1)

    LOGGER.info("Sending %s to %s:%d" % (args.file, args.ip, args.port))

    server_sock: socket = socket(family=AF_INET, type=SOCK_DGRAM, proto=IPPROTO_UDP)

    server_address = connect(server_sock, args.ip, args.port)

    inp: str = ""
    bytes_sent: int = 0
    bytes_to_send: int = 0
    data_length: int = 0

    raw_data: bytes = b''

    sequence_number: int = 1

    with open(args.file, 'rb') as fd:
        while True:
            raw_data = fd.read(BUFFER_SIZE)

            if not raw_data:
                LOGGER.info("End of File")
                break
                
            LOGGER.debug(f"Sequence number: {sequence_number}")
            bytes_to_send, data_length, frame = create_frame(raw_data, sequence_number)
            LOGGER.debug("Frame sent (packet:%d, data:%d):" % (bytes_to_send, data_length))
            # LOGGER.debug(''.join(format(x, '02x') for x in frame))
            bytes_sent = server_sock.sendto(frame, server_address)
            sequence_number += data_length

            raw_data, _ = server_sock.recvfrom(BUFFER_SIZE)
            ack_status, sequence_number_is_correct, net_seq_number = parse_ack(raw_data, sequence_number)
    
    server_sock.sendto(get_end_frame(), server_address)
    
    server_sock.close()