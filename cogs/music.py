import asyncio
from asyncio import Queue
import os
import time
import discord
from discord import PCMVolumeTransformer, FFmpegPCMAudio, Embed, Member, VoiceClient
# from discord.ext import commands
from discord.ext.commands import Cog, Bot, command
from discord.ext.commands import Context
# from collections import deque

import yt_dlp

format_options: dict = {
    'format': 'bestaudio',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': True,
    'quiet': False,
    'no_warnings': False,
    'default_search': 'auto',
    'throttledratelimit': 300,
    'ratelimit': 100,
}
ffmpeg_options: dict = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

youtube_dl = yt_dlp.YoutubeDL(format_options)


class YTSource(PCMVolumeTransformer):
    def __init__(self, source, *, data: dict, requester: Member):
        super().__init__(source)
        self.data = data
        self.requester = requester
        self.title = data.get('title')
        self.url = data.get('url')
        self.web_url = data.get('webpage_url')
        self.duration = self.convert_duration(data.get('duration'))

    @staticmethod
    def convert_duration(duration: int) -> str:
        minutes, seconds = divmod(duration, 60)
        return f"{minutes}m : {seconds}s"

    @classmethod
    async def from_url(cls, ctx: Context, url: str, *, loop=None, download=False):
        loop = loop or asyncio.get_event_loop()

        data = await loop.run_in_executor(None, lambda: youtube_dl.extract_info(url, download=download))
        if 'entries' in data:  # ensure only the first item in a playlist is used
            data = data['entries'][0]
        filename = data['url']
        return cls(FFmpegPCMAudio(filename, **ffmpeg_options), data=data, requester=ctx.author)


# TODO: create a separate event loop for url extraction
class Music(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.queue: Queue = Queue(maxsize=7)
        self.current = None

    @command(name='add2q', aliases=['add', 'a2q'])
    async def enqueue(self, ctx: Context, url: str) -> None:
        async with ctx.typing():
            player = await YTSource.from_url(ctx, url=url, loop=self.bot.loop, download=False)
            await self.queue.put(player)
            embed: Embed = Embed(
                title='Queue: add',
                description=f'{player.title} added by {player.requester}.\n{player.duration}',
                color=discord.Colour.purple()
            )
            await ctx.send(embed=embed)

    @command(name='clearq', aliases=['clear', 'deleteall'])
    async def clear_queue(self, ctx: Context) -> None:
        self.queue = Queue(maxsize=7)
        embed: Embed = Embed(title='Queue: cleared', color=discord.Colour.purple())
        await ctx.send(embed=embed)

    @command(name='queue', aliases=['q', 'upnext'])
    async def view_queue(self, ctx: Context) -> None:
        tracks = []
        while not self.queue.empty():
            track = await self.queue.get()
            tracks.append(track)
        description = '\n\n'.join(
            [f'{index + 1} : {track.title} added by {track.requester}. {track.duration}'
             for index, track in enumerate(tracks)]
        )
        embed: Embed = Embed(title="Queue", description=description, color=discord.Colour.purple())
        await ctx.send(embed=embed)

    @command(name="nowplaying", aliases=['np', 'playing', 'track'])
    async def now_playing(self, ctx: Context):
        np_embed: Embed = Embed(
            title='Now playing',
            description=f'{self.current.title} added by {self.current.requester}.\n{self.current.duration}',
            color=discord.Colour.purple()
        )
        await ctx.send(embed=np_embed)

    @command(name='play')
    async def play(self, ctx: [Context, Context.voice_client]):
        if self.queue.empty():
            await asyncio.sleep(120)
            if self.queue.empty():
                await ctx.send(f'Queue is empty Bozo {ctx.author.mention}')
                await ctx.send('https://tenor.com/byaam.gif')
                await ctx.voice_client.disconnect()
                return
        track = await self.queue.get()
        self.current = track
        embed: Embed = Embed(
            title='Now playing',
            description=f'{track.title} added by {track.requester}.\n{track.duration}',
            color=discord.Colour.purple()
        )
        await ctx.send(embed=embed)
        if not ctx.voice_client.is_playing():
            await ctx.voice_client.play(track, after=lambda e: self.bot.loop.create_task(self.play(ctx)))

    @command(name='next', aliases=['n', 'skip'])
    async def play_next(self, ctx: [Context, VoiceClient]) -> None:
        if ctx.voice_client is None:
            await ctx.send("I'm not even there bozo\nhttps://tenor.com/bOm6q.gif")
            return
        if self.queue.empty():
            await ctx.send('Nothing in queue bozo\nhttps://tenor.com/bOm6q.gif')
            return
        ctx.voice_client.stop()

    @command(name='leave')
    async def leave(self, ctx: Context) -> None:
        if ctx.voice_client is None:
            await ctx.send(f"I'm not even there bozo {ctx.author.mention}\nhttps://tenor.com/bOm6q.gif")
            return
        await ctx.send('Until next time\nhttps://tenor.com/byaam.gif')
        await ctx.voice_client.disconnect(force=True)

    @play.before_invoke
    async def ensure_voice(self, ctx) -> None:
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send(f'Join a call you bozo {ctx.author.mention}')


# -------------- intent management --------------##
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# bot config
# TODO: remove and integrate with main
butler = Bot(command_prefix='!', intents=intents)

with open(r"E:\Discord\TheButler\secrets.txt") as secrets:
    for line in secrets:
        key, value = line.strip().split('=')
        os.environ[key] = value
TOKEN: str = os.environ['DISCORD_TOKEN']


async def main():
    async with butler:
        await butler.add_cog(Music(butler))
        await butler.start(TOKEN)


asyncio.run(main())
