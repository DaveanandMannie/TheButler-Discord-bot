import sqlite3
import discord
from discord.ext import commands
from discord.ext.commands import Context
import os
import logging
from storage import Database

# ------------ funny messages --------------- #
correct: str = "... Hopefully. It is Dave's code so who knows 🤷‍♂️"
incorrect: str = "Dave's code is shit and let him know"
maybe: str = "or Dave's code is shit 🤷‍♂️"

# -------------- database -------------------#
butler_db: Database.Manager = Database.Manager(database_name='ButlerDB')
# butler_db.build_from_schema()

# ---------------- logging -------------------#
handler: logging.Handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# --------------- environment ---------------- #
with open('secrets.txt') as secrets:
    for line in secrets:
        key, value = line.strip().split('=')
        os.environ[key] = value
TOKEN: str = os.environ['DISCORD_TOKEN']

# -------------- intent management --------------#
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# bot config
butler = commands.Bot(command_prefix='!', intents=intents)


# -----------------stack operations---------------- #
@butler.command()
async def add_all_users(ctx: Context) -> None:
    """Add all members of the server to the user table"""
    member: discord.Member
    for member in ctx.guild.members:
        try:
            butler_db.add_user(username=member.name, nickname=member.nick, discord_id=member.id)
            await ctx.send(f'{member.name}added to db')
        except sqlite3.IntegrityError:
            await ctx.send(f'User: {member.name} in db already')
    await ctx.send('TASK COMPLETED: check stdout')


@butler.command(name='createstack')
async def create_mention_group(ctx: Context, name: str) -> None:
    """Creates a stack: value-1 -> stack name"""
    try:
        butler_db.create_mention_group(mention_group_name=name)
        await ctx.send(f'stack: {name} has been created. {correct}')
    except sqlite3.IntegrityError as error:
        await ctx.send(f"error:{error}: {incorrect}")


@butler.command('add2stack')
async def add_to_mention_group(ctx: Context, member_namesake: str, stack_name: str) -> None:
    """Adds member to a stack: value-1 -> member username OR nickname, value-2 -> stack name,"""
    stack_tuple: tuple[int, str] = butler_db.get_mention_group_data(name=stack_name)
    member_tuple: tuple[int, str, str, int] = butler_db.get_member_data(name=member_namesake)

    if member_tuple is None:
        await ctx.send(f"Yikes: That user does not exist or has not been added to the database {maybe}")
    elif stack_tuple is None:
        await ctx.send(f"Yikes: That stack does not exist or has not been added to the database {maybe}")
    else:
        try:
            butler_db.add_to_mention_group(user_id=member_tuple[0], group_id=stack_tuple[0])
            await ctx.send(
                f"{member_tuple[1]} has been added the {stack_tuple[1]} stack{correct}"
            )
        except sqlite3.IntegrityError:
            await ctx.send(f"{member_tuple[1]} is in the {stack_tuple[1]} stack already{correct}")


@butler.command('@')
async def ping_stack(ctx: Context, stack_name: str) -> None:
    """Pings all members in a stack: value-1 -> stack name"""
    stack_message: str = f'Assembling the {stack_name} stack, Ready up! '
    member_list: list[int] = butler_db.get_stack_members(stack_name=stack_name)
    member: int
    for member in member_list:
        stack_message += f'<@!{member}>'
    await ctx.send(stack_message)


butler.load_extension('cogs.music')


butler.run(TOKEN)

# client.run(TOKEN, log_handler=handler, log_level=logging.DEBUG, root_logger=True)
