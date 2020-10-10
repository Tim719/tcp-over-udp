import argparse
import logging

FORMAT = '%(asctime)-15s %(levelname)-10s %(message)s'
logging.basicConfig(format=FORMAT)
LOGGER = logging.getLogger()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a file using a connected transport protocol over UDP")
    parser.add_argument('-i', '--ip', required=True, help="Receiver IP address")
    parser.add_argument('-p', '--port', required=False, help="Port", type=int, default=1234)
    parser.add_argument('-f', '--file', required=True, help="File to send")

    args = parser.parse_args()

    print("Sending %s to %s:%d" % (args.file, args.ip, args.port))