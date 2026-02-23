import time
from socket import *
from sys import  *

import requests

BUFFER_SIZE = 1024

MOVIE_HEADER_SIZE = 2
TRACK_HEADER_SIZE = 5

def arg_validation():
    if len(argv) != 4:
        print("Error: wrong number of arguments")
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


def fetch_header(response):
    header_end = response.find("\r\n\r\n")
    if header_end == -1:
        print("Invalid HTTP")
        exit(1)
    return header_end


def extract_http_body(response):
    header_end = fetch_header(response)
    return response[header_end + 4:]


def build_request_url(url, movie_name, track_name):
    host, port = parse_url(url)
    return f'http://{host}:{port}/{movie_name}/{track_name}'

def download_track(segment_start_idx, segment_end_idx, manifest_lines, url):
    start = time.time()
    size = download(segment_start_idx, segment_end_idx, manifest_lines, url)
    duration = time.time() - start
    return duration, size

def download(segment_start_idx, segment_end_idx, manifest_lines, url):
    total_size = 0
    for i in range(segment_start_idx, segment_end_idx):
        offset_str, size_str = manifest_lines[i].split()
        offset, size = int(offset_str), int(size_str)
        byte_end = size + offset - 1
        headers = {"Range": f"bytes={offset}-{byte_end}"}  # request header
        video_data = requests.get(url, headers=headers) # segment download
        total_size += len(video_data.content)
    return total_size


def result_file_maker(results_file_name, lines, url, movie_name):
    with open(results_file_name, "w") as rf:
        num_tracks = int(lines[1])
        num_seg = int(lines[MOVIE_HEADER_SIZE + 5 - 1])
        offset = MOVIE_HEADER_SIZE + TRACK_HEADER_SIZE
        track_name_line = MOVIE_HEADER_SIZE

        for _ in range(num_tracks):
            download_time, download_rate = download_track(
                offset,
                offset + num_seg,
                lines,
                build_request_url(url, movie_name, lines[track_name_line]) # request url,
            )
            rf.write(f'{str(download_time)}\n{str(download_rate)}\n')

            # move to next track block
            offset += TRACK_HEADER_SIZE + num_seg
            track_name_line += num_seg + TRACK_HEADER_SIZE




def main():

    arg_validation()

    _, url, movie_name, results_file_name = argv

    with socket(family=AF_INET, type=SOCK_STREAM) as sck:
        # connect to socket
        host, port = parse_url(url)
        sck.connect((host, int(port)))
        # REQUEST for manifest file
        send_manifest_request(sck, movie_name)
        # RECEIVAL of manifest file
        raw_response = read_full_response(sck).decode()

    # extract data in lines
    lines = extract_http_body(raw_response).split("\n")

    result_file_maker(results_file_name, lines, url, movie_name)


if __name__ == "__main__":
    main()

