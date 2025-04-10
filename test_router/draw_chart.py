import matplotlib.pyplot as plt
import numpy as np

# Read data from file
with open("statistics.txt", "r") as file:
    raw_data = file.read()

# Parsing data
data = {}
histogram_data = {}
channels_set = set()
for line in raw_data.strip().split("\n"):
    parts = {p.split(": ")[0]: p.split(": ")[1] for p in line.split(", ")}
    c = int(parts["c"])
    f = int(parts["f"])
    packet_loss = float(parts["packet_loss"].strip('%')) # Convert to float
    
    if f not in data:
        data[f] = []
    if f not in histogram_data:
        histogram_data[f] = {}
    
    data[f].append((c, packet_loss))
    histogram_data[f][c] = packet_loss  # Store packet loss per channel
    channels_set.add(c)

# Ensure all frame durations have all channels (fill missing values with 0)
channels_list = sorted(channels_set)
for f in histogram_data:
    for c in channels_list:
        if c not in histogram_data[f]:
            histogram_data[f][c] = 0

# Line Chart
plt.figure(figsize=(8, 5))
for f, values in sorted(data.items()):
    values.sort()  # Ensure x-axis is sorted
    channels, packet_losses = zip(*values)
    plt.plot(channels, packet_losses, marker='o', label=f"Frame {f} ms")

plt.xlabel("Channel (c)")
plt.ylabel("Packet Loss (%)")
plt.title("Packet Loss vs. Channels for Different Frame Durations")
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.show()

# Histogram with side-by-side bars
plt.figure(figsize=(8, 5))
bar_width = 0.15  # Width of each bar
x_indices = np.arange(len(channels_list))  # X locations for the groups

for i, (f, channel_losses) in enumerate(sorted(histogram_data.items())):
    packet_losses = [channel_losses[c] for c in channels_list]  # Ensure correct order
    x_positions = x_indices + (i * bar_width)  # Shift bars to the right
    plt.bar(x_positions, packet_losses, width=bar_width, label=f"Frame {f} ms", alpha=0.7)

plt.xticks(x_indices + (bar_width * ((len(histogram_data) - 1) / 2)), channels_list)  # Center labels
plt.xlabel("Channel (c)")
plt.ylabel("Packet Loss (%)")
plt.title("Histogram of Packet Loss by Frame Duration")
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.show()