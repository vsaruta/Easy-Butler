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
WAIT_FOR_RATE_LIMIT = 0.05 # in seconds
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


        # get welcome channel
            # This could also be done with the channel ID
        welcome_channel = discord.utils.get(client.get_all_channels(),
                                            name=WELCOME_CHANNEL_NAME)

        # get log channel
        bot_log_channel = discord.utils.get(client.get_all_channels(),
                                            name=BOT_CHANNEL_NAME)
        # check if bot is not in any servers
        if len(client.guilds) == 0:
            print("Error: Bot is in no servers.")
            await client.close()

         # Iterate through the bot's joined servers (guilds)
        for guild in client.guilds:

            if CURRENT_SEMESTER not in guild.name:

                print(f"Leaving {guild.name} - Old Semester")

                # Send embed only if set up correctly
                if guild_correctly_set_up(guild):
                    embed = embed_leave_message()
                    await bot_log_channel.send(embed=embed)

                await guild.leave() # leave the server

                if len(client.guilds) == 0:
                    print("Bot is in no servers.")
                    await client.close()
                break

            # check if both welcome and bot log channel
            if not guild_correctly_set_up(guild):

                print(f"{guild.name} Set up incorrectly.")
                print(f"\tPlease checK if {guild.name} has both")
                print(f"\t#{WELCOME_CHANNEL_NAME} and #{BOT_CHANNEL_NAME}")

                break

            # get guest list
            guest_list = get_guest_list(CSV_FILE)

            # send to log channel that processing has started
            embed = embed_start_end_bot(START_MESSAGE, welcome_channel)
            await bot_log_channel.send(embed=embed)

            # initialize count for users added
            users_added = 0

            print(f"Scanning messages in #{WELCOME_CHANNEL_NAME}")

            try:
                # Fetch all messages in the welcome channel
                async for message in welcome_channel.history(limit=None):

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

                                try:
                                    # assign nick_name to user
                                    await user.edit(nick=nick_name)
                                    print(f"Assigned {nick_name} to " +
                                                            f"{user.name}")

                                except Exception as e:
                                    print("Unable to assign nick name to " +
                                                            f"{user.name}")
                                    raise e
                                    break

                                # grab student role
                                    #role_id = 1062778282640166973
                                role = discord.utils.get(message.guild.roles,
                                                            name=STUDENT_ROLE)

                                try:
                                    # Add role to user
                                    await user.add_roles(role)
                                    print(f"Assigned {STUDENT_ROLE} role to " +
                                                           f"{user.name}")

                                except Exception as e:
                                    print("Unable to assign role to " +
                                                           f"{user.name}")
                                    raise e
                                    break

                                # create success embed
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
                                users_added += 1

                            # nick_name is not in student file
                            else:
                                # create error embed
                                embed = embed_user_error(nick_name)

                                # send error embed
                                await message.channel.send(message.author.mention,
                                                            embed=embed)

                                embed = embed_unsuccessful_assign(nick_name,
                                                                       user)
                                await bot_log_channel.send(embed=embed)

                                # delete seen message for ease's sake
                                    # bot will work without this, but this
                                    # declutters the channel a little
                                await message.delete()

                    # wait for wait limit, if thats an issue.
                    time.sleep(WAIT_FOR_RATE_LIMIT)

                # Print a log message once all the messages have been processed
                embed = embed_start_end_bot(END_MESSGAE, welcome_channel,
                                                                users_added)
                await bot_log_channel.send(embed=embed)

            # end bot operations by terminal and send a message
            except KeyboardInterrupt as e:

                embed = embed_abrupt_end("KeyboardInterrupt", users_added)
                await bot_log_channel.send(embed=embed)

            # raise exception if anything else goes awry
            except Exception as e:

                embed = embed_abrupt_end("Error", users_added)
                await bot_log_channel.send(embed=embed)
                raise e

            finally:
                # end message to console
                print("Ending program.")

                # End run
                await client.close()

    # run client
    client.run(secret.TOKEN)

def guild_correctly_set_up(guild):

    guild_channels = []

    for channel in guild.channels:

        # put channel name in list
        guild_channels.append(channel.name)

    if (WELCOME_CHANNEL_NAME not in guild_channels) or (BOT_CHANNEL_NAME not in guild_channels):
        return False

    return True

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

# embed for unsuccessful assign of role
    # triggers when attempted name is not in guest_list
    # - for use in bot log channel
def embed_unsuccessful_assign(name, user):
        now = datetime.now()
        user_display = user.name
        user_id = user.id

        embed = discord.Embed(title=f"Unable to Add New Student",
                        color = ERROR_COLOR)

        embed.add_field(name=f"Attempted Name",
                        value=f"{name}",
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
