from datetime import datetime
from Embed_Utilities import *
from Standard_Constants import *
import discord
import csv

'''
OBSOLETE | Function to assign a nick name to a user

Parameters:
    nick_name: str
        - The name to assign a user
    user: object
        - The user object
    bot_log_channel: object
        - The bot log channel to send success/failure
        messages to

Returns:
    Bool
'''
async def assign_nick_name(nick_name, user, channel):

    try:
        # assign nick_name to user
        await user.edit(nick=nick_name)
        print_formatted(f"( +N ) Assigned name '{nick_name}' to {user.name}", 1)
        return True

    except Exception as e:
        embed = embed_unsuccessful_assign(user, name=nick_name, e=e)
        await channel.send(embed=embed)

        print_formatted(f"( -N ) Unable to assign nick name to {user.name}", 1)
        print_formatted(f"Is bot's permisson level above {user.name}?", 2)
        return False
'''
OBSOLETE | Function to assign a role to a user

Parameters:
    role: object
        - The role to assign a user
    user: object
        - The user object
    bot_log_channel: object
        - The bot log channel to send success/failure
        messages to

Returns: Bool
'''
async def assign_role(role, user, channel):

    # check that role exists
    if role:

        try:
            # Add role to user
            await user.add_roles(role)
            print_formatted(f"( +R ) Assigned '{STUDENT_ROLE}' role to {user.name}\n", 1)
            return True

        except Exception as e:

            embed = embed_unsuccessful_assign(user, role=role, e=e)
            await channel.send(embed=embed)

            print_formatted(f"( -R ) Unable to assign role to {user.name}", 1)
            print_formatted(f"Is bot's permisson level above {STUDENT_ROLE}?\n", 2)

            return False

    # role does not exist
    return False

'''
Function grab dateTime object from a discord channel

Parameters:
    channel: object
        - The name to assign a user
    limit: Double or Str
        - Limits messages to grab

Returns: Datetime object
'''
async def get_timestamp(channel, limit = None):

    async for message in channel.history( limit=limit ):
        timestamp = message.created_at

    return timestamp

'''
Function to handle a message from a user and process it.

Parameters:
    message: object
        - The message object received from the user
    client: object
        - The Discord bot client object
    guest_list: list
        - A list of guest names
    bot_log_channel: object
        - The bot log channel to send messages to
    guild: object
        - The Discord server (guild) where the message was sent

Returns:
    users_added: int
        - The number of users added or processed
'''
async def add_student(guest_list, user, nick_name, role, guild):

    # Check if user only has @everyone role
    if (len(user.roles) == 1):

        if nick_name in guest_list:

            nick_name = format_nick_name(nick_name)
            student_role = get_role(guild, STUDENT_ROLE)

            await user.edit(nick=nick_name)
            print_formatted(f"( +N ) Assigned name '{nick_name}' to {user.name}", 1)

            await user.add_roles(student_role)
            print_formatted(f"( +R ) Assigned '{STUDENT_ROLE}' role to {user.name}\n", 1)

            return True

        # nick_name is not in student file
        return False

'''
Function to check if client can manage role

Parameters:
    client: object
    guild: object
    target_role_name: str
        - The name of the role to be checked


Returns:
    Bool
        - True if client can manage role, false if not
'''
def can_manage_role(client, guild, target_role_name):

    # client = discord.Client(intents=intents)
    target_role = get_role( guild, target_role_name )

    if target_role:

        if guild.me.top_role > target_role:

            return True

        return False

    print_formatted(f"<{target_role_name}> does not exist!", 1)

    return False
'''
Function to get a list of guest names from CANVAS

Returns:
    guest_list: list
        - A list of guest names (in lowercase)
'''
def canv_guest_list( TOKEN ):

    '''
        CODE NEEDED FROM VOVA
    '''

    # returns a list of canvas names
    print("Not yet implemented")
    quit()

'''
OBSOLETE | Function to compare two strings while ignoring spaces and hyphens.

Parameters:
    input_str: str
        - The input string for comparison
    name: str
        - The name to compare with

Returns:
    Bool
        - True if the strings match after removing spaces and hyphens;
        otherwise, False
'''
def compare_strings(input_str, name):
    # Normalize both strings to lowercase and remove spaces and hyphens
    normalized_input = input_str.lower().replace(" ", "").replace("-", "")
    normalized_name = name.lower().replace(" ", "").replace("-", "")

    # Compare the normalized strings
    return normalized_input == normalized_name

'''
Function to get a list of guest names from a CSV file.

Parameters:
    filename: str
        - The filename of the CSV file containing guest names

Returns:
    guest_list: list
        - A list of names (in lowercase)
'''
def csv_guest_list(filename):

     # Initialize an empty list to store the guest names
    guest_list = []

    # Open the CSV file and read the "name" field from each row
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row["name"]

            # Convert the name to lowercase and add it to the guest list
            guest_list.append( name.strip().lower() )

            section = row["lab section"]

            guest_list.append( name.strip().lower() )

    return guest_list

'''
Function to display a menu of program choices.
'''
def display_menu():

    print_formatted("Program Choices", 1)
    print_formatted("[1] Process New Students with .csv")
    print_formatted("[2] Process New Students with Canvas")
    print_formatted("[3] Re-role Former Students")
    print_formatted("[4] Clear *All* Messages in Welcome Channel")
    print_formatted("[5] Assign lab roles to all students")
    print_formatted("[6] Quit")


'''
Function to check if a server (guild) name contains the current semester.

Parameters:
    guild: object
        - The Discord server (guild) object to check
    current_semester: str
        - The current semester string

Returns:
    Bool
        - True if the server name contains the current semester; otherwise, False
'''
# function to check if server is current
def is_current_server(guild, current_semester) :

    return current_semester in guild.name.lower()

'''
Function to format a Discord message into a prettier nickname.

Parameters:
    name: str
        - The original name to format

Returns:
    formatted_name: str
        - The formatted nickname
'''
# formats discord message to prettier nick name
def format_nick_name(name):

    formatted_name = ""

    split_name = name.split(" ")

    for name_parts in split_name:

        if "-" in name_parts:

            hyphen_split = name_parts.split('-')

            for hyphenated_part in hyphen_split:

                formatted_name += hyphenated_part[0].capitalize()
                formatted_name += hyphenated_part[1:] + "-"

            formatted_name = formatted_name[:-1]
            formatted_name += " "
        else:
            formatted_name += name_parts[0].capitalize()
            formatted_name += name_parts[1:] + " "

    return formatted_name

'''
Function to get welcome and bot log channels for a Discord server (guild).

Parameters:
    guild: object
        - The Discord server (guild) object
    channel_name: str
        - The Discord channel name

Returns:
    - channel object
'''
# function to get welcome channel
def get_channel_object(guild, channel_name):

    # get welcome channel
    return discord.utils.get(guild.channels, name=channel_name)


def get_section_list(filename):

    header = "lab section"
    section_list = []

    # 1) cehck if in same csv file "lab section" column exists
    with open(filename, newline='') as csvfile:

        reader = csv.DictReader(csvfile)

        if header not in reader.fieldnames:

            print("The 'lab section' column does not exist.")

            return None

        for row in reader:

            name = row["name"]

            section = row[header]

            # create list of tuples with lab sections and names
            section_list.append( (name.strip().lower(), section) )

    return section_list
'''
Function to get the current semester as a string based on the current date.

Parameters:
    None

Returns:
    current_season_year_str: str
        - The current semester as a string (e.g., "spring 2023")
'''
def get_current_semester_string():

    # Get the current date
    current_date = datetime.now()

    # dates for sping semester (1/13 ~ 5/3)
    sp_month_start = 1
    sp_day_start   = 13
    sp_month_end   = 5
    sp_day_end     = 3

    # dates for summer semester (5/4 ~ 7/31)
    su_month_start = 5
    su_day_start   = 4
    su_month_end   = 7
    su_day_end     = 31

    # dates for fall semester (8/1 ~ 12/17)
    f_month_start  = 8
    f_day_start    = 1
    f_month_end    = 12
    f_day_end      = 27

    # dates for winter semester (12/28 ~ 1/12)
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

'''
Function to get the count of Discord servers (guilds) that the bot is a member of.

Parameters:
    client: object
        - The Discord bot client object

Returns:
    guild_count: int
        - The count of Discord servers (guilds)
'''
def get_guild_count(client):
    return len(client.guilds)

'''
Function to convert a list of guest names to lowercase.

Parameters:
    guest_list: list
        - A list of guest names

Returns:
    lower_guest_list: list
        - A list of guest names in lowercase
'''
def get_lower_guest_list(guest_list):

    lower_guest_list = []
    for guest in guest_list:
        lower_guest_list.append(guest.lower())

    return lower_guest_list

'''
Function to retrieve a Discord role by its name within a given guild (server).

Parameters:
    role_name: str
        - The name of the role to retrieve

Returns:
    role: object
        - The Discord role object with the specified name, or None if not found
'''
def get_role( guild, role_name):
    return discord.utils.get(guild.roles, name=role_name)

'''
Function to log a new student's information to a file.

    format:
    <datetime>,<server_name>,<student_name>,<discord_username>

Parameters:
    filename: str
        - The filename of the log file
    name: str
        - The student's name
    user: object
        - The user object
    guild: object
        - The Discord server (guild) object where the user is from


'''
def log_to_file(filename, name, user, guild):

    now = datetime.now()
    user_display = user.name
    user_id = user.id

    with open(filename, "a") as file:

        string = f"{now},{guild.name},{name},{user_display}\n"
        file.write(string)

'''
Function to print a formatted message with indentation.

Parameters:
    string: str
        - The message to print
    tabs: int (optional)
        - The number of tabs to indent the message
'''
def print_formatted(string, tabs=0):

        print("\t" * (tabs + 1), end = "")
        print(string)
