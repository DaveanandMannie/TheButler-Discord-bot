import asyncio

import discord
from discord.ext import commands
import os
from cogs.gaming_stacks import GamingStack
from cogs.music import Music

# --------------- environment ---------------- #
with open('secrets.txt') as secrets:
    for line in secrets:
        key, value = line.strip().split('=')
        os.environ[key] = value
TOKEN: str = os.environ['DISCORD_TOKEN']

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
butler = commands.Bot(command_prefix='!', intents=intents)


# butler.run(TOKEN)
async def main() -> None:
    async with butler:
        await butler.add_cog(GamingStack(butler))
        await butler.add_cog(Music(butler))
        await butler.start(TOKEN)
asyncio.run(main())