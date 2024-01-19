import discord, json, os, shutil, asyncio, youtubesearchpython.__future__, youtubesearchpython
from pytube import YouTube
from discord import app_commands, Interaction, Member, RawReactionActionEvent, VoiceClient, VoiceState
from typing import Literal, Union
from dotenv import load_dotenv

# Discord app_commands and client Init
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Constants, init vars, and Env
load_dotenv()
TOKEN = os.getenv('TOKEN')
AUDIO_FOLDER = os.getenv('AUDIO_FOLDER')
GUILD_ID = int(os.getenv('GUILD_ID'))
DEF_GUILD = discord.Object(id=GUILD_ID)

queue = []
vc = None
song_is_active = False
song_is_paused = False

# Pre load actions
if __name__ == '__main__':

    # Credit to Nick Stinemates [https://stackoverflow.com/a/185941]
    
    for filename in os.listdir(AUDIO_FOLDER):
        file_path = os.path.join(AUDIO_FOLDER, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

async def queue_handler(interaction: discord.Interaction, action: Literal['Play', 'Skip', 'Pause', 'Resume', 'Stop'], queue: list = queue):

    global song_is_active
    global song_is_paused
    global vc

    user = interaction.user
    voice_channel = interaction.user.voice.channel
    text_channel = interaction.channel
    song_name = queue[0]['song_name']
    song_link = queue[0]['song_link']

    match action:

        case 'Play':

            await music_status_channel.edit(name=song_name)

            yt = YouTube(song_link)
            audio = yt.streams.filter(only_audio = True).first().download(output_path='./music')

            if vc == None:
                vc = await voice_channel.connect()

            if not vc.is_connected():
                vc = await voice_channel.connect()
            
            vc.play(discord.FFmpegPCMAudio(executable='C:/ffmpeg/bin/ffmpeg.exe', source=audio))

            await text_channel.send(f'Loaded [{song_name}](<{song_link}>)')
            song_is_active = True
            

            while song_is_active and vc.is_playing() or song_is_paused:
                await asyncio.sleep(1)

            vc.stop()
            queue.pop(0)

            while True:
                try:
                    os.remove(audio)
                    break
                except:
                    await asyncio.sleep(1)

            if queue == []:
                await vc.disconnect()
                vc = None
                await music_status_channel.edit(name='No songs playing')
                
            song_is_active = False

            
        case 'Pause':

            if not song_is_active:
                await interaction.response.send_message('There is no song playing!', ephemeral=True)
                return
            
            if song_is_paused:
                await interaction.response.send_message('The song is already paused!', ephemeral=True)
                return

            if type(vc) != VoiceClient:
                await interaction.response.send_message('Error handling queue, please let Jade know!')
                return
            
            vc.pause()
            song_is_paused = True

            await interaction.response.send_message(f'Paused [{song_name}](<{song_link}>)!')

        case 'Skip':
            
            if not song_is_active:
                await interaction.response.send_message('There is no song playing!', ephemeral=True)
                return
            
            song_is_paused = False
            song_is_active = False

            await interaction.response.send_message(f'Skipped [{song_name}](<{song_link}>)!')

        case 'Resume':

            if not song_is_active:
                await interaction.response.send_message('There is no song playing!', ephemeral=True)
                return
            
            if not song_is_paused:
                await interaction.response.send_message('The song is already playing!', ephemeral=True)
                return
            
            if type(vc) != VoiceClient:
                await interaction.response.send_message('Error handling queue, please let Jade know!')
                return
            
            vc.resume()
            song_is_paused = False

            await interaction.response.send_message(f'Resumed [{song_name}](<{song_link}>)')

        case 'Stop':

            if not song_is_active:
                await interaction.response.send_message('There is no song playing!', ephemeral=True)
                return
            
            queue = []
            song_is_paused = False
            song_is_active = False

            await interaction.response.send_message(f'Stopped playback and cleared queue!')

@tree.command(name='play', description='Part of the sounds pack, searches for music on YouTube.', guild=DEF_GUILD)
async def search(interaction: Interaction, q: str): # <Add provider selector>

    user = interaction.user

    if user.voice == None:
        await interaction.response.send_message('You must be in a voice channel to use this command!', ephemeral=True)
        return

    if vc != None:
        if interaction.user not in vc.channel.members and song_is_active:
            await interaction.response.send_message('The bot is currently in use in another channel, please wait for that session to end.', ephemeral=True)
            return

    video_search = youtubesearchpython.__future__.VideosSearch(q, limit=1)
    res = await video_search.next()
    song_link = res['result'][0]['link']
    song_name = res['result'][0]['title']

    if queue != []:
        await interaction.response.send_message(f'Added [{song_name}](<{song_link}>) to the queue')
    else:
        await interaction.response.send_message(f'Loading [{song_name}](<{song_link}>)')

    queue.append({'song_name': song_name, 'song_link': song_link})

    while True:

        i = 0
        for dict in queue:
            if dict['song_link'] == song_link:
                break
            i += 1

        if i == 0:
            break
        
        await asyncio.sleep(1)

    while song_is_active:
        await asyncio.sleep(1)

    await queue_handler(interaction, 'Play')

@tree.command(name='queue', description='Part of the sounds pack, checks the current queue,', guild=DEF_GUILD)
async def queue_cmd(interaction: Interaction):

    if not song_is_active:
        await interaction.response.send_message('There is no song playing!', ephemeral=True)
        return

    i = 0
    msg = 'Next in queue:\n'
    for song in queue:
        msg += f"{'Playing' if i == 0 else i}: [{song['song_name']}](<{song['song_link']}>)\n"
    await interaction.response.send_message(msg)

@tree.command(name='skip', description='Part of the sounds pack, skips current song.', guild=DEF_GUILD)
async def skip(interaction: Interaction):
    await queue_handler(interaction, 'Skip')

@tree.command(name='pause', description='Part of the sounds pack, pauses current song.', guild=DEF_GUILD)
async def pause(interaction: Interaction):
    await queue_handler(interaction, 'Pause')

@tree.command(name='resume', description='Part of the sounds pack, resumes current song.', guild=DEF_GUILD)
async def skip(interaction: Interaction):
    await queue_handler(interaction, 'Resume')

@tree.command(name='stop', description='Part of the sounds pack, stops playback and clears queue.', guild=DEF_GUILD)
async def stop(interaction: Interaction):
    await queue_handler(interaction, 'Stop')

@tree.command(name='username', description='View, Edit, Delete, or Add Usernames! (to delete, type delete as username)', guild=DEF_GUILD)
async def username(interaction: Interaction, mode: Literal['View', 'Edit', 'Add'], username: str = None, platform: str = None, user: Member | None = None):
    """/username command

    Args:
        interaction (Interaction): discord.Interaction
        mode (Literal['View', 'Edit', 'Add']): mode selector.
        username (str, optional): username input. Defaults to None.
        platform (str, optional): platform input. Defaults to None.
        user (Member | None, optional): discord.Member input. Defaults to None.
    """

    # Capitalize platform if given
    platform = platform.capitalize() if platform else None

    # Load JSON as Dict Constant
    with open('./usernames.json', 'r') as R:
        USERNAME_DATA = json.load(R)
        R.close()

    # Mode selector
    match mode:

        # View mode
        case 'View':
            # Set user to the request's user if user not given
            if not user:
                user = interaction.user

            # User db check
            if str(user.id) not in USERNAME_DATA:
                await interaction.response.send_message(f'{user.display_name} has no usernames', ephemeral=True)
                return
            
            # Platform view variant (single username)
            if platform:

                # Platform db check
                if platform not in USERNAME_DATA[str(user.id)]:
                    await interaction.response.send_message(f'No username for {user.display_name} on {platform}', ephemeral=True)
                    return
                await interaction.response.send_message(f"{user.display_name}'s username for {platform} is {USERNAME_DATA[str(user.id)][platform]}")
                return

            # Default interation if platform not given (multi-username)
            msg = f'Usernames for {user.display_name}:\n'
            for platf, usern in USERNAME_DATA[str(user.id)].items():
                msg += f'{platf}: {usern}\n'
            await interaction.response.send_message(msg)
            
        # Edit mode
        case 'Edit':
            # Username + platform var check (str | None)
            if not username or not platform:
                await interaction.response.send_message("Username and/or Platform was not supplied.", ephemeral=True)
                return
            
            # Username db check
            if str(interaction.user.id) not in USERNAME_DATA:
                await interaction.response.send_message("You do not have any usernames in the db!", ephemeral=True)
                return
            
            # Platform db check
            if platform not in USERNAME_DATA[str(interaction.user.id)]:
                await interaction.response.send_message(f'Platform ({platform}) not found in your database, make sure it was added before!', ephemeral=True)
                return
            
            # Delete mode
            if username.lower() == 'delete':
                del USERNAME_DATA[str(interaction.user.id)][platform]
                await interaction.response.send_message(f'Deleted username on {platform}!')
            
            # Edit db
            else:
                USERNAME_DATA[str(interaction.user.id)][platform] = username
                await interaction.response.send_message(f'Edited username on {platform} to {username}!')
            
            # Convert Dict to JSON and save to db
            with open('./usernames.json', 'w') as W:
                json.dump(USERNAME_DATA, W, indent=3)
                W.close()

        # Add mode
        case 'Add':
            # Username + platform check
            if not username or not platform:
                await interaction.response.send_message("Username and/or Platform was not supplied.", ephemeral=True)
                return
            
            # Username db check + init
            if str(interaction.user.id) not in USERNAME_DATA:
                USERNAME_DATA[str(interaction.user.id)] = {}
            
            # Add username to Dict
            USERNAME_DATA[str(interaction.user.id)][platform] = username

            # Convert Dict to JSON and save to db
            with open('./usernames.json', 'w') as w:
                json.dump(USERNAME_DATA, w, indent=3)
                w.close()

            # Response if all goes correct
            await interaction.response.send_message(f"Added the username \"{username}\" to {platform}.")

@tree.command(name='reset_self_roles', description="resets the self roles handler", guild=DEF_GUILD)
async def reset_self_roles(interaction: Interaction):

    ADMIN_ROLE = interaction.guild.get_role(1193767938612789259)
    if ADMIN_ROLE not in interaction.user.roles:
        await interaction.response.send_message("Requires the `$~ sudo` role")

    MESSAGE = await interaction.channel.fetch_message(1193785577724727338)

    await MESSAGE.edit(content="React with the corrosponding emoji to get the role.\n\n🧊 - Siege Ping\n🪳 - Lethal Company Ping\n🌐 - Destiny 2 Ping")
    await MESSAGE.add_reaction("🧊")
    await MESSAGE.add_reaction("🪳")
    await MESSAGE.add_reaction("🌐")

    await interaction.response.send_message("Reset was successful!", ephemeral=True)

@tree.command(name='echo', description="Owner only", guild=DEF_GUILD)
async def activate(interaction: Interaction, message: str):
    if interaction.user.id == 737486185466691585:
        await interaction.response.send_message("Done!", ephemeral = True)
        await interaction.channel.send(message)
    else:
        await interaction.response.send_message("read desc goofball")


@client.event
async def on_member_join(member: Member):
    normie_role = member.guild.get_role(1193769091396288514)
    await member.add_roles(normie_role, reason="Join")

@client.event
async def on_raw_reaction_add(payload: RawReactionActionEvent):
    

    SIEGE_ROLE = payload.member.guild.get_role(1193768641079021588)
    LETHAL_ROLE = payload.member.guild.get_role(1193770900881940570)
    DESTINY_ROLE = payload.member.guild.get_role(1193770955516940398)

    if payload.channel_id != 1193770729175519363:
        return

    if payload.emoji.name == '🧊':
        await payload.member.add_roles(SIEGE_ROLE)

    if payload.emoji.name == '🪳':
        await payload.member.add_roles(LETHAL_ROLE)

    if payload.emoji.name == '🌐':
        await payload.member.add_roles(DESTINY_ROLE)

@client.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    
    GUILD = await client.fetch_guild(1193767905049981069)
    MEMBER = await GUILD.fetch_member(payload.user_id)

    SIEGE_ROLE = GUILD.get_role(1193768641079021588)
    LETHAL_ROLE = GUILD.get_role(1193770900881940570)
    DESTINY_ROLE = GUILD.get_role(1193770955516940398)

    if payload.channel_id != 1193770729175519363:
        return

    if payload.emoji.name == '🧊':
        await MEMBER.remove_roles(SIEGE_ROLE)

    if payload.emoji.name == '🪳':
        await MEMBER.remove_roles(LETHAL_ROLE)

    if payload.emoji.name == '🌐':
        await MEMBER.remove_roles(DESTINY_ROLE)

# @client.event
# async def on_voice_state_update(member: Member, before: VoiceState, after: VoiceState):
#     if member.bot:
#         if member in before.channel.members and member not in after.channel.members:
#             await music_status_channel.edit(name='No songs playing')

@client.event
async def on_ready():

    global music_status_channel
    music_status_channel = client.get_guild(GUILD_ID).voice_channels[0]
    
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="for plant"))
    await tree.sync(guild=DEF_GUILD)
    print("Ready!")


if __name__ == '__main__':
    client.run(TOKEN)