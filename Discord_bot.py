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

    # Intents for the bot, this allows the bot to read the members of the server
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True

    # Create the bot client, with a prefix of .
        # prefix irrelevant in butler bot
    client = commands.Bot(command_prefix='.', intents=intents)

    @client.event
    async def on_ready():

        # Begin running bot
        print(f"- Running {client.user.name}")

        # get semester name
        current_semester = get_current_semester_string()

        # check if client in any guilds
        if ( get_guild_count(client) == 0 ):

            # print error message
            print("- Error: Bot is in no servers.")

            print( f"- Ending {client.user.name}" )

            # leave if no guilds
            await client.close()

        # iterate through guilds
        for guild in client.guilds:

            # begin processing guild
            print(f"\n- Processing: '{guild.name}'")

            # get welcome + bot channel
            welcome_channel, bot_log_channel = get_channel_objects(guild)

            # check if server is current
            if ( is_current_server( guild, current_semester ) ):

                # check if both bot channel + welcome channel
                if ( welcome_channel and bot_log_channel ):

                    # send to log channel that processing has started
                    embed = embed_start_end_bot( "Started", welcome_channel )
                    await bot_log_channel.send( embed=embed )

                    # get guest list
                    guest_list = get_guest_list( CSV_FILE )

                    # initialize count for users added
                    users_added = 0

                    # print scanning has started
                    print( f"\t- Scanning messages in #{WELCOME_CHANNEL_NAME}" )

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
                            users_added += await handle_message(message, client,
                                                                guest_list,
                                                                bot_log_channel,
                                                                guild)

                            # wait for wait limit, if thats an issue.
                            time.sleep( WAIT_FOR_RATE_LIMIT )

                        # embed for KeyboardInterrupt
                        except KeyboardInterrupt as e:
                            print(f" - End search for '{guild.name}'\n")
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
                    print(f"- End: " +
                        f"Processed {message_count} messages in '{guild.name}'")

                    embed = embed_start_end_bot( "Finished", welcome_channel,
                                                                users_added,
                                                                message_count )
                    await bot_log_channel.send( embed=embed )

                # server does not have proper channels
                else:
                    # print to console
                    print("\t- Server set up incorrectly:")

                    # if no welcome channel
                    if not welcome_channel:

                        #print error
                        print(f"\t- #{WELCOME_CHANNEL_NAME} not found.")

                    # if no bot channel
                    if not bot_log_channel:

                        #print error
                        print(f"\t- #{BOT_CHANNEL_NAME} not found.")

            # server name does not include
            else:
                # print to console
                print(f"\t- Leaving '{guild.name}' - does not include "
                        + f"'{current_semester}' in server name.")

                # Send embed only if set up correctly
                if bot_log_channel:
                    embed = embed_leave_message( current_semester )
                    await bot_log_channel.send( embed=embed )

                # leave the guilds
                await guild.leave()

                # check if client in any more guilds
                if ( get_guild_count(client) == 0 ):

                    # print error message
                    print("- Error: Bot is in no more servers.")

                    print( f"- Ending {client.user.name}" )
                    # leave if no guilds
                    await client.close()

        # all guilds have been iterated through, close
        print()
        print( f"- Ending {client.user.name}" )

        # close client
        await client.close()

    # run client
    client.run( secret.TOKEN )

run_discord_bot()
