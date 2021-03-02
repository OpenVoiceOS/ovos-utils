from ovos_utils.messagebus import send_binary_data_message, \
    send_binary_file_message, decode_binary_message, listen_for_message

from time import sleep
import json
from os.path import dirname, join

# random file
my_file_path = join(dirname(__file__), "music.txt")
with open(my_file_path, "rb") as f:
    original_binary = f.read()


def receive_file(message):
    print("Receiving file")
    path = message.data["path"]
    print(path)
    hex_data = message.data["binary"]

    # all accepted decode formats
    binary_data = decode_binary_message(message)
    print(binary_data == original_binary)
    binary_data = decode_binary_message(hex_data)
    print(binary_data == original_binary)
    binary_data = decode_binary_message(message.data)
    print(binary_data == original_binary)
    binary_data = decode_binary_message(json.dumps(message.data))
    print(binary_data == original_binary)
    binary_data = decode_binary_message(message.serialize())
    print(binary_data == original_binary)


listen_for_message("mycroft.binary.file", receive_file)
sleep(1)
send_binary_file_message(my_file_path)


def receive_binary(message):
    print("Receiving binary data")
    binary_data = decode_binary_message(message)
    print(binary_data == original_binary)


listen_for_message("mycroft.binary.data", receive_binary)
sleep(1)
send_binary_data_message(original_binary)
