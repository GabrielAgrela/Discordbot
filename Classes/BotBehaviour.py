import asyncio
import time
import discord
import random
from Classes.SoundDownloader import SoundDownloader
import os
import glob
import threading
from Classes.AudioDatabase import AudioDatabase
from Classes.PlayHistoryDatabase import PlayHistoryDatabase
from Classes.TTS import TTS

from discord.ui import Button, View

class ReplayButton(Button):
    def __init__(self, bot_behavior, audio_file, **kwargs):
        super().__init__(**kwargs)
        self.bot_behavior = bot_behavior
        self.audio_file = audio_file

    async def callback(self, interaction):
        # Delete the last message
        await interaction.response.defer()
        # Then start the audio playback
        asyncio.create_task(self.bot_behavior.play_audio(interaction.message.channel, self.audio_file, interaction.user.name))

class ReplayView(View):
    def __init__(self, bot_behavior, audio_file):
        super().__init__()
        # Add the replay button to the view
        self.add_item(ReplayButton(bot_behavior, audio_file, label=None, emoji="🔁", style=discord.ButtonStyle.primary))
        # Add the play random button to the view
        self.add_item(PlayRandomButton(bot_behavior, label=None, emoji="🎲", style=discord.ButtonStyle.primary))
        # Add the play slap button to the view
        self.add_item(PlaySlapButton(bot_behavior, label=None, emoji="👋", style=discord.ButtonStyle.primary))

class PlayRandomButton(Button):
    def __init__(self, bot_behavior, **kwargs):
        super().__init__(**kwargs)
        self.bot_behavior = bot_behavior

    async def callback(self, interaction):
        await interaction.response.defer()
        # Start the audio playback
        asyncio.create_task(self.bot_behavior.play_random_sound(interaction.user.name))

class PlaySlapButton(Button):
    def __init__(self, bot_behavior, **kwargs):
        super().__init__(**kwargs)
        self.bot_behavior = bot_behavior

    async def callback(self, interaction):
        await interaction.response.defer()
        # Start the slap sound playback
        asyncio.create_task(self.bot_behavior.play_audio("", "slap.mp3", "admin"))



class BotBehavior:
    def __init__(self, bot, ffmpeg_path):
        self.bot = bot
        self.ffmpeg_path = ffmpeg_path
        
        self.temp_channel = ""
        self.last_channel = {}
        self.playback_done = asyncio.Event()
        # Usage example
        self.script_dir = os.path.dirname(__file__)  # Get the directory of the current script
        self.db_path = os.path.join(self.script_dir, "../Data/soundsDB.csv")
        self.ph_path = os.path.join(self.script_dir, "../Data/play_history.csv")
        self.db = AudioDatabase(self.db_path, self.bot)
        self.player_history_db = PlayHistoryDatabase(self.ph_path,self.db, self.bot)
        self.sound_downloader = SoundDownloader(self.db)
        self.TTS = TTS(self,bot)
        

    def get_largest_voice_channel(self, guild):
        """Find the voice channel with the most members."""
        largest_channel = None
        largest_size = 0
        for channel in guild.voice_channels:
            if len(channel.members) > largest_size:
                largest_channel = channel
                largest_size = len(channel.members)
        return largest_channel

    async def disconnect_all_bots(self, guild):
        if self.bot.voice_clients:
            for vc_bot in self.bot.voice_clients:
                if vc_bot.guild == guild:
                    await vc_bot.disconnect()

    async def play_audio(self, channel, audio_file,user, is_entrance=False, is_tts=False, extra=""):
        self.player_history_db.add_entry(audio_file, user)
        #make channel be the current channel
        if channel == "":
            channel = self.temp_channel
        self.temp_channel = channel
        voice_client = discord.utils.get(self.bot.voice_clients, guild=channel.guild)
        bot_channel = discord.utils.get(self.bot.guilds[0].text_channels, name='bot')
        if bot_channel and not is_entrance and not is_tts:
            if extra != "": 
                embed = discord.Embed(
                    title=f"🔊 **{audio_file.split('/')[-1].replace('.mp3', '')}** 🔊",
                    description= f"Similarity: {extra}%",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title=f"🔊 **{audio_file.split('/')[-1].replace('.mp3', '')}** 🔊",
                    color=discord.Color.red()
                )
            #delete last message
            view = ReplayView(self, audio_file)
            # Add the view to the message
            if audio_file.split('/')[-1].replace('.mp3', '') != "slap":
                await bot_channel.send(embed=embed, view=view)
                
            
            
        audio_file_path = f"D:/eu/sounds/{audio_file}"
        voice_client = discord.utils.get(self.bot.voice_clients, guild=channel.guild)

        if voice_client:
            # Move to new channel if needed and stop current audio if playing
            if voice_client.channel != channel:
                await voice_client.move_to(channel)
            if voice_client.is_playing():
                voice_client.stop()
        else:
            try:
                voice_client = await channel.connect()
            except Exception as e:
                print(f"Error connecting to channel: {e}")
                return

        self.playback_done.clear()

        def after_playing(error):
            if error:
                print(f'Error in playback: {error}')
            print("playing3")
            self.playback_done.set()

        try:
            print(f"Current WebSocket latency: {self.bot.latency*1000:.2f} ms")
            voice_client.play(
                discord.FFmpegPCMAudio(executable=self.ffmpeg_path, source=audio_file_path),
                after=after_playing
            )
        except Exception as e:
            print(f"An error occurred: {e}")
            await voice_client.disconnect()

        await self.playback_done.wait()




    async def update_bot_status_once(self):
        if hasattr(self.bot, 'next_download_time'):
            time_left = self.bot.next_download_time - time.time()
            if time_left > 0:
                minutes = round(time_left / 60)
                if minutes < 2:
                    activity = discord.Activity(name=f'explosion imminent!!!', type=discord.ActivityType.playing)
                else:
                    activity = discord.Activity(name=f'an explosion in ~{minutes}m', type=discord.ActivityType.playing)
                await self.bot.change_presence(activity=activity)



    async def update_bot_status(self):
        while True:
            await self.update_bot_status_once()
            await asyncio.sleep(60)

    async def play_sound_periodically(self):
        while True:
            try:
                for guild in self.bot.guilds:
                    channel = self.get_largest_voice_channel(guild)
                    #if channel is not None:
                        #await self.disconnect_all_bots(guild)
                sleep_time = random.uniform(0, 800)
                self.bot.next_download_time = time.time() + sleep_time
                while time.time() < self.bot.next_download_time:
                    await self.update_bot_status_once()
                    await asyncio.sleep(60)
                # Playing the audio after ensuring that time_left has reached 0 or less
                for guild in self.bot.guilds:
                    channel = self.get_largest_voice_channel(guild)
                    if channel is not None:
    
                        random_file = self.db.get_random_filename()
                        
                        await self.play_audio(channel, random_file, "periodic function")
                    else:
                        await asyncio.sleep(sleep_time)
            except Exception as e:
                print(f"An error occurred: {e}")
                await asyncio.sleep(60) # if an error occurred, try again in 1 minute

    async def play_random_sound(self, user="admin"):
        try:
            for guild in self.bot.guilds:
                channel = self.get_largest_voice_channel(guild)
                if channel is not None:
                    asyncio.create_task(self.play_audio(channel, self.db.get_random_filename(),user))
        except Exception as e:
            print(f"An error occurred: {e}")

    async def download_sound_periodically(self):
        while True:
            thread = threading.Thread(target=self.sound_downloader.download_sound)
            thread.start()
            await asyncio.sleep(50)
    
    async def play_request(self, id, user):
        distance, filename = self.db.get_most_similar_filename(id)
        for guild in self.bot.guilds:
            channel = self.get_largest_voice_channel(guild)
            if channel is not None:
                asyncio.create_task(self.play_audio(channel, filename,user,extra=distance))
                #bot_channel = discord.utils.get(self.bot.guilds[0].text_channels, name='bot')
                #if bot_channel:
                    #await bot_channel.send(f"🎶{distance}🎶 ")

    async def change_filename(self, oldfilename, newfilename):
        print("oldfilename: ", oldfilename, " newfilename: ", newfilename)
        await self.db.modify_filename(oldfilename, newfilename)
                    
    async def tts(self,behavior, speech):
        print("stt: ", speech)
        await self.TTS.save_as_mp3(speech)     
    
    

    async def list_sounds(self):
        try:
            for guild in self.bot.guilds:
                channel = self.get_largest_voice_channel(guild)
                if channel is not None:
                    bot_channel = discord.utils.get(self.bot.guilds[0].text_channels, name='bot')
                    
                    if bot_channel:
                        with open(self.db_path, 'rb') as file:
                            # Sending the .csv file to the chat
                            await bot_channel.send(file=discord.File(file, 'Data/soundsDB.csv'))
                        print(f"csv sent to the chat.")
                        return
                    
        except Exception as e:
            print(f"An error occurred: {e}")



    

