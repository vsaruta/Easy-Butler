from discord.ext import commands
from datetime import datetime
import discord
import time
import csv
import secret

CSV_FILE = "fall_2023_cs126_names.csv"
LOG_FILE = "discord_log.txt"
STUDENT_ROLE = "Students"
START_MESSAGE = "Started"
END_MESSGAE = "Finished"
WELCOME_CHANNEL_NAME = "welcome"
BOT_CHANNEL_NAME = "bot_log"
NEUTRAL_COLOR = 0x4895FF
SUCCESS_COLOR = 0x21D375
ERROR_COLOR   = 0xb30000
WAIT_FOR_RATE_LIMIT = 0

def run_discord_bot():

    # Intents for the bot, this allows the bot to read the members of the server
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True

    # Create the bot client, with a prefix of .
    client = commands.Bot(command_prefix='.', intents=intents)

    @client.event
    async def on_ready():

        # get welcome channel
        welcome_channel = discord.utils.get(client.get_all_channels(),
                                            name=WELCOME_CHANNEL_NAME)

        # get log channel
        bot_log_channel = discord.utils.get(client.get_all_channels(),
                                            name=BOT_CHANNEL_NAME)

        # get guest list
        guest_list = get_guest_list(CSV_FILE)

        # send to log channel that processing has started
        embed = embed_start_end_bot(START_MESSAGE)
        await bot_log_channel.send(embed=embed)

        # initialize count for users added
        users_added = 0

        try:
            # Fetch all messages in the welcome channel
            async for message in welcome_channel.history(limit=None):

                # Skip messages sent by bot or admins
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

                            # assign nick_name to user
                            await user.edit(nick=nick_name)

                            # grab student role
                                #role_id = 1062778282640166973
                            role = discord.utils.get(message.guild.roles,
                                                        name=STUDENT_ROLE)

                            # Add role to user
                            await user.add_roles(role)

                            # create success embed
                            embed = embed_successful_assign(nick_name, user)

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

                time.sleep(WAIT_FOR_RATE_LIMIT)
                # delete seen message for ease's sake
                    # bot will work without this, but this declutters the
                    # channel a little
                #await message.delete()

            # Print a log message once all the messages have been processed
            embed = embed_start_end_bot(END_MESSGAE, users_added)
            await bot_log_channel.send(embed=embed)


        # raise exception if anything goes awry
        except Exception as e:
            raise e

            # DOES NOT WORK?
            embed = embed_start_end_bot(END_MESSGAE)
            await bot_log_channel.send(embed=embed)

        # End run
        await client.close()

    # run client
    client.run(secret.TOKEN)

def embed_client_error(user, type):

    embed = discord.Embed(title=f"Unable to add {type} to {user.name}",
                    color = ERROR_COLOR)

    embed.set_footer(text=f"{now}")

    return embed

def embed_start_end_bot(state, users_added = 0):

    now = datetime.now()

    embed = discord.Embed(title=f"{state} processing chat log.",
                        color = NEUTRAL_COLOR)

    embed.set_footer(text=f"{now}")

    if state == END_MESSGAE:

        embed.add_field(name=f"Students added in batch: {users_added}",
                        value = "",
                        inline=False)
    return embed

def embed_successful_assign(name, user):

    now = datetime.now()
    user_display = user.name
    user_id = user.id

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

    embed.set_footer(text=f"{now}")

    return embed

def embed_user_error(nick_name):

    now = datetime.now()
    embed = discord.Embed(title=f"Name Not Recognized",
                        color = ERROR_COLOR)

    embed.add_field(name=f"{nick_name}",
                    value = "Name not recognized. " +
                    "Please type your name " +
                    "exactly as it is in canvas.",
                    inline=False)

    embed.set_footer(text=f"{now}")

    return embed

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

    return formatted_nick

def get_guest_list(filename):

    # Read guest list from CSV file and convert names to lowercase
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        guest_list = [row[0].lower() for row in reader]

    return guest_list


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
