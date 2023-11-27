#from Bot_Utilities import *
from Standard_Constants import *
from datetime import datetime
import discord

def universal_embed(title, title_desc, color, fields, image=None,
                                                        timestamp=False,
                                                        footer=None):

    embed = discord.Embed(title=title,
                          description=title_desc,
                          color=color)

    for name, value in fields:

        embed.add_field(name=name,
                        value=value,
                        inline=False)

    if image:
        embed.set_thumbnail(url=image)

    if footer:
        embed.set_footer(text=footer)

    if timestamp:
        timestamp = datetime.now()
        dt_string = timestamp.strftime("%B %d, %Y (%H:%M:%S)")

        embed.add_field(name="Timestamp",
                        value=dt_string,
                        inline=False)
    return embed

# embed for unexpected end
def embed_abrupt_end(type, users_added, e =""):

    title=f"{type}: Bot Stopped Unexpectedly."
    title_desc = ""
    color = CAUTION_COLOR
    fields = [
                (f"Students added in batch: {users_added}", ""),
                ("context", e[-500:])
             ]

    return universal_embed(title, title_desc, color, fields, timestamp=True)

# embed for unsuccessful assigning of type
def embed_client_error(user, type):

    title = f"Unable to add {type} to {user.name}"
    title_desc = ""
    color = ERROR_COLOR
    timestamp = datetime.now()

    return universal_embed(title, title_desc, color, fields, footer=timestamp)

def embed_leave_message(current_semester):

    title = "Left Server - Old Semester"
    title_desc = f"Leaving all servers without {current_semester}' in its name."
    color = NEUTRAL_COLOR

    return universal_embed(title, title_desc, color, fields, timestamp=True)


def embed_start_bot(message=None, channel=None):

    fields = []
    color = NEUTRAL_COLOR
    title = "Started " + message
    title_desc = ''

    if channel:
        title_desc += f'<#{channel.id}>'

    timestamp = datetime.now()

    return universal_embed(title, title_desc, color, fields, footer=timestamp)

def embed_end_bot(message=None, channel=None, users_added = None, messages = None):

    fields = []
    color = NEUTRAL_COLOR
    timestamp = datetime.now()
    title_desc = ''

    title = "Finished " + message

    if users_added:
        fields.insert( -1, (f"Students Processed: {users_added}","") )
    if messages:
        fields.insert( -1, (f"Messages Processed: {messages}", "") )

    return universal_embed(title, title_desc, color, fields, footer=timestamp)

# embed for successful assigning of name and role
def embed_successful_assign(name, user, role):

    title = f"Added New Student"
    title_desc = ""
    color = SUCCESS_COLOR
    fields = [
                ("Discord Account", f"{user.mention}" ),
                ("Role", role.mention),
                ("Canvas Name", name),
                ("Discord Name", user.name)
             ]
    image = user.avatar

    return universal_embed(title, title_desc, color, fields, image, timestamp=True)

def embed_successful_rerole(user, old_role, new_role):

    title = "Reassigned Student"
    title_desc = ""
    color = SUCCESS_COLOR
    fields = [
                ("Discord Account", f"{user.mention}" ),
                ("Old Role", old_role.mention),
                ("New Role", new_role.mention),
             ]
    image = user.avatar

    return universal_embed(title, title_desc, color, fields, image, timestamp=True)

# embed for unsuccessful assign of nick_name
    # triggers when attempted name is not in guest_list
    # - for use in bot log channel
    # obsolete!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def embed_unsuccessful_assign(user, name=None, role=None, e=None):

        user_roles = user.roles
        role_mentions = [role.mention for role in user_roles]
        join_role_mentions = ", ".join(role_mentions)

        title = f"Unable to Add New Student"
        title_desc = ""
        color = ERROR_COLOR
        image = user.avatar

        fields = [
                    ("Discord Account", user.mention),
                    ("Current Roles At Timestamp", join_role_mentions)
                 ]

        if (name):
            fields.append( ("Attempted Name", name) )

        if (role):

            fields.append( ("Attempted Role",
            f"{role.mention} - Please check if bot's permissions are above role") )

        if (e):
            fields.append( ("Error", e ) )

        return universal_embed(title, title_desc, color, fields, image=image,
                                                                timestamp=True)

# embed for unsuccessful assign of role
    # triggers when attempted name is not in guest_list
    # and notifies the user
    # - for use in welcome channel
def embed_user_error(nick_name):

    title = "Name Not Recognized"
    title_desc = ""
    color = ERROR_COLOR
    fields = [
                (nick_name, "Please double check if your name is " +
                            "spelled **exactly** the same as found on Canvas.")
             ]
    footer = f"{datetime.now()} If you believe this was a mistake, please inform an admin."

    return universal_embed(title, title_desc, color, fields, footer=footer)
