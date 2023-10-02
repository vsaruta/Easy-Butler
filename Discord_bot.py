from discord.ext import commands
from datetime import datetime
import discord
import time
import sys
import csv
import secret

# Customization :)
CSV_FILE = "fall_2023_cs126_names.csv"
CURRENT_SEMESTER = "Fall 2023"
LOG_FILE = "discord_log.txt"
STUDENT_ROLE = "Students"
START_MESSAGE = "Started"
END_MESSGAE = "Finished"
WELCOME_CHANNEL_NAME = "welcome"
BOT_CHANNEL_NAME = "bot_log"
NEUTRAL_COLOR = 0x4895FF # hex
CAUTION_COLOR = 0xFFF253 # hex
SUCCESS_COLOR = 0x21D375 # hex
ERROR_COLOR   = 0xF95C52 # hex
WAIT_FOR_RATE_LIMIT = 0.2 # in seconds
BOT_REACTION = '👍'

def run_discord_bot():

    # Intents for the bot, this allows the bot to read the members of the server
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True

    # Create the bot client, with a prefix of .
        # irrelegant in butler bot
    client = commands.Bot(command_prefix='.', intents=intents)

    @client.event
    async def on_ready():

        await close_if_no_guilds(client)

        for guild in client.guilds:

            # get welcome channel
                # This could also be done with the channel ID
            welcome_channel = discord.utils.get(guild.channels,
                                                name=WELCOME_CHANNEL_NAME)

            # get log channel
            bot_log_channel = discord.utils.get(guild.channels,
                                                name=BOT_CHANNEL_NAME)

            # initialize count for users added
            users_added = 0

            print(f"\nProcessing '{guild.name}'")

            # Leave old semester servers
            if CURRENT_SEMESTER not in guild.name:

                # print to console
                print(f"\tLeaving '{guild.name}' - Old Semester")

                # Send embed only if set up correctly
                if guild_correctly_set_up(guild):
                    embed = embed_leave_message()
                    await bot_log_channel.send(embed=embed)

                # leave the server
                await guild.leave()

                await close_if_no_guilds(client)

            # check if both welcome and bot log channel
            else:
                if not guild_correctly_set_up(guild):

                    print(f"\t'{guild.name}' Set up incorrectly.")
                    print(f"\tPlease check if {guild.name} has both")
                    print(f"\t#{WELCOME_CHANNEL_NAME} and #{BOT_CHANNEL_NAME}")
                    print(f"\tEnd search for '{guild.name}'\n")

                # guild is set up correctly
                else:
                    # get guest list
                    guest_list = get_guest_list(CSV_FILE)

                    # send to log channel that processing has started
                    embed = embed_start_end_bot(START_MESSAGE, welcome_channel)
                    await bot_log_channel.send(embed=embed)

                    print(f"\tScanning messages in #{WELCOME_CHANNEL_NAME}")

                    # Fetch all messages in the welcome channel
                    async for message in welcome_channel.history(limit=None):

                        try:
                            # Handle the messages, return the users added
                            users_added += await handle_message(message, client,
                                                                guest_list,
                                                                bot_log_channel)

                            # wait for wait limit, if thats an issue.
                            time.sleep(WAIT_FOR_RATE_LIMIT)

                        # raise exception if anything else goes awry
                        except KeyboardInterrupt as e:
                            print(f"\tEnd search for '{guild.name}'\n")
                            embed = embed_abrupt_end("KeyboardInterrupt",
                                                                users_added)
                            await bot_log_channel.send(embed=embed)
                            await client.close()

                        except:
                            embed = embed_abrupt_end("Error",
                                                                users_added)
                            await bot_log_channel.send(embed=embed)
                            await client.close()


                    # Print a log message once all the messages have been
                        # processed
                    print(f"\tEnd search for '{guild.name}'")
                    embed = embed_start_end_bot(END_MESSGAE, welcome_channel,
                                                                users_added)
                    await bot_log_channel.send(embed=embed)
                    # End run

        await client.close()

    # run client
    client.run(secret.TOKEN)

async def assign_nick_name(nick_name, user):

    try:
        # assign nick_name to user
        await user.edit(nick=nick_name)
        print(f"\tAssigned '{nick_name}' to " +
                                f"{user.name}")
        return True

    except Exception as e:
        embed = embed_unsuccessful_assign(user,
                                    name=nick_name)
        await bot_log_channel.send(embed=embed)

        print("\tUnable to assign nick name to " +
                                f"{user.name}")
        return False


async def assign_role(role, user, bot_log_channel):

    try:
        # Add role to user
        await user.add_roles(role)
        print(f"\tAssigned '{STUDENT_ROLE}' role to " +
                               f"{user.name}")
        return True

    except Exception as e:

        embed = embed_unsuccessful_assign(user,
                                    role=role)
        await bot_log_channel.send(embed=embed)

        print("\tUnable to assign role to " +
                               f"{user.name}")
        print(f"\t\tIs bot's permisson level "+
                f"above {STUDENT_ROLE}?")

        return False

async def close_if_no_guilds(client):

    # check if bot is not in any servers
    if len(client.guilds) == 0:
        print("Error: Bot is in no servers.")
        await client.close()

def guild_correctly_set_up(guild):

    guild_channels = []

    for channel in guild.channels:

        # put channel name in list
        guild_channels.append(channel.name)

    if (WELCOME_CHANNEL_NAME not in guild_channels):
        return False

    if (BOT_CHANNEL_NAME not in guild_channels):
        return False

    return True

async def handle_message(message, client, guest_list, bot_log_channel):

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
                                                           user)

                attempt2 = await assign_role(role, user,
                                                bot_log_channel)


                # create success embed
                if (attempt1) and (attempt2):

                    users_added += 1

                    embed = embed_successful_assign(nick_name,
                                                        user,
                                                        role)

                    # add BOT_REACTION to message
                    await message.add_reaction(BOT_REACTION)

                    # send success embed to bot channel
                    await bot_log_channel.send(embed=embed)

                    # log to file
                    log_to_file(LOG_FILE, nick_name, user)

                    # increase users added count

            # nick_name is not in student file
            else:
                # create error embed
                embed = embed_user_error(nick_name)

                # send error embed
                await message.channel.send(message.author.mention,
                                            embed=embed)

                embed = embed_unsuccessful_assign(user,
                                                name=nick_name)

                await bot_log_channel.send(embed=embed)

                # delete seen message for ease's sake
                    # bot will work without this, but this
                    # declutters the channel a little
                await message.delete()

    return users_added

# embed for unexpected end
def embed_abrupt_end(type, users_added):

    now = datetime.now()

    embed = discord.Embed(title=f"{type}: Bot Stopped Unexpectedly.",
                    color = CAUTION_COLOR)

    embed.add_field(name=f"Students added in batch: {users_added}",
                    value = "",
                    inline=False)

    embed.set_footer(text=f"{now}")

    return embed

# embed for unsuccessful assigning of type
def embed_client_error(user, type):

    now = datetime.now()

    embed = discord.Embed(title=f"Unable to add {type} to {user.name}",
                    color = ERROR_COLOR)

    embed.set_footer(text=f"{now}")

    return embed

def embed_leave_message():

    now = datetime.now()

    embed = discord.Embed(title=f"Left Server - Old Semester",
                    description=f"Leaving all servers without " +
                                f"{CURRENT_SEMESTER} in its name.",
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

    if (state == END_MESSGAE):

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

    embed.set_footer(text=f"{now}")

    return embed

# embed for unsuccessful assign of nick_name
    # triggers when attempted name is not in guest_list
    # - for use in bot log channel
def embed_unsuccessful_assign(user, name=None, role=None):
        now = datetime.now()
        user_display = user.name
        user_id = user.id

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
                    value = "Name not recognized. " +
                    "Please type your name " +
                    "exactly as it is in canvas.",
                    inline=False)

    embed.set_footer(text=f"{now} - " +
        "If you believe this was a mistake, please inform an admin.")

    return embed

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

# grabs guest list from filename for nick names to be compared to
def get_guest_list(filename):

    # Read guest list from CSV file and convert names to lowercase
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        guest_list = [row[0].lower() for row in reader]

    return guest_list

# logs new student to file
def log_to_file(filename, name, user):

    now = datetime.now()
    user_display = user.name
    user_id = user.id

    '''
    file should be set up like:
        datetime,name,discord_username,user_id
    '''

    with open(filename, "a") as file:

        string = f"{now},{name},{user_display},{user_id}\n"
        file.write(string)

run_discord_bot()
