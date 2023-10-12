from datetime import datetime
from Embed_Utilities import *
from Standard_Constants import *
import discord
import csv

async def assign_nick_name(nick_name, user, bot_log_channel):

    try:
        # assign nick_name to user
        await user.edit(nick=nick_name)
        print(f"\n\t( +N ) Assigned name '{nick_name}' to {user.name}")
        return True

    except Exception as e:
        embed = embed_unsuccessful_assign(user,
                                    name=nick_name)
        await bot_log_channel.send(embed=embed)

        print(f"\n\t( -N ) Unable to assign nick name to {user.name}")
        print(f"\t\tIs bot's permisson level above {user.name}?")
        return False

async def assign_role(role, user, bot_log_channel):

    try:
        # Add role to user
        await user.add_roles(role)
        print(f"\t( +R ) Assigned '{STUDENT_ROLE}' role to {user.name}\n")
        return True

    except Exception as e:

        embed = embed_unsuccessful_assign(user,
                                    role=role)
        await bot_log_channel.send(embed=embed)

        print(f"\t( -R ) Unable to assign role to {user.name}")
        print(f"\t\tIs bot's permisson level above {STUDENT_ROLE}?\n")

        return False

# this should go in bot_utilities but im not sure why it won't work
async def handle_message(message, client, guest_list, bot_log_channel, guild):

    users_added = 0

    # Skip messages sent by bot
    if (message.author != client.user):

        # grab nick_name and user objects
        nick_name = message.content.lower()
        user = message.author

        # Check if user doesn't have role
        if (len(user.roles) == 1):

            # check if user is in CSV
            if nick_name in guest_list:

                # format nickname nicely
                nick_name = format_nick_name(nick_name)

                # grab student role
                    #role_id = 1062778282640166973
                role = discord.utils.get(message.guild.roles,
                                                name=STUDENT_ROLE)

                attempt1 = await assign_nick_name(nick_name,
                                                           user,
                                                           bot_log_channel)

                attempt2 = await assign_role(role, user,
                                                bot_log_channel)


                # create success embed
                if (attempt1) and (attempt2):

                    # increase users addeed by 1
                    users_added = 1

                    # send success message
                    embed = embed_successful_assign(nick_name,
                                                        user,
                                                        role)

                    # add BOT_REACTION to message
                    await message.add_reaction(BOT_REACTION)

                    # send success embed to bot channel
                    await bot_log_channel.send(embed=embed)

                    # log to file
                    log_to_file(LOG_FILE, nick_name, user, guild)

            # nick_name is not in student file
            else:
                # create error embed
                embed = embed_user_error(nick_name)

                # send error embed for user to see
                await message.channel.send(message.author.mention,
                                            embed=embed)

                # create error embed
                embed = embed_unsuccessful_assign(user,
                                                name=nick_name)
                # send error embed for log keeping
                await bot_log_channel.send(embed=embed)

                # delete seen message for ease's sake
                    # bot will work without this, but this
                    # declutters the channel a little
                await message.delete()

    return users_added

# function to check if server is current
def is_current_server(guild, current_semester) :

    return current_semester in guild.name.lower()


# formats discord message to prettier nick name
def format_nick_name(nick_name):

    # split the name on spaces
    temp_list = nick_name.split()

    # create an empty string
    formatted_nick = ""

    # Loop through name parts
    for index in range(len(temp_list)):
        # Format the name to be Proper Case
        formatted_nick += f"{temp_list[index][0].upper()}"
        formatted_nick += f"{temp_list[index][1:]} "

    return formatted_nick[:-1] # cuts off end space. fencepost problem!
# function to get welcome channel
def get_channel_objects(guild):

    # get welcome channel
    welcome_channel = discord.utils.get(guild.channels,
                                        name=WELCOME_CHANNEL_NAME)

    # get log channel
    bot_log_channel = discord.utils.get(guild.channels,
                                        name=BOT_CHANNEL_NAME)

    return welcome_channel, bot_log_channel

def get_current_semester_string():

    # Get the current date
    current_date = datetime.now()

    # dates for sping semester
    sp_month_start = 1
    sp_day_start   = 13
    sp_month_end   = 5
    sp_day_end     = 3

    # dates for summer semester
    su_month_start = 5
    su_day_start   = 4
    su_month_end   = 7
    su_day_end     = 31

    # dates for fall semester
    f_month_start  = 8
    f_day_start    = 1
    f_month_end    = 12
    f_day_end      = 27

    # dates for spring semester
    w_month_start  = 12
    w_day_start    = 28
    w_month_end    = 1
    w_day_end      = 12

    # Define the season ranges
    seasons = [
        ('spring',  (datetime(current_date.year, sp_month_start, sp_day_start),
                     datetime(current_date.year, sp_month_end,   sp_day_end))),

        ('summer',  (datetime(current_date.year, su_month_start, su_day_start),
                     datetime(current_date.year, su_month_end,   su_day_end))),

        ('fall',    (datetime(current_date.year, f_month_start, f_day_start),
                     datetime(current_date.year, f_month_end,   f_day_end))),

        ('winter',  (datetime(current_date.year, w_month_start, w_day_start),
                     datetime(current_date.year + 1, w_month_end, w_day_end)))
    ]

    for season, (start_date, end_date) in seasons:

        if start_date <= current_date <= end_date:

            current_season = season

            break

    # Create the desired string
    season_year_str = f"{current_season} {current_date.year}"

    return season_year_str

def get_guest_list(filename):

    # Read guest list from CSV file and convert names to lowercase
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        guest_list = [row[0].lower() for row in reader]

    return guest_list

def get_guild_count(client):
    return len(client.guilds)


# logs new student to file
def log_to_file(filename, name, user, guild):

    now = datetime.now()
    user_display = user.name
    user_id = user.id

    '''
    file should be set up like:
        datetime,server_name,student_name,discord_username
    '''

    with open(filename, "a") as file:

        string = f"{now},{guild.name},{name},{user_display}\n"
        file.write(string)
