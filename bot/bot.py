import discord
import secret as sc
import config as cfg
from classes.Bot import Bot
from discord.ext import tasks
import classes.EmbedHandler

def run_discord_bot():

    # Set up bot
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client( intents=intents )

    # initialize variables
    name      = cfg.name
    prefix    = cfg.prefix
    token     = sc.TOKEN

    # initialize bot
    bot = Bot(name, client, prefix, token)

    # Task loop to update data periodically
    @tasks.loop(hours=cfg.HOURS_UPDATE)  
    async def passive_update_database():
        bot._update_database() 

    @client.event
    async def on_guild_join(guild): # check if we need to update bot on a new join
        success = await bot.initialize_guilds()

    # Show bot logged on successfully
    @client.event
    async def on_ready():

        # change bot's presence
        await client.change_presence(activity=discord.Game(name=f"Hi, I'm {bot.name}! Try {bot.prefix}help"))

        # Attempt to initialize guild
        success = await bot.initialize_guilds() # has to go here, can't be done in _init_

        # handle success status
        if success:

            # Print bot is now running
            print(f"{bot.name} is now running!")
            passive_update_database.start()

        else:
            print( "Bot is not part of any guilds.")
            print( "Invite with link:")
            print( "\t" + bot.invite_link )
            print(f"Shutting down {bot.name}...")
            await client.close() # this doesn't close all async threads, but it works for now

    # Message Handler
    @client.event
    async def on_message(msg):

        # Don't listen to self
        if msg.author == client.user or msg.attachments:
            return

        '''
        vvvvvvvvvvvvvvvvv

            Five bucks says we can shrink the two chunks down to just one 
        
        vvvvvvvvvvvvvvvvv
        '''

        # Handle commands elsewhere
        if msg.content.startswith( bot.prefix ):
            
            # handle the command, grab the embed
            embed = await bot.handle_command( msg )
            await send_embed( embed, msg.guild, msg.channel )
            return

        # realtime - specifically check for welcome channel
        if msg.channel.name == bot.welcome_channel_str:

            # handle student
            embed = await bot.handle_welcome_channel( msg )
            await send_embed( embed, msg.guild, msg.channel )
            return 

    # Run Bot with Token
        # Should be  the very last command inside of run_discord_bot 
    client.run( bot.token )

async def send_embed( embed, guild, channel ):
    # Send 
    if embed != None:
        await embed.send( guild, channel )