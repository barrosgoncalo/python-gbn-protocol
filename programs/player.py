import socket
import subprocess

# Start a socket listening for connections on 0.0.0.0:8000
#(0.0.0.0 means all interfaces)
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 8000))
server_socket.listen(0)

# Accept a single connection and make a file-like object out of it
connection = server_socket.accept()[0].makefile('rb')

try:
    # Run a viewer with an appropriate command line. Adapt cmdline according to
    # your operating system and video player
    # Mac example: alias vlc='/Applications/VLC.app/Contents/MacOS/VLC'
    # cmdline = '/Applications/VLC.app/Contents/MacOS/VLC --demux h264 -'
    # Windows example: cmdline = 'c:/Users/pedro/Bin/MPlayer/mplayer.exe -ni -'
    cmdline = 'mplayer -'

    player = subprocess.Popen(cmdline.split(), stdin=subprocess.PIPE)

    while True:
        # Repeatedly read 1k of data from the connection and write it to
        # the media player's stdin
        data = connection.read(1024)
        if not data:
            break
        player.stdin.write(data)
finally:
    connection.close()
    server_socket.close()
    player.terminate()