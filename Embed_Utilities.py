#from Bot_Utilities import *
from Standard_Constants import *
from datetime import datetime
import discord

# embed for unexpected end
def embed_abrupt_end(type, users_added, e =""):

    now = datetime.now()

    embed = discord.Embed(title=f"{type}: Bot Stopped Unexpectedly.",
                    color = CAUTION_COLOR)

    embed.add_field(name=f"Students added in batch: {users_added}",
                    value = "",
                    inline=False)
    embed.add_field(name = "Context",
                    value = f"{e[-500:]}")

    embed.set_footer(text=f"{now}")

    return embed

# embed for unsuccessful assigning of type
def embed_client_error(user, type):

    now = datetime.now()

    embed = discord.Embed(title=f"Unable to add {type} to {user.name}",
                    color = ERROR_COLOR)

    embed.set_footer(text=f"{now}")

    return embed

def embed_leave_message(current_semester):

    now = datetime.now()

    embed = discord.Embed(title=f"Left Server - Old Semester",
                    description=f"Leaving all servers without " +
                                f"'{current_semester}' in its name.",
                    color = NEUTRAL_COLOR)

    embed.set_footer(text=f"{now}")

    return embed


# embed for signaling the start/end of the bot
def embed_start_end_bot(state, channel, users_added = 0):

    now = datetime.now()
    channel_mention = f'<#{channel.id}>'

    embed = discord.Embed(title=f"{state} processing chat log.",
                        description=f"{channel_mention}",
                        color = NEUTRAL_COLOR)

    embed.set_footer(text=f"{now}")

    if (state == "Finished"):

        embed.add_field(name=f"Students added in batch: {users_added}",
                        value = "",
                        inline=False)
    return embed

# embed for successful assigning of name and role
def embed_successful_assign(name, user, role):

    now = datetime.now()
    user_display = user.name
    user_id = user.id
    role_mention = role.mention
    user_pfp = user.avatar
    #thumbnail_url = user_pfp.with_size(64, 64)

    embed = discord.Embed(title=f"Added New Student",
                    color = SUCCESS_COLOR)

    embed.add_field(name=f"Full Name",
                    value=f"{name}",
                    inline=False)

    embed.add_field(name=f"Discord Name",
                    value=f"{user_display}",
                    inline=False)

    embed.add_field(name=f"Discord ID",
                    value=f"{user_id}",
                    inline=False)

    embed.add_field(name="Role",
                    value=f"{role_mention}",
                    inline=False)

    embed.set_thumbnail(url=user_pfp)

    embed.set_footer(text=f"{now}")

    return embed

# embed for unsuccessful assign of nick_name
    # triggers when attempted name is not in guest_list
    # - for use in bot log channel
def embed_unsuccessful_assign(user, name=None, role=None):

        now = datetime.now()
        user_display = user.name
        user_id = user.id
        user_pfp = user.avatar

        embed = discord.Embed(title=f"Unable to Add New Student",
                            color = ERROR_COLOR)


        if (name):
            embed.add_field(name=f"Attempted Name",
                            value=f"{name}",
                            inline=False)
        if (role):
            embed.add_field(name=f"Attempted Role",
                            value=f"{role.mention} - " +
                            "Please check if bot's permissions are above role",
                            inline=False)

        embed.add_field(name=f"Discord Name",
                            value=f"{user_display}",
                            inline=False)

        embed.add_field(name=f"Discord ID",
                            value=f"{user_id}",
                            inline=False)

        embed.set_thumbnail(url=user_pfp)

        embed.set_footer(text=f"{now}")

        return embed

# embed for unsuccessful assign of role
    # triggers when attempted name is not in guest_list
    # and notifies the user
    # - for use in welcome channel
def embed_user_error(nick_name):

    now = datetime.now()
    embed = discord.Embed(title=f"Name Not Recognized",
                        color = ERROR_COLOR)

    embed.add_field(name=f"{nick_name}",
                        value = "Please type your name " +
                        "exactly as it is in canvas.",
                        inline=False)

    embed.set_footer(text=f"{now} - " +
        "If you believe this was a mistake, please inform an admin.")

    return embed
