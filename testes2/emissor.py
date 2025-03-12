import subprocess

input_file = "audio.mp3"
multicast_address = "rtp://239.255.0.1:12345"

ffmpeg_cmd = [
    "ffmpeg",
    "-re",                   # Lê na velocidade real
    "-i", input_file,        # Arquivo de entrada
    "-c:a", "libopus",       # Codec Opus
    "-f", "rtp",             # Formato RTP
    "-sdp_file", "session.sdp",  # Gera arquivo SDP (opcional)
    multicast_address        # Endereço multicast
]

subprocess.run(ffmpeg_cmd)