import subprocess
import yt_dlp

def download_youtube_audio(youtube_url, output_file="output.mp3"):
    """
    Extracts audio from a YouTube video and saves it as an MP3 file
    without downloading the video.
    """
    # Configure yt-dlp to fetch the best audio stream URL
    ydl_opts = {
        'format': 'bestaudio/best',  # Best audio quality
        'quiet': True,               # Suppress logs
        'extract_audio': True,       # Extract audio (not strictly needed here)
        'audio_format': 'mp3',       # Convert to MP3 (optional)
    }

    # Get the direct audio stream URL
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        audio_url = info['url']  # Direct stream URL of the audio

    # Stream the audio directly to ffmpeg and save as MP3
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', audio_url,          # Input stream URL
        '-vn',                    # Disable video (audio only)
        '-c:a', 'libmp3lame',     # Encode as MP3
        '-q:a', '2',              # Quality (0=best, 9=worst)
        '-y',                     # Overwrite output if exists
        output_file
    ]

    # Run FFmpeg
    subprocess.run(ffmpeg_cmd)

# Example usage
youtube_url = "https://www.youtube.com/watch?v=a5uQMwRMHcs"
download_youtube_audio(youtube_url, "instant_crush.mp3")