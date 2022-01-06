import discord
import os
from discord.ext import commands
from collections import OrderedDict

with open('token') as f:
    TOKEN = f.read().strip()

levels = OrderedDict()
secret_levels = OrderedDict()

milestones = {
    '10': 'Natural Thinkers',
    '20': 'Integer Explorers',
    '30': 'Rational Defeaters',
    '40': 'Real Conquerers',
    '49': 'Complex Masters',
    'epilogue': 'Enigma Crackers',
}

with open('levels.txt') as f:
    ln = 0
    for l in f.readlines():
        level, path, answer = l.strip().split()
        levels[level] = [path, answer.split('/')[-1].split('.')[0]]
        if ln >= 50: # levels after line 50 are secret levels
            secret_levels[level] = [path, answer.split('/')[-1].split('.')[0]]
        ln += 1

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!',intents=intents)

@bot.event
async def on_ready():
    print("Ébot ready!")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send('Invalid command... Follow `!help` for the syntax')

@bot.command(name='solve',
             help='syntax: !solve <level_name> <answer>')
async def solve(ctx, level_name, answer):
    if not isinstance(ctx.channel, discord.channel.DMChannel):
        await ctx.message.delete()
        await ctx.send(f'No spoiler... DM me instead')
        return
    level_name = level_name.lower()
    if level_name not in levels:
        level_names = ', '.join(levels.keys())
        await ctx.send(f"Invalid level name\nValid level names are: `{level_names}`")
        return

    if levels[level_name][1] != answer:
        return

    guild = discord.utils.get(bot.guilds, name='Énigmapédia')
    member = discord.utils.get(guild.members, name=ctx.author.name)
    channel = discord.utils.get(guild.channels, name=level_name)

    if len(member.roles) == 1: # newly joined player
        role = discord.utils.get(guild.roles, name='reached-01')
        await member.add_roles(role)
        await member.edit(nick=f'{member.name} [01]')

    for r in member.roles:
        # only when player reaches this level will they be able to remove this reached role
        if f'reached-{level_name}' != r.name:
            continue

        await member.remove_roles(r)
        if level_name in secret_levels:
            role = discord.utils.get(guild.roles, name=f'solved-{level_name}')
            await member.add_roles(role)
            await ctx.send(f'Congratulations on beating the secret level **{level_name}**!')
            await channel.send(f'<@{member.id}> has beaten the secret level **{level_name}**! '
                               f'Nice job :partying_face:')

        elif level_name < '49':
            next_level = int(level_name) + 1
            await member.edit(nick=f'{member.name} [{next_level:02}]')
            role = discord.utils.get(guild.roles, name=f'reached-{next_level:02}')
            await member.add_roles(role)
            await ctx.send(f'Congratulations on solving level **{level_name}**!')
        elif level_name == '49':
            await member.edit(nick=f'{member.name} [Epilogue]')
            role = discord.utils.get(guild.roles, name='reached-epilogue')
            await member.add_roles(role)
            await ctx.send(f'Congratulations on solving level **{level_name}**!')
        elif level_name == 'epilogue':
            await member.edit(nick=f'{member.name} 🏅')

        if level_name in milestones:
            mn = milestones[level_name]
            role = discord.utils.get(guild.roles, name=mn)
            await member.add_roles(role)
            await ctx.send(f'Now you are part of {mn}! Congrats :tada:')
            await channel.send(f'<@{member.id}> has beaten level **{level_name}** and '
                               f'become one of **@{mn}**! Congrats :tada:')
        break


@bot.command(name='find',
             help='syntax: !find <level_name> <answer>')
async def find(ctx, level_name, answer):
    if not isinstance(ctx.channel, discord.channel.DMChannel):
        await ctx.message.delete()
        await ctx.send(f'No spoiler... DM me instead')
        return
    level_name = level_name.lower()
    if level_name not in secret_levels:
        level_names = ', '.join(secret_levels.keys())
        await ctx.send(f"Invalid level name\nValid level names are: `{level_names}`")
        return

    # format: /xxx/<answer>.htm OR /xxx/<answer>/xxx.htm
    if secret_levels[level_name][0].split('/')[2].split('.')[0] != answer:
        return

    guild = discord.utils.get(bot.guilds, name='Énigmapédia')
    member = discord.utils.get(guild.members, name=ctx.author.name)

    for r in member.roles:
        if level_name in r.name:
            break
    else:
        role = discord.utils.get(guild.roles, name=f'reached-{level_name}')
        await member.add_roles(role)
        await ctx.send(f'You found the secret level **{level_name}**!')


@bot.command(name='recall',
             help='syntax: !recall <level_name>')
async def recall(ctx, level_name):
    if not isinstance(ctx.channel, discord.channel.DMChannel):
        await ctx.message.delete()
        await ctx.send(f'No spoiler... DM me instead')
        return
    level_name = level_name.lower()
    if level_name not in levels:
        level_names = ', '.join(levels.keys())
        await ctx.send(f"Invalid level name\nValid level names are: `{level_names}`")
        return

    guild = discord.utils.get(bot.guilds, name='Énigmapédia')
    member = discord.utils.get(guild.members, name=ctx.author.name)

    if len(member.roles) == 1: # newly joined player
        role = discord.utils.get(guild.roles, name='reached-01')
        await member.add_roles(role)
        await member.edit(nick=f'{member.name} [01]')

    output = f'https://enigmapedia.xyz{levels[level_name][0]}'
    for r in member.roles:
        if level_name in secret_levels:
            if r.name == f'reached-{level_name}' or r.name == f'solved-{level_name}':
                await ctx.send(output)
                return
        else:
            if r.name == 'Enigma Crackers':
                await ctx.send(output)
                return
            if r.name.startswith('reached-'):
                reached_level = r.name.split('reached-')[1]
                if reached_level == 'epilogue' or \
                        (reached_level not in secret_levels and int(reached_level) >= int(level_name)):
                    await ctx.send(output)
                    return

bot.run(TOKEN)
