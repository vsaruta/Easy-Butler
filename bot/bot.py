import discord
import secret as sc
import config as cfg
from classes.Bot import Bot

def run_discord_bot():

    # Set up bot
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client( intents=intents )

    # initialize variables
    name      = cfg.name
    prefix    = cfg.prefix
    dft_color = cfg.dft_color
    token     = sc.TOKEN

    # initialize bot
    bot = Bot(name, client, prefix, dft_color, token)

    @client.event
    async def on_guild_join(guild): # check if we need to update bot on a new join
        await bot.initialize_guilds()

    # Show bot logged on successfully
    @client.event
    async def on_ready():
        await bot.initialize_guilds()
        #await client.change_presence(activity=discord.Game(name="New Bot!"))
        print(f"{bot.name} is now running!")

    # Message Handler
    @client.event
    async def on_message(msg):

        # Don't listen to self
        if msg.author == client.user or msg.attachments:
            return 0 # skip
        
        # realtime - specifically check for welcome channel

        # if in admin command channel 
        # handle any commands
        if msg.content.startswith( bot.prefix ):
            
            # handle the message, grab the embed
            embed = await bot.handle_msg( msg )

            # send the embed
            async with msg.channel.typing(): 
                
                # send with reply
                await msg.reply( embed=embed )

    # Run Bot with Token
        # Should be  the very last command inside of run_discord_bot 
    client.run( bot.token )
