"""Analyse packet loss from the captured packets."""
import struct


capture_file = "Captures/session_c20_f10.pcap"
print(f"Analyzing packet loss for {capture_file}")

with open(capture_file, "rb") as f:  # Open in binary mode
    data = f.read()

# Process the data here to extract sequence numbers or analyze packet loss
frame_numbers = []

#has only the header
for i in range(0, len(data), 12):  # RTP header is 12 bytes
    rtp_header = struct.unpack("!BBHII", data[i:i + 12])
    frame_numbers.append(rtp_header[2])  # Sequence number

# Sort packet sequence numbers in ascending order
frame_numbers.sort()

total_frames = len(frame_numbers)
lost_frames = 0

for i in range(1, total_frames):
    diff = frame_numbers[i] - frame_numbers[i - 1]
    if diff > 1:  # There's a gap
        lost_frames += diff - 1

packet_loss = (lost_frames / total_frames) * 100
print(f"Total frames: {total_frames}, Lost frames: {lost_frames}, Packet loss: {packet_loss:.2f}%")

# Write on a file without deleting the previous content

channel = "20"
frame_duration = "10"

with open("statistics.txt", "a") as f:
    f.write(f"c: {channel}, f: {frame_duration}, total_packets: {total_frames}, lost_packets: {lost_frames}, packet_loss: {packet_loss:.2f}%\n")
