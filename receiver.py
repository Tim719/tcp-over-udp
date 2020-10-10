import argparse
import logging

FORMAT = '%(asctime)-15s %(levelname)-10s %(message)s'
logging.basicConfig(format=FORMAT)
LOGGER = logging.getLogger()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Receiver a file using a connected transport protocol over UDP")
    parser.add_argument('-i', '--interface', required=False, help="Listening interface", default="0.0.0.0")
    parser.add_argument('-p', '--port', required=False, help="Port used for control connection", type=int, default=1234)
    parser.add_argument('-d', '--data', required=False, help="Port used for data connection (will be incremented for each new client)", type=int, default=5500)

    args = parser.parse_args()

    print("Listening to connections on %s:%d (data port: %d)" % (args.interface, args.port, args.data))