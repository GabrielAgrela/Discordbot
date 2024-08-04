import yt_dlp
from pydub import AudioSegment
import os
import uuid

class ManualSoundDownloader:
    def tiktok_to_mp3(url, output_dir='.', custom_filename=None, time_limit=None):
        # Set up yt-dlp options
        def sanitize_title(title):
            if len(title) > 30:
                return title[:27] + '...' + str(uuid.uuid4())[:3]
            return title

        # Download the video and extract audio
        with yt_dlp.YoutubeDL() as ydl:
            info_dict = ydl.extract_info(url, download=False)
            title = sanitize_title(info_dict.get('title', ''))
            mp3_filename = f"{title}.mp3"
            mp3_filepath = os.path.join(output_dir, mp3_filename)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': mp3_filepath,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # If time_limit is provided, trim the audio
        if time_limit:
            audio = AudioSegment.from_mp3(mp3_filepath)
            trimmed_audio = audio[:time_limit * 1000]  # time_limit is in seconds, pydub uses milliseconds
            trimmed_audio.export(mp3_filepath, format="mp3")
        
        return mp3_filename