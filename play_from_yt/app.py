from flask import Flask, render_template, request
from googleapiclient.discovery import build
import subprocess
import yt_dlp
import threading
import os

# Directory to store downloaded songs
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

app = Flask(__name__)

# Replace this with your actual API key
YOUTUBE_API_KEY = "AIzaSyAQMBxoyjQTeJyM6KP-om0F-qO1B0cevXU"

def search_youtube(query, max_results=5):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=max_results
    )
    response = request.execute()

    results = []
    for item in response['items']:
        video_id = item['id']['videoId']
        title = item['snippet']['title']
        thumbnail = item['snippet']['thumbnails']['medium']['url']
        url = f"https://www.youtube.com/watch?v={video_id}"
        results.append({
            'title': title,
            'thumbnail': thumbnail,
            'url': url
        })

    return results

def download_youtube_audio(youtube_url, output_file="output.wav"):
    """
    Extracts audio from a YouTube video and saves it as a WAV file
    without downloading the video.
    """
    # Configure yt-dlp to fetch the best audio stream URL
    ydl_opts = {
        'format': 'bestaudio/best',  # Best audio quality
        'quiet': True,               # Suppress logs
        'extract_audio': True,       # Extract audio (not strictly needed here)
    }

    # Get the direct audio stream URL
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        audio_url = info['url']  # Direct stream URL of the audio

    # Stream the audio directly to ffmpeg and save as WAV
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', audio_url,           # Input stream URL
        '-vn',                     # Disable video (audio only)
        '-acodec', 'pcm_s16le',    # Audio codec for WAV format
        '-ar', '44100',            # Set audio sample rate to 44.1kHz (WAV standard)
        '-ac', '2',                # Set audio channels to stereo (2 channels)
        '-y',                      # Overwrite output if exists
        output_file
    ]

    # Run FFmpeg
    subprocess.run(ffmpeg_cmd)

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    if request.method == "POST":
        query = request.form.get("query")
        if query:
            results = search_youtube(query)
    return render_template("index.html", results=results)

@app.route("/select", methods=["POST"])
def select():
    title = request.form.get("title")
    url = request.form.get("url")
    print(f"Selected video: {title} - {url}")

    # Generate a safe filename for the song (now saving as .wav)
    filename = os.path.join(DOWNLOAD_DIR, f"{title.replace(' ', '_')}.wav")

    # Download the selected YouTube audio in a separate thread to avoid blocking Flask
    threading.Thread(target=download_youtube_audio, args=(url, filename)).start()

    return render_template("selected.html", title=title, url=url, filename=filename)

if __name__ == "__main__":
    app.run(debug=True)
