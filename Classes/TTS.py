import asyncio
import os
import time
import requests
from gtts import gTTS
from dotenv import load_dotenv

class TTS:
    def __init__(self, behavior, bot, filename="tts.mp3", cooldown_seconds=60):
        load_dotenv()
        self.api_key = os.getenv('EL_key')
        self.voice_id = os.getenv('EL_voice_id')
        self.filename = filename
        self.behavior = behavior
        self.bot = bot
        self.last_request_time = 0
        self.cooldown_seconds = cooldown_seconds

    def is_on_cooldown(self):
        current_time = time.time()
        return current_time - self.last_request_time < self.cooldown_seconds

    def update_last_request_time(self):
        self.last_request_time = time.time()

    async def save_as_mp3(self, text, lang, region=""):
        if region == "":
            tts = gTTS(text=text, lang=lang)
        else:
            tts = gTTS(text=text, lang=lang, tld=region)
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Sounds", self.filename))
        tts.save(path)
        for guild in self.bot.guilds:
            channel = self.behavior.get_largest_voice_channel(guild)
        await self.behavior.play_audio(channel, self.filename, "admin", is_tts=True)
        self.update_last_request_time()

    async def save_as_mp3_EL(self, text, lang="pt", region=""):
        
        if self.is_on_cooldown():
            print("Cooldown active. Please wait before making another request.")
            cooldown_message = await self.behavior.send_message(view=None, title="Não dês spam nesta merda (1/m)", description="Custa 11 euros por 2h de andre ventura fdp")
            #remove the cooldown message after 5 seconds
            await asyncio.sleep(5)
            await cooldown_message.delete()
            return

        text = text[:500]
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.7,
                "similarity_boost": 1,
                "style": 1,
                "use_speaker_boost": True
            }
        }

        response = requests.post(url, json=data, headers=headers)
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Sounds", self.filename))
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        for guild in self.bot.guilds:
            channel = self.behavior.get_largest_voice_channel(guild)
        await self.behavior.play_audio(channel, self.filename, "admin", is_tts=True)
        self.update_last_request_time()
