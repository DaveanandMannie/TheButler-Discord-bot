import sqlite3
import discord
from discord import Embed, Member
from discord.ext.commands import Cog, Bot, command, Context
from storage import Database


class GamingStack(Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.db: Database.Manager = Database.Manager(database_name='ButlerDB')

    @command()
    async def _add_all_users(self, ctx: Context) -> None:
        member: Member
        for member in ctx.guild.members:
            try:
                self.db.add_user(username=member.name, nickname=member.nick, discord_id=member.id)
                await ctx.send(f'{member.name} added to db')
            except sqlite3.IntegrityError:
                await ctx.send(f'User: {member.name} in db already')
            await ctx.send('TASK COMPLETED: Check stdout')

    @command(name='createstack', aliases=['createping', 'cs'])
    async def create_mention_group(self, ctx: Context, group_name: str) -> None:
        """Creates a stack: value-1 -> stack name"""
        try:
            self.db.create_mention_group(mention_group_name=group_name)
            create_stack_embed: Embed = Embed(
                title=f'Stack {group_name} has been created.',
                description=f'Created by {ctx.author.mention}',
                color=discord.Color.purple()
            )
            await ctx.send(embed=create_stack_embed)
        except sqlite3.IntegrityError:
            create_stack_embed_error: Embed = Embed(title='Stack already exists bozo',
                                                    description=f'{ctx.author.mention}')
            await ctx.send(embed=create_stack_embed_error)
            await ctx.send('https://tenor.com/bOm6q.gif')

    @command(name='add2stack', aliases=['a2s'])
    async def add_to_mention_group(self, ctx: Context, member_namesake: str, stack_name: str) -> None:
        """stack:value-1:member OR nickname, value-2:stack name"""
        stack_tuple: tuple[int, str] = self.db.get_mention_group_data(name=stack_name)
        member_tuple: tuple[int, str, str, int] = self.db.get_member_data(name=member_namesake)
        if member_tuple is None:
            embed_1: Embed = Embed(title='Yikes', color=discord.Color.purple(),
                                   description='That user does not exist or has not been added to the database.')
            await ctx.send(embed=embed_1)
            await ctx.send('https://tenor.com/bOm6q.gif')
        elif stack_tuple is None:
            embed_2: Embed = Embed(title='Yikes', color=discord.Color.purple(),
                                   description='That stack does not exist or has not been added to the database.')
            await ctx.send(embed=embed_2)
            await ctx.send('https://tenor.com/bOm6q.gif')
        else:
            try:
                self.db.add_to_mention_group(user_id=member_tuple[0], group_id=stack_tuple[0])
                success_embed: Embed = Embed(
                    title=f'{member_tuple[1]} has been added to the {stack_tuple[1]}',
                    description="Hopefully it is Dave's code so who knows",
                    color=discord.Color.purple()
                )
                await ctx.send(embed=success_embed)
            except sqlite3.IntegrityError:
                failure_embed: Embed = Embed(
                    title='Yikes',
                    description=f"{member_tuple[1]} is in the {stack_tuple[1]} stack already bozo",
                    color=discord.Color.purple()
                )
                await ctx.send(embed=failure_embed)
                await ctx.send('https://tenor.com/bOm6q.gif')

    @command(name='@', aliases=['ping'])
    async def ping_stack(self, ctx: Context, stack_name: str) -> None:
        """Pings all members in a stack: value-1 -> stack Name"""
        try:
            member_list: list[int] = self.db.get_stack_members_ids(stack_name=stack_name)
            member: int
            stack_message: str = ''
            for member in member_list:
                stack_message += f'<@!{member}>'
            ping_embed: Embed = Embed(title=f'Assembling the {stack_name} stack, Ready up!',
                                      description=stack_message,
                                      color=discord.Color.purple())
            await ctx.send(embed=ping_embed)
            await ctx.send(stack_message)
        except Database.StackNotFoundError:
            error_embed: Embed = Embed(title="That's not a correct stack bozo", color=discord.Color.purple())
            await ctx.send(embed=error_embed)
            await ctx.send('https://tenor.com/bOm6q.gif')

    @command(name='stacks')
    async def get_all_stacks(self, ctx: Context) -> None:
        """Shows all stacks"""
        stack_embed: Embed = Embed(
            title="List of of stacks, personally I think they're all bozos",
            description='\n'.join(self.db.get_mention_names()),
            color=discord.Color.purple()
        )
        await ctx.send(embed=stack_embed)

    @command(name='show')
    async def show_members_stack(self, ctx: Context, stack_name) -> None:
        """Shows all users in a particular stack: value1: stack name """
        member_stack_embed: Embed = Embed(
            title=f'{stack_name}',
            description='\n'.join(self.db.get_stack_members(stack_name=stack_name)),
            color=discord.Color.purple()
        )
        await ctx.send(embed=member_stack_embed)
