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

    embed.set_footer(text=now)

    return embed

# embed for unsuccessful assigning of type
def embed_client_error(user, type):

    now = datetime.now()

    embed = discord.Embed(title=f"Unable to add {type} to {user.name}",
                    color = ERROR_COLOR)

    embed.set_footer(text=now)

    return embed

def embed_leave_message(current_semester):

    now = datetime.now()

    embed = discord.Embed(title=f"Left Server - Old Semester",
                    description=f"Leaving all servers without " +
                                f"'{current_semester}' in its name.",
                    color = NEUTRAL_COLOR)

    embed.set_footer(text=now)

    return embed


# embed for signaling the start/end of the bot
def embed_start_end_bot(state, channel, users_added = 0, messages = 0):

    now = datetime.now()
    channel_mention = f'<#{channel.id}>'

    embed = discord.Embed(title=f"{state} processing chat log.",
                        description=f"{channel_mention}",
                        color = NEUTRAL_COLOR)

    embed.set_footer(text=now)

    if (state == "Finished"):

        embed.add_field(name=f"Messages Processed: {messages}",
                        value = "",
                        inline=False)
        embed.add_field(name=f"Students added in batch: {users_added}",
                        value = "",
                        inline=False)
    return embed

# embed for successful assigning of name and role
def embed_successful_assign(name, user, role):

    now = datetime.now()
    user_display = user.name
    user_mention = user.mention
    user_id = user.id
    role_mention = role.mention
    user_pfp = user.avatar

    embed = discord.Embed(title=f"Added New Student",
                    color = SUCCESS_COLOR)

    embed.add_field(name=f"Discord Account",
                    value=f"{user_mention}",
                    inline=False)

    embed.add_field(name="Role",
                    value=role_mention,
                    inline=False)

    embed.add_field(name=f"Canvas Name",
                    value=f"{name}",
                    inline=False)

    embed.add_field(name=f"Discord Name",
                    value=f"{user_display}",
                    inline=False)

    embed.set_thumbnail(url=user_pfp)

    embed.set_footer(text=now)

    return embed

# embed for unsuccessful assign of nick_name
    # triggers when attempted name is not in guest_list
    # - for use in bot log channel
def embed_unsuccessful_assign(user, name=None, role=None, e=None):

        now = datetime.now()
        user_mention = user.mention
        user_id = user.id
        user_pfp = user.avatar
        user_roles = user.roles
        role_names = [role.name for role in user_roles]

        embed = discord.Embed(title=f"Unable to Add New Student",
                            color = ERROR_COLOR)
        
        embed.add_field(name = f"A Time Stamp",
                        value = now,
                        inline = False)

        embed.add_field(name=f"Discord Account",
                            value=f"{user_mention}",
                            inline=False)

        embed.add_field(name=f"Current Roles At A Timestamp",
                            value=", ".join(role_names),
                            inline=False)

        if (name):
            embed.add_field(name=f"Attempted Name",
                            value=f"{name}",
                            inline=False)

        if (role):
            embed.add_field(name=f"Attempted Role",
                            value=f"{role.mention} - " +
                            "Please check if bot's permissions are above role",
                            inline=False)

        if (e):
            embed.add_field(name="Error",
                            value=f"{e}",
                            inline=False)

        embed.set_thumbnail(url=user_pfp)
        
        embed.set_footer(text="END OF LOG MESSAGE")

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
                        value = "Please double check if your name is "+
                        "spelled the same as on Canvas.",
                        inline=False)

    embed.set_footer(text=f"{now} - " +
        "If you believe this was a mistake, please inform an admin.")

    return embed
