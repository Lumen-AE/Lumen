"""Literal JSON bridge to the paused simulator. No model/code execution tools.

An external API loop may import SimulationClient. This transport does not choose
a model, generate machine words, retrieve examples or transform instructions.
"""
import argparse
import json
import sys
import zmq


class SimulationClient:
    def __init__(self, address='tcp://127.0.0.1:5567', timeout_ms=120000):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.RCVTIMEO, timeout_ms)
        self.socket.setsockopt(zmq.SNDTIMEO, timeout_ms)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.connect(address)

    def send_literal_json(self, model_text):
        # Forward raw model output without fixing, assembling, evaluating or encoding it.
        self.socket.send_string(model_text)
        return self.socket.recv_json()

    def close(self):
        self.socket.close(); self.context.term()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--address', default='tcp://127.0.0.1:5567')
    args = parser.parse_args()
    client = SimulationClient(args.address)
    try:
        for line in sys.stdin:
            print(json.dumps(client.send_literal_json(line)), flush=True)
    finally: client.close()


if __name__ == '__main__': main()
