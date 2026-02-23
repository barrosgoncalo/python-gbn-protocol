from socket import *
from sys import *

def arg_validation():
    if len(argv) != 4:
        print("Error: wrong number of arguments")
        exit(1)

BUFFER_SIZE = 1024

def main():
    arg_validation()

    _, url, movie_name, results_file_name = argv

    # parse_url
    addr, port = (url.split('/')[2]).split(':')


    sck = socket(family=AF_INET, type=SOCK_STREAM)
    sck.connect((addr, int(port)))

    request = f'GET ./{movie_name}/manifest.txt HTTP/1.0\r\n\r\n'

    sck.send(request.encode())
    rcvd_data = sck.recv(BUFFER_SIZE)

    # manifest.txt file download

    tmp = b'' # tmp variable

    while rcvd_data:
        tmp += rcvd_data
        rcvd_data = sck.recv(BUFFER_SIZE)


    tmp_str = tmp.decode()
    header_end = tmp_str.find("\r\n\r\n")

    if header_end == -1:
        print("Invalid HTTP")
        exit(1)

    content = tmp_str[header_end + 4:]
    lines = content.split("\n")

    with open(results_file_name, "w") as rf:
        num_tracks = int(lines[1])
        num_seg = int(lines[6])
        rf.write(f"{num_tracks}\n{num_seg}\n")
        movie_header = 2
        track_header = 5
        offset = movie_header + track_header

        for t in range(num_tracks):
            total = 0
            for s in range(offset, offset + num_seg - 1):
                total += int(lines[s].split(" ")[1])
            rf.write(f"{total}\n")
            offset += track_header + num_seg

if __name__ == "__main__":
    main()
