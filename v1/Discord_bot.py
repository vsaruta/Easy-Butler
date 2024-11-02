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
    LONG_LINE = "======================================================"

    # Intents for the bot, this allows the bot to read the members of the server
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True

    # Create the bot client, with a prefix of .
        # prefix irrelevant in butler bot
    client = commands.Bot(command_prefix='.', intents=intents)

    print()
    print(LONG_LINE)

    # ask for menu choice
    display_menu()

    while ( menu_choice < 0 ) or ( menu_choice > 6 ):

        try:
            menu_choice = int(input("\n\tChoose Program: "))

        except ValueError:
            menu_choice = -1

    if (menu_choice == 6):
        print_formatted( "Ended program." )
        quit()

    print(LONG_LINE)
    print_formatted( "Beginning Program..." )

    @client.event
    async def on_ready():

        # Begin running bot
        print_formatted( f"Running {client.user.name}\n" )

        # check if client in any guilds
        if ( get_guild_count(client) == 0 ):

            # print error message
            print_formatted( "Error: Bot is in no servers.", 1 )
            print_formatted( f"Ending {client.user.name}", 1 )

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

                # option 1, 2: process_new_students
                if menu_choice == 1 or menu_choice == 2:

                    # CSV guest list or Canvas guest_list
                    if menu_choice == 1:
                        guest_list = csv_guest_list( CSV_FILE )
                    else:

                        guest_list = canv_guest_list( CANVAS_TOKEN )

                    # check if both bot channel + welcome channel
                    if ( welcome_channel and bot_log_channel ):

                        # check if bot is able to assign role
                        if can_manage_role( client, guild, STUDENT_ROLE ):

                            # process new students
                            await process_new_students( client, guild,
                                                                welcome_channel,
                                                                bot_log_channel,
                                                                guest_list)


                        # bot cannot assign role
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

                # option 3:
                    # function: rerole_former_students
                elif menu_choice == 3:

                    # check if bot_log_channel exists
                    if bot_log_channel:

                        # check if bot can manage role
                        if (can_manage_role( client, guild, STUDENT_ROLE ) and
                            can_manage_role( client, guild, FORMER_ROLE ) ):

                            await rerole_former_students( client, guild,
                                                                bot_log_channel)
                        # bot cannot manage role
                        else:
                            print_formatted(f"Bot unable to manage <{STUDENT_ROLE}>" +
                                f" and <{FORMER_ROLE}>.", 1)

                    # server set up incorrectly for this action
                    else:

                        # print to console
                        print_formatted("Server set up incorrectly:", 1)

                        #print error
                        print_formatted(f"#{BOT_CHANNEL_NAME} not found.", 1)


                # option 4:
                    # function: clean up welcome-channel
                elif menu_choice == 4:

                    # clean channel, grab messages deleted
                    messages = await clean_channel(welcome_channel, bot_log_channel)

                    m = f"Messages deleted: {messages}"
                    print_formatted(m, 1)

                elif menu_choice == 5:

                    student_role = get_role(guild, STUDENT_ROLE)
                    section_list = get_section_list(CSV_FILE)

                    if section_list:

                        # 2) If yes, go through users
                        for user in guild.members:

                            # if user has student role and < 3 roles
                            if student_role in user.roles and len(user.roles) < 3:

                                # grab student name
                                nick_name = user.nick.lower()

                                # find name in section_list
                                for name, section in section_list:

                                    if nick_name == name:

                                        # grab appropriate section (1,2,3 etc) role
                                        role = get_role( guild, section )

                                        await user.add_roles(role)
                                        print_formatted(f"( +R ) Assigned '{section}' role to {user.name}\n", 1)


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
    print(secret.TOKEN)
    client.run( secret.TOKEN )


# Function: process_new_students()
async def process_new_students( client, guild, welcome_channel,
                                                bot_log_channel,
                                                guest_list):
    desc = "Processing Students"
    users_added = 0
    message_count = 0
    role = get_role(guild, STUDENT_ROLE)

    # send to log channel that processing has started
    # embed_start_end_bot(menu, state, channel=None, users_added = 0, messages = 0):
    embed = embed_start_bot( desc, welcome_channel )
    await bot_log_channel.send( embed=embed )

    # print scanning has started
    print_formatted( f"Scanning messages in #{WELCOME_CHANNEL_NAME}", 1 )

    # Fetch all messages in the welcome channel
        # change to after=timestamp for better efficiency
        # reverse = True: Will grab messages from the bottom and go
        # to the top
    async for message in welcome_channel.history( limit = None ):

        # increase message count
        message_count += 1

        # Check that bot is above user's role
            # Bot will ignore anybody above its permissions
        if guild.me.top_role >= message.author.top_role:

            # check if messages sent by bot and has a mention in it
            if (message.author == client.user) and (message.mentions):

                # Loop through all mentioned users in the message
                for mentioned_user in message.mentions:

                    # Check if the mentioned user has the "STUDENT" role
                    user = guild.get_member(mentioned_user.id)

                    # Check if they have any role
                    if (len(user.roles) > 1):

                        # Delete the message
                        await message.delete()

                        # break out, no more mentions
                        break

            # message not sent by bot
            else:

                # grab user object and nick name str
                user = message.author

                # Grab nick name
                nick_name = message.content.lower()

                # Handle the messages, return the users added
                added_user = await add_student( guest_list, user, nick_name,
                                                                role, guild )

                # format name
                fname = format_nick_name(nick_name)

                # check if user was added
                if ( added_user ):

                    # send success message
                    embed = embed_successful_assign(fname, user, role)

                    # send success embed to bot channel
                    await bot_log_channel.send(embed=embed)

                    users_added += 1

                else:
                    # catches if student has been added but they
                    # said invalid stuff after added
                    if (role not in user.roles):

                        # create error embed
                        embed = embed_user_error(fname)

                        # send error embed for user to see
                        await message.channel.send(message.author.mention,
                                                    embed=embed)

                        # create error embed
                        embed = embed_unsuccessful_assign(user,
                                                        name=nick_name,
                                                        e="Nickname not in guest list")
                        # send error embed for log keeping
                        await bot_log_channel.send(embed=embed)

                # delete user message
                await message.delete()

                # wait for wait limit, if thats an issue.
                time.sleep( WAIT_FOR_RATE_LIMIT )

    # Print a log message once all the messages have been
        # processed
    print_formatted(f"End: " +
        f"Processed {message_count} messages in '{guild.name}'")

    embed = embed_end_bot(desc, welcome_channel, users_added, message_count )

    await bot_log_channel.send( embed=embed )

# Function: rerole_former_students( client, guild, bot_log_channel )
async def rerole_former_students( client, guild, bot_log_channel ):

    desc = "Re-roling Former Students"
    # send message to bot channel
    embed = embed_start_bot(desc)
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

            # increase users assigned
            users_reassigned += 1

    embed = embed_end_bot(desc, users_added = users_reassigned )
    await bot_log_channel.send( embed=embed )

# Function: clean_welcome ( client, guild )
# Delete message in welcome if succssfully added to Students and Renamed them
async def clean_channel( channel , bot_log_channel):

    # declare Variables
    messages = 0
    desc = "Clearing Channel"

    embed = embed_start_bot( desc, channel )
    await bot_log_channel.send( embed=embed )

    # print scanning has started
    print_formatted( f"Deleting messages in #{channel.name}", 1 )

    async for message in channel.history( limit = None ):

        m = f"Deleing message by {message.author.name}:"
        print_formatted( m, 1)

        m = f"Content: {message.content}"
        print_formatted( m, 2)

        m = f"Timestamp: {message.created_at}"
        print_formatted( m, 2)

        await message.delete()

        messages += 1

    embed = embed_end_bot( desc, channel = channel, messages = messages)
    await bot_log_channel.send( embed=embed )

    return messages
