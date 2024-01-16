import discord, json, os
from discord import app_commands, Interaction, Member, RawReactionActionEvent
from typing import Literal
from dotenv import load_dotenv

# Constants and Env
load_dotenv()
TOKEN = os.getenv('TOKEN')
DEF_GUILD = discord.Object(id=1193767905049981069)

# Discord app_commands and client Init
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


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


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="the server grow"))
    await tree.sync(guild=DEF_GUILD)
    print("Ready!")


if __name__ == '__main__':
    client.run(TOKEN)