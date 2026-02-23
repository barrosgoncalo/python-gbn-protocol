import queue
import threading
from sys import *
from socket import *

import requests

BUFFER_SIZE = 1024

MOVIE_HEADER_SIZE = 2
TRACK_HEADER_SIZE = 5

# producer task
def producer(buffer, url, movie_name, track):
    with socket(family=AF_INET, type=SOCK_STREAM) as sck:
        host, port = parse_url(url)
        sck.connect((host, port))

        send_manifest_request(sck, movie_name)
        raw_data = read_full_response(sck).decode()

    lines = extract_http_body(raw_data).split('\n')
    req_url = build_request_url(url, movie_name, track)

    num_seg = int(lines[MOVIE_HEADER_SIZE + 5 - 1])
    offset = MOVIE_HEADER_SIZE + (parseTrackNumber(track) * TRACK_HEADER_SIZE) + ((parseTrackNumber(track) - 1) * num_seg)

    for s in range(offset, offset + num_seg):
        segment = fetch_segment(lines, req_url, s)
        buffer.put(segment.content)
    buffer.put(None) # sentinel


def parseTrackNumber(track_name):
    return int(track_name.split('.')[0].split('-')[1])

# consumer task
def consumer(buffer):
    player_socket = socket()
    player_socket.connect(('localhost', 8000))
    while True:
        # retrieve an item
        item = buffer.get()
        if item is None:
            break
        player_socket.send(item)
    player_socket.close()

def arg_validation():
    if len(argv) != 4:
        print('Error: wrong number of arguments')
        exit(1)

def parse_url(url):
    host, port = (url.split('/')[2]).split(':')
    return host, int(port)

def send_manifest_request(sck, movie_name):
    request = f"GET ./{movie_name}/manifest.txt HTTP/1.0\r\n\r\n"
    sck.send(request.encode())

def read_full_response(sck):
    recv_data = sck.recv(BUFFER_SIZE)
    data = b''
    while recv_data:
        data += recv_data
        recv_data = sck.recv(BUFFER_SIZE)
    return data

def extract_http_body(response):
    header_end = fetch_header(response)
    return response[header_end + 4:]

def fetch_header(response):
    header_end = response.find("\r\n\r\n")
    if header_end == -1:
        print("Invalid HTTP")
        exit(1)
    return header_end

def fetch_segment(lines, url, s):
    offset_str, size_str = lines[s].split()
    offset, size = int(offset_str), int(size_str)
    byte_end = size + offset - 1
    headers = {"Range": f"bytes={offset}-{byte_end}"}  # request header
    return requests.get(url, headers=headers)  # segment download

def build_request_url(url, movie_name, track_name):
    host, port = parse_url(url)
    return f'http://{host}:{port}/{movie_name}/{track_name}'



def main():

    # create a shared queue
    buffer = queue.Queue(maxsize = 10)

    arg_validation()

    _, url, movie_name, track = argv

    # create a producer thread
    producer_thread = threading.Thread(target=producer, args=(buffer,url, movie_name, track))
    # create a consumer thread
    consumer_thread = threading.Thread(target=consumer, args=(buffer,))
    # start the producer thread
    producer_thread.start()
    # start the producer thread
    consumer_thread.start()

    producer_thread.join()
    consumer_thread.join()


if __name__ == '__main__':
    main()