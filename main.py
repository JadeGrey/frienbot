import discord, json, os, shutil, asyncio, youtubesearchpython.__future__, youtubesearchpython, handlers.currency, time
from pytube import YouTube, exceptions
from discord import app_commands, Interaction, Member, RawReactionActionEvent, VoiceClient, VoiceState
from typing import Literal, Union
from dotenv import load_dotenv

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

load_dotenv()
TOKEN = os.getenv('TOKEN')
AUDIO_FOLDER = os.getenv('AUDIO_FOLDER')
DB_FOLDER = os.getenv('DB_FOLDER')
GUILD_ID = int(os.getenv('GUILD_ID'))
DEF_GUILD = discord.Object(id=GUILD_ID)

queue = []
vc = None
song_is_active = False
song_is_paused = False
queue_stopped = False

if __name__ == '__main__':

    for filename in os.listdir(AUDIO_FOLDER):
        file_path = os.path.join(AUDIO_FOLDER, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

async def queue_handler(interaction: discord.Interaction, action: Literal['Play', 'Skip', 'Pause', 'Resume', 'Stop'], queue: list = queue) -> None:

    global song_is_active
    global song_is_paused
    global queue_stopped
    global vc

    voice_channel = interaction.user.voice.channel
    text_channel = interaction.channel
    song_name = queue[0]['song_name']
    song_link = queue[0]['song_link']

    match action:
        # <CODE UGLY ASF BRO WTF HIGH ME????>
        case 'Play':

            yt = YouTube(song_link)

            try:

                audio_size = yt.streams.filter(only_audio = True).first().filesize_mb

                if audio_size > 100:
                    await text_channel.send(f'Failed to load {song_name} (Audio {round(audio_size - 100)}mb over size limit)')
                    queue.pop(0)
                    return

                audio = yt.streams.filter(only_audio = True).first().download(output_path='./music')

                if vc == None:
                    vc = await voice_channel.connect()

                if not vc.is_connected():
                    vc = await voice_channel.connect()

                ffmpeg_instance = discord.FFmpegPCMAudio(executable='C:/ffmpeg/bin/ffmpeg.exe', source=audio)
                
                vc.play(ffmpeg_instance)

                await text_channel.send(f'Loaded [{song_name}](<{song_link}>)')
                song_is_active = True
                

                while song_is_active and vc.is_playing() or song_is_paused:
                    await asyncio.sleep(1)

                vc.stop()
                queue.pop(0)
                
                ffmpeg_instance.cleanup()

                while True:
                    try:
                        os.remove(audio)
                        break
                    except:
                        await asyncio.sleep(1)

                if queue == []:
                    await vc.disconnect()
                    vc = None
                    
                song_is_active = False

            except exceptions.AgeRestrictedError:
                queue.pop(0)
                await text_channel.send(f'Failed to load {song_name} (Age Restricted)')

            
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
            queue_stopped = True

            await vc.disconnect()

            await interaction.response.send_message(f'Stopped playback and cleared queue!')

@tree.command(name='play', description='Part of the sounds pack, searches for music on YouTube.', guild=DEF_GUILD)
async def search(interaction: Interaction, q: str) -> None:

    global queue_stopped

    BLACKLIST = interaction.guild.get_role(1198842714683355246)

    if BLACKLIST in interaction.user.roles:
        await interaction.response.send_message('You are blacklisted from this function.', ephemeral=True)
        return

    if queue_stopped:
        queue_stopped = False

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

    if queue_stopped:
        return

    await queue_handler(interaction, 'Play')

@tree.command(name='queue', description='Part of the sounds pack, checks the current queue,', guild=DEF_GUILD)
async def queue_cmd(interaction: Interaction) -> None:
    try:
        if not song_is_active and not vc.is_playing():
            await interaction.response.send_message('There is no song playing!', ephemeral=True)
            return
    except:
            await interaction.response.send_message('There is no song playing!', ephemeral=True)
            return

    i = 0
    msg = 'Next in queue:\n'
    for song in queue:
        msg += f"{'Playing' if i == 0 else i}: [{song['song_name']}](<{song['song_link']}>)\n"
        i += 1
        
    await interaction.response.send_message(msg)

@tree.command(name='skip', description='Part of the sounds pack, skips current song.', guild=DEF_GUILD)
async def skip(interaction: Interaction) -> None:
    BLACKLIST = interaction.guild.get_role(1198842714683355246)

    if BLACKLIST in interaction.user.roles:
        await interaction.response.send_message('You are blacklisted from this function.', ephemeral=True)
        return
    
    await queue_handler(interaction, 'Skip')

@tree.command(name='pause', description='Part of the sounds pack, pauses current song.', guild=DEF_GUILD)
async def pause(interaction: Interaction) -> None:
    BLACKLIST = interaction.guild.get_role(1198842714683355246)

    if BLACKLIST in interaction.user.roles:
        await interaction.response.send_message('You are blacklisted from this function.', ephemeral=True)
        return
    
    await queue_handler(interaction, 'Pause')

@tree.command(name='resume', description='Part of the sounds pack, resumes current song.', guild=DEF_GUILD)
async def skip(interaction: Interaction) -> None:
    BLACKLIST = interaction.guild.get_role(1198842714683355246)

    if BLACKLIST in interaction.user.roles:
        await interaction.response.send_message('You are blacklisted from this function.', ephemeral=True)
        return
    
    await queue_handler(interaction, 'Resume')

@tree.command(name='stop', description='Part of the sounds pack, stops playback and clears queue.', guild=DEF_GUILD)
async def stop(interaction: Interaction) -> None:
    BLACKLIST = interaction.guild.get_role(1198842714683355246)

    if BLACKLIST in interaction.user.roles:
        await interaction.response.send_message('You are blacklisted from this function.', ephemeral=True)
        return
    
    await queue_handler(interaction, 'Stop')

@tree.command(name='username', description='View, Edit, Delete, or Add Usernames! (to delete, type delete as username)', guild=DEF_GUILD)
async def username(interaction: Interaction, mode: Literal['View', 'Edit', 'Add'], username: str = None, platform: str = None, user: Member | None = None) -> None:

    platform = platform.capitalize() if platform else None

    with open(f'{DB_FOLDER}usernames.json', 'r') as R:
        USERNAME_DATA = json.load(R)
        R.close()

    match mode:

        case 'View':
            if not user:
                user = interaction.user

            if str(user.id) not in USERNAME_DATA:
                await interaction.response.send_message(f'{user.display_name} has no usernames', ephemeral=True)
                return
            
            if platform:

                if platform not in USERNAME_DATA[str(user.id)]:
                    await interaction.response.send_message(f'No username for {user.display_name} on {platform}', ephemeral=True)
                    return
                await interaction.response.send_message(f"{user.display_name}'s username for {platform} is {USERNAME_DATA[str(user.id)][platform]}")
                return

            msg = f'Usernames for {user.display_name}:\n'
            for platf, usern in USERNAME_DATA[str(user.id)].items():
                msg += f'{platf}: {usern}\n'
            await interaction.response.send_message(msg)
            
        case 'Edit':
            if not username or not platform:
                await interaction.response.send_message("Username and/or Platform was not supplied.", ephemeral=True)
                return
            
            if str(interaction.user.id) not in USERNAME_DATA:
                await interaction.response.send_message("You do not have any usernames in the db!", ephemeral=True)
                return
            
            if platform not in USERNAME_DATA[str(interaction.user.id)]:
                await interaction.response.send_message(f'Platform ({platform}) not found in your database, make sure it was added before!', ephemeral=True)
                return
            
            if username.lower() == 'delete':
                del USERNAME_DATA[str(interaction.user.id)][platform]
                await interaction.response.send_message(f'Deleted username on {platform}!')
            
            else:
                USERNAME_DATA[str(interaction.user.id)][platform] = username
                await interaction.response.send_message(f'Edited username on {platform} to {username}!')
            
            with open(f'{DB_FOLDER}usernames.json', 'w') as W:
                json.dump(USERNAME_DATA, W, indent=3)
                W.close()

        case 'Add':
            if not username or not platform:
                await interaction.response.send_message("Username and/or Platform was not supplied.", ephemeral=True)
                return
            
            if str(interaction.user.id) not in USERNAME_DATA:
                USERNAME_DATA[str(interaction.user.id)] = {}
            
            USERNAME_DATA[str(interaction.user.id)][platform] = username

            with open(f'{DB_FOLDER}usernames.json', 'w') as w:
                json.dump(USERNAME_DATA, w, indent=3)
                w.close()

            await interaction.response.send_message(f"Added the username \"{username}\" to {platform}.")

@tree.command(name='reset_self_roles', description="resets the self roles handler", guild=DEF_GUILD)
async def reset_self_roles(interaction: Interaction) -> None:

    ADMIN_ROLE = interaction.guild.get_role(1193767938612789259)
    if ADMIN_ROLE not in interaction.user.roles:
        await interaction.response.send_message("Requires the `$~ sudo` role")

    MESSAGE = await interaction.channel.fetch_message(1193785577724727338)

    await MESSAGE.edit(content="React with the corrosponding emoji to get the role.\n\n🧊 - Siege Ping\n🪳 - Lethal Company Ping\n🌐 - Destiny 2 Ping\n🐱 - Palworld Ping")
    await MESSAGE.add_reaction("🧊")
    await MESSAGE.add_reaction("🪳")
    await MESSAGE.add_reaction("🌐")
    await MESSAGE.add_reaction("🐱")

    await interaction.response.send_message("Reset was successful!", ephemeral=True)

@tree.command(name='echo', description="Owner only", guild=DEF_GUILD)
async def activate(interaction: Interaction, message: str):
    if interaction.user.id == 737486185466691585:
        await interaction.response.send_message("Done!", ephemeral = True)
        await interaction.channel.send(message)
    else:
        await interaction.response.send_message("read desc goofball")

@tree.command(name='dev_add_currency', description='dev pack', guild=DEF_GUILD)
async def dev_add_currency(interaction: Interaction, amount: int, user: Member):
    currency_data = handlers.currency.get_currency_data()

    if str(user.id) not in currency_data:
        handlers.currency.add_user_to_currency_data(str(user.id))
        currency_data = handlers.currency.get_currency_data()

    currency_data[str(user.id)] += amount
    handlers.currency.save_currency_data(currency_data)

    await interaction.response.send_message(f'{'Added' if amount >= 0 else 'Removed'} {amount if amount >= 0 else -amount} coin{'s' if amount != 1 else ''} {'to' if amount >= 0 else 'from'} {user.display_name}!')

@tree.command(name='coins', description='Part of the economy pack, checks your coin wallet!', guild=DEF_GUILD)
async def coins(interaction: Interaction, user: Member = None):
    if not user:
        user = interaction.user

    currency_data = handlers.currency.get_currency_data()

    if str(user.id) not in currency_data:
        handlers.currency.add_user_to_currency_data(str(user.id))
        currency_data = handlers.currency.get_currency_data()

    coins = currency_data[str(user.id)]

    await interaction.response.send_message(f'You have {coins} coin{'s' if coins != 1 else ''}!')

@tree.command(name='daily', description='Part of the economy pack, gets your daily coins!', guild=DEF_GUILD)
async def daily(interaction: Interaction):
    currency_data = handlers.currency.get_currency_data()
    drop_data = handlers.currency.get_drop_data()

    if str(interaction.user.id) not in drop_data:
        handlers.currency.add_user_to_drop_data(str(interaction.user.id))
        drop_data = handlers.currency.get_drop_data()

    if str(interaction.user.id) not in currency_data:
        handlers.currency.add_user_to_currency_data(str(interaction.user.id))
        currency_data = handlers.currency.get_currency_data()

    now = time.time()
    then = drop_data[str(interaction.user.id)]['daily']

    if now - then < 86400:
        await interaction.response.send_message(f'You will get another daily box <t:{round(then) + 86400}:R>')
        return
    
    drop = handlers.currency.calculate_drop('Daily')
    
    amount = drop['amount']
    rarity = drop['rarity']

    currency_data[str(interaction.user.id)] += amount
    drop_data[str(interaction.user.id)]['daily'] = now

    handlers.currency.save_currency_data(currency_data)
    handlers.currency.save_drop_data(drop_data)

    await interaction.response.send_message(f'You opened a {rarity} daily box and got {amount} coins!')

@tree.command(name='weekly', description='Part of the economy pack, gets your weekly coins!', guild=DEF_GUILD)
async def daily(interaction: Interaction):
    currency_data = handlers.currency.get_currency_data()
    drop_data = handlers.currency.get_drop_data()

    if str(interaction.user.id) not in drop_data:
        handlers.currency.add_user_to_drop_data(str(interaction.user.id))
        drop_data = handlers.currency.get_drop_data()

    if str(interaction.user.id) not in currency_data:
        handlers.currency.add_user_to_currency_data(str(interaction.user.id))
        currency_data = handlers.currency.get_currency_data()

    now = time.time()
    then = drop_data[str(interaction.user.id)]['weekly']

    if now - then < (86400 * 7):
        await interaction.response.send_message(f'You will get another weekly box <t:{round(then) + (86400 * 7)}:R>')
        return
    
    drop = handlers.currency.calculate_drop('Weekly')
    
    amount = drop['amount']
    rarity = drop['rarity']

    currency_data[str(interaction.user.id)] += amount
    drop_data[str(interaction.user.id)]['weekly'] = now

    handlers.currency.save_currency_data(currency_data)
    handlers.currency.save_drop_data(drop_data)

    await interaction.response.send_message(f'You opened a {rarity} weekly box and got {amount} coins!')

@tree.command(name='monthly', description='Part of the economy pack, gets your monthly coins!', guild=DEF_GUILD)
async def daily(interaction: Interaction):
    currency_data = handlers.currency.get_currency_data()
    drop_data = handlers.currency.get_drop_data()

    if str(interaction.user.id) not in drop_data:
        handlers.currency.add_user_to_drop_data(str(interaction.user.id))
        drop_data = handlers.currency.get_drop_data()

    if str(interaction.user.id) not in currency_data:
        handlers.currency.add_user_to_currency_data(str(interaction.user.id))
        currency_data = handlers.currency.get_currency_data()

    now = time.time()
    then = drop_data[str(interaction.user.id)]['monthly']

    if now - then < (86400 * 28):
        await interaction.response.send_message(f'You will get another monthly box <t:{round(then) + (86400 * 28)}:R>')
        return
    
    drop = handlers.currency.calculate_drop('Monthly')
    
    amount = drop['amount']
    rarity = drop['rarity']

    currency_data[str(interaction.user.id)] += amount
    drop_data[str(interaction.user.id)]['monthly'] = now

    handlers.currency.save_currency_data(currency_data)
    handlers.currency.save_drop_data(drop_data)

    await interaction.response.send_message(f'You opened a {rarity} monthly box and got {amount} coins!')

@tree.command(name='leaderboard', description='Part of the economy pack, gets the top users\' coin balances', guild=DEF_GUILD)
async def leaderboard(interaction: Interaction):
    currency_data: dict = handlers.currency.get_currency_data()
    sorted_currency_data = sorted(currency_data.items(), key=lambda x: int(x[1]), reverse=True)
    coins = sorted_currency_data[i][1]

    msg = 'Leaderboard:'
    for i in range(10) if len(currency_data) > 10 else range(len(currency_data)):
        user = interaction.guild.get_member(int(sorted_currency_data[i][0]))
        msg += f'\n- {user.display_name}: {coins} coin{'s' if coins != 1 else ''}'

    await interaction.response.send_message(msg)

@tree.command(name='gamble', description='Part of the economy pack, gambles \'n\' coins.', guild=DEF_GUILD)
async def gamble(interaction: Interaction, amount: int):
    winnings = handlers.currency.calculate_gamble(amount)

    currency_data = handlers.currency.get_currency_data()
    gambling_data = handlers.currency.get_gambling_data()

    if str(interaction.user.id) not in currency_data:
        handlers.currency.add_user_to_currency_data(str(interaction.user.id))
        currency_data = handlers.currency.get_currency_data()

    if str(interaction.user.id) not in gambling_data:
        handlers.currency.add_user_to_gambling_data(str(interaction.user.id))
        gambling_data = handlers.currency.get_gambling_data()

    currency_data[str(interaction.user.id)] += winnings - amount
    handlers.currency.save_currency_data(currency_data)

    gambling_data[str(interaction.user.id)]['coins'] += winnings - amount

    if winnings == 0:
        gambling_data[str(interaction.user.id)]['losses'] += 1
    else:
        gambling_data[str(interaction.user.id)]['wins'] += 1

    handlers.currency.save_gambling_data(gambling_data)

    await interaction.response.send_message(f'You {f'won {winnings} coin{'s' if winnings != 1 else ''}' if winnings != 0 else f'lost {amount} coin{'s' if amount != 1 else ''}'}')


@client.event
async def on_member_join(member: Member):
    normie_role = member.guild.get_role(1193769091396288514)
    await member.add_roles(normie_role, reason="Join")

@client.event
async def on_raw_reaction_add(payload: RawReactionActionEvent):
    

    SIEGE_ROLE = payload.member.guild.get_role(1193768641079021588)
    LETHAL_ROLE = payload.member.guild.get_role(1193770900881940570)
    DESTINY_ROLE = payload.member.guild.get_role(1193770955516940398)
    PALWORLD_ROLE = payload.member.guild.get_role(1200753458555396147)

    if payload.channel_id != 1193770729175519363:
        return

    if payload.emoji.name == '🧊':
        await payload.member.add_roles(SIEGE_ROLE)

    if payload.emoji.name == '🪳':
        await payload.member.add_roles(LETHAL_ROLE)

    if payload.emoji.name == '🌐':
        await payload.member.add_roles(DESTINY_ROLE)
    
    if payload.emoji.name == '🐱':
        await payload.member.add_roles(PALWORLD_ROLE)

@client.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    
    GUILD = await client.fetch_guild(1193767905049981069)
    MEMBER = await GUILD.fetch_member(payload.user_id)

    SIEGE_ROLE = GUILD.get_role(1193768641079021588)
    LETHAL_ROLE = GUILD.get_role(1193770900881940570)
    DESTINY_ROLE = GUILD.get_role(1193770955516940398)
    PALWORLD_ROLE = GUILD.get_role(1200753458555396147)

    if payload.channel_id != 1193770729175519363:
        return

    if payload.emoji.name == '🧊':
        await MEMBER.remove_roles(SIEGE_ROLE)

    if payload.emoji.name == '🪳':
        await MEMBER.remove_roles(LETHAL_ROLE)

    if payload.emoji.name == '🌐':
        await MEMBER.remove_roles(DESTINY_ROLE)

    if payload.emoji.name == '🐱':
        await payload.member.add_roles(PALWORLD_ROLE)


@client.event
async def on_ready():

    
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="for plant"))
    await tree.sync(guild=DEF_GUILD)
    print("Ready!")

if __name__ == '__main__':
    client.run(TOKEN)