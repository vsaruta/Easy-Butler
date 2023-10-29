from Embed_Utilities import *
from Bot_Utilities import *
from Standard_Constants import *
from discord.ext import commands
from datetime import datetime
import discord
import time
import csv
import secret

def run_discord_bot():
    # Initilize variables
    # get semester name
    current_semester = get_current_semester_string()
    menu_choice = -1

    # Intents for the bot, this allows the bot to read the members of the server
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True

    # Create the bot client, with a prefix of .
        # prefix irrelevant in butler bot
    client = commands.Bot(command_prefix='.', intents=intents)

    # ask for menu choice
    display_menu()

    while (menu_choice < 0) or (menu_choice > 3):

        try:
            menu_choice = int(input("Choose Program: "))

        except ValueError:
            menu_choice = -1

    print_formatted("Beginning Program...")

    @client.event
    async def on_ready():

        # Begin running bot
        print_formatted(f"Running {client.user.name}")

        # check if client in any guilds
        if ( get_guild_count(client) == 0 ):

            # print error message
            print_formatted("Error: Bot is in no servers.", 1)

            print_formatted(f"Ending {client.user.name}", 1)

            # leave if no guilds
            await client.close()

        # iterate through guilds
        for guild in client.guilds:

            # begin processing guild
            print_formatted(f"Processing: '{guild.name}'")

            # get welcome + bot channel
            welcome_channel = get_channel_object(guild, WELCOME_CHANNEL_NAME)
            bot_log_channel = get_channel_object(guild, BOT_CHANNEL_NAME)

            # check if server is current
            if ( is_current_server( guild, current_semester ) ):

                # option 1: process_new_students
                if menu_choice == 1:

                    # check if both bot channel + welcome channel
                    if ( welcome_channel and bot_log_channel ):

                        if can_manage_role( client, guild, STUDENT_ROLE ):

                            # process new students
                            # TODO: link STUDENT_ROLE to handle_message
                            await process_new_students( client, guild,
                                                                welcome_channel,
                                                                bot_log_channel)
                        else:
                            print_formatted(f"Bot unable to manage <{STUDENT_ROLE}>.", 1)

                    # server does not have proper channels
                    else:
                        # print to console
                        print_formatted("Server set up incorrectly:", 1)

                        # if no welcome channel
                        if not welcome_channel:

                            #print error
                            print_formatted(f"#{WELCOME_CHANNEL_NAME} not found.", 1)

                        # if no bot channel
                        if not bot_log_channel:

                            #print error
                            print_formatted(f"#{BOT_CHANNEL_NAME} not found.", 1)

                # option 2:
                    # function: rerole_former_students
                elif menu_choice == 2:

                    # check if bot_log_channel exists
                    if bot_log_channel:

                        if (can_manage_role( client, guild, STUDENT_ROLE ) and
                            can_manage_role( client, guild, FORMER_ROLE ) ):

                            await rerole_former_students( client, guild,
                                                                bot_log_channel)

                        else:
                            print_formatted(f"Bot unable to manage <{STUDENT_ROLE}>" +
                                f" and <{FORMER_ROLE}>.", 1)

                    else:

                        # print to console
                        print_formatted("Server set up incorrectly:", 1)

                        #print error
                        print_formatted(f"#{BOT_CHANNEL_NAME} not found.", 1)


                # option 3:
                    # function: clean up welcome-channel
                elif menu_choice == 3:
                    pass

            # server name does not include correct naming
            else:
                # print to console
                print_formatted(f"Leaving '{guild.name}' - does not include "
                        + f"'{current_semester}' in server name.", 1)

                # Send embed only if set up correctly
                if bot_log_channel:
                    embed = embed_leave_message( current_semester )
                    await bot_log_channel.send( embed=embed )

                # leave the guilds
                await guild.leave()

                # check if client in any more guilds
                if ( get_guild_count(client) == 0 ):

                    # print error message
                    print_formatted("Error: Bot is in no more servers.")

                    print_formatted( f"Ending {client.user.name}" )
                    # leave if no guilds
                    await client.close()

        # all guilds have been iterated through, close
        print()
        print_formatted( f"Ending {client.user.name}" )

        # close client
        await client.close()

    # run client
    client.run( secret.TOKEN )

# Function: process_new_students( client, guild )
async def process_new_students( client, guild, welcome_channel,
                                                            bot_log_channel ):

    # send to log channel that processing has started
    # embed_start_end_bot(menu, state, channel=None, users_added = 0, messages = 0):
    embed = embed_start_end_bot( 1, "Started", channel=welcome_channel )
    await bot_log_channel.send( embed=embed )

    # get guest list
        # guest list is in LOWER
    guest_list = get_guest_list( CSV_FILE )

    # initialize count for users added
    users_added = 0

    # print scanning has started
    print_formatted( f"Scanning messages in #{WELCOME_CHANNEL_NAME}", 1 )

    timestamp = await get_timestamp(bot_log_channel, limit=2)

    message_count = 0

    # Fetch all messages in the welcome channel
        # change to after=timestamp for better efficiency
    async for message in welcome_channel.history( around=
                                        timestamp ):

        # increase message count
        message_count += 1

        # try to handle message
        try:
            # Handle the messages, return the users added
            users_added += await handle_message(message,
                                                client,
                                                guest_list,
                                                bot_log_channel,
                                                guild)

            # wait for wait limit, if thats an issue.
            time.sleep( WAIT_FOR_RATE_LIMIT )

        # embed for KeyboardInterrupt
        except KeyboardInterrupt as e:
            print_formatted(f"End search for '{guild.name}'")
            embed = embed_abrupt_end( "KeyboardInterrupt",
                                                users_added )
            await bot_log_channel.send( embed=embed )
            await client.close()

        # embed exception if anything else goes awry
        except Exception as e:
            embed = embed_abrupt_end( "Error", users_added,
                                                    str(e) )
            await bot_log_channel.send( embed=embed )
            raise e
            await client.close()

    # Print a log message once all the messages have been
        # processed
    print_formatted(f"End: " +
        f"Processed {message_count} messages in '{guild.name}'")

    embed = embed_start_end_bot( 1, "Finished", welcome_channel,
                                                users_added,
                                                message_count )
    await bot_log_channel.send( embed=embed )

# Function: rerole_former_students( client, guild, bot_log_channel )
async def rerole_former_students( client, guild, bot_log_channel ):

    # send message to bot channel
    embed = embed_start_end_bot( 2, "Started")
    await bot_log_channel.send( embed=embed )

    users_reassigned = 0

    # get roles
    old_role = get_role(guild, STUDENT_ROLE)
    new_role = get_role(guild, FORMER_ROLE)

    # loop through members in server
    for member in guild.members:

        # check if member has student role
        if old_role in member.roles:

            # remove old role
            await member.remove_roles(old_role)

            # add new role
            await member.add_roles(new_role)

            # print to console
            m = f"Changed {member.name} from <{old_role.name}> to <{new_role.name}>."
            print_formatted(m, 1)

            # send success
                # TODO: check if actually successful...
            embed = embed_successful_rerole( member, old_role, new_role )

            await bot_log_channel.send( embed=embed )

            users_reassigned += 1

    # embed_start_end_bot(menu, state, channel=None, users_added = 0, messages = 0)
    embed = embed_start_end_bot( 2, "Finished", users_added = users_reassigned)
    await bot_log_channel.send( embed=embed )

# Function: clean_welcome ( client, guild)

# Run bot
run_discord_bot()
