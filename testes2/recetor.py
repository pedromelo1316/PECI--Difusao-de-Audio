import subprocess

sdp_file = "session.sdp"  # Usa o arquivo SDP gerado pelo emissor

ffmpeg_cmd = [
    "ffmpeg",
    "-protocol_whitelist", "file,rtp,udp",  # Adicione 'file' aqui
    "-i", sdp_file,                         # Carrega o SDP como entrada
    "-c:a", "pcm_s16le",
    "-f", "wav",
    "pipe:1"
]

player_cmd = [
    "ffplay",
    "-nodisp",
    "-autoexit",
    "-"
]

ffmpeg = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE)
player = subprocess.Popen(player_cmd, stdin=ffmpeg.stdout)

player.communicate()