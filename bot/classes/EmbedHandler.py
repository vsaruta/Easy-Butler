import os
import json
import discord
import config as cfg
import datetime
from classes.GuildHandler import GuildHandler

# Overarching handler
class EmbedHandler ( GuildHandler ):

    # Custom embed class
    class CustomEmbed( discord.Embed ):
        def __init__(self, *, guildHandler, channel_name, **kwargs):
            super().__init__(**kwargs)
            self.guildHandler = guildHandler
            self.channel_name = channel_name
            self.channel_obj = None
            self.guild = None
            self.file_obj = None
            self.reply_to = None

        def set_channel_obj( self, msg_channel:discord.channel ):
        
            # check if embed can be sent anywhere
            if self.channel_name == "" and msg_channel != None:

                # set the channel obj
                self.channel_obj = msg_channel
            
            # A channel has been named
            else:
                self.channel_obj = self.guild.get_channel_obj( self.channel_name )

        def set_file(self, filepath: str):
            """
            Embeds an image into the embed from the given file path.

            Parameters:
            - filepath (str): The path to the image file.

            Returns:
            - discord.File: The file object to be sent with the embed.
            """
            file = discord.File(filepath, filename=filepath.split("/")[-1])
            self.set_image(url=f"attachment://{file.filename}")
            
            self.file_obj = file


        def set_guild(self, guild):
            self.guild = self.guildHandler.create_guild( guild )

        async def send(self, guild, msg_channel:discord.channel=None):
            """Sends the embed to the assigned channel."""

            # Set embed parameters
            self.set_guild( guild )
            self.set_channel_obj( msg_channel )

            # send the embed
            if self.channel_obj is not None:

                # Send the embed
                async with self.channel_obj.typing():
                    
                    # See if we need to reply to someone
                    if self.reply_to != None:

                        # reply to the message with file
                        if self.file_obj != None:
                            await self.reply_to.reply(embed=self, file=self.file_obj)
                        
                        # reply to the message WITHOUT file
                        else:
                            await self.reply_to.reply(embed=self)
                    
                    #else, simply send the message
                    else:                        
                        # send embed with file
                        if self.file_obj != None:
                            await self.channel_obj.send(embed=self, file=self.file_obj)
                        
                        # send embed WITHOUT file
                        else:
                            await self.channel_obj.send(embed=self)

            else:
                raise ValueError(f"Embed '{self.title}' needs a channel in order to be sent!.")

    # init
    def __init__(self):

        self.guildHandler = GuildHandler()

        self._json_file = cfg.json_file

        self._color_map = {
            "DEFAULT":cfg.dft_color,
            "SUCCESS":cfg.success_color,
            "FAILURE":cfg.error_color
        }

        self.guild = None

        with open(self._json_file, 'r') as embed_file:
            self.messages = json.load(embed_file)

    def get_embed(self, key, reply_to:discord.Message=None, **kwargs):

        # get embed format
        data = self._get_embed_format( key )

        # retrieve channel name 
        channel_name = data.get("channel")

        # create embed with channel obj
        embed = EmbedHandler.CustomEmbed(
            title=data.get("title").format(**kwargs),             # format the title w args
            description=data.get("description").format(**kwargs), # format the body w args
            color=self._color_map[(data.get("color"))],           # Get the hex color
            channel_name = channel_name,                          # set destination channel
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),    # set timestamp         
            guildHandler=self.guildHandler                                # set guild handler
        )

        if reply_to != None:
            embed.reply_to = reply_to

        # set the footer
        embed.set_footer(text=data.get("footer").format(**kwargs))

        # return the embed
        return embed
    
    def _get_embed_format( self, key ):

        data = self.messages.get(key)

        if not data:
            raise ValueError(f"Embed key '{key}' not found in configuration.")
        
        return data
    
    def set_guild(self, guild):
        self.guild = guild

