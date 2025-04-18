import subprocess

def listen():
    subprocess.run([
        "ffplay",
        "-protocol_whitelist", "file,udp,rtp",
        "-i", "session_1.sdp"
    ])

if __name__ == "__main__":
    listen()
