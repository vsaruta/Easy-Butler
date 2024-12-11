import json
import discord
import config as cfg
import datetime

# Overarching handler
class EmbedHandler:

    # Custom embed class
    class CustomEmbed(discord.Embed):
        def __init__(self, *, channel=None, **kwargs):
            super().__init__(**kwargs)
            self.channel = channel

        async def send(self):
            """Sends the embed to the assigned channel."""
            if self.channel is not None:
                # Send the embed
                async with self.channel.typing():
                    await self.channel.send(embed=self)
            else:
                raise ValueError("Channel not set. Use set_channel(channel) to set a channel before sending.")

        def set_channel(self, channel):
            """Sets the destination channel for this embed."""
            self.channel = channel

        def get_channel(self):
            """Returns the destination channel for this embed."""
            return self.channel

    # init
    def __init__(self):

        self._json_file = cfg.json_file

        self._color_map = {
            "DEFAULT":cfg.dft_color,
            "SUCCESS":cfg.success_color,
            "FAILURE":cfg.error_color
        }

        self.guild = None

        with open(self._json_file, 'r') as embed_file:
            self.messages = json.load(embed_file)

    async def get_embed(self, key, channel=None, **kwargs):
        """
        Retrieves an embed by key, resolves the channel by name, and formats with kwargs.

        Args:
            key (str): The key in the JSON configuration.
            kwargs: Additional formatting arguments.

        Returns:
            CustomEmbed: The dynamically created embed with a resolved destination channel.

        Usage:
            embed = await embed_handler.get_embed(key, guild, mention=msg.author)
        """

        if self.guild == None:
            raise ValueError(f"Guild has not been set for embedHandler.")

        # get the embed format
        data = self.messages.get(key)
        if not data:
            raise ValueError(f"Embed key '{key}' not found in configuration.")

        # Resolve the destination channel by name
        channel_name = data.get("channel")

        if channel_name == "ANYWHERE":
            if channel:
                dest = channel  # Use the current message's channel
            else:
                raise ValueError("channel object must be provided when sending 'ANYWHERE'.")
        else: 
            channel = discord.utils.get(self.guild.text_channels, name=channel_name)
            if not channel:
                raise ValueError(f"Channel '{channel_name}' not found in guild '{self.guild.name}'.")

        # Create the embed
        embed = EmbedHandler.CustomEmbed(
            title=data.get("title").format(**kwargs),             # format the title w args
            description=data.get("description").format(**kwargs), # format the body w args
            color=self._color_map[(data.get("color"))],           # Get the hex color
            channel=channel,                                      # set destination channel
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc)             
        )

        return embed

    def set_guild(self, guild):
        self.guild = guild

def _example():

    guild = discord.guild
    embed_handler = EmbedHandler(guild)

    '''
    Assume regular bot stuff here
    '''

    # @bot.event
    async def on_member_join(member):
        """
        Handles the event when a member joins the server.
        Sends a welcome embed message to the configured channel.
        """
        guild = member.guild
        try:
            embed = await embed_handler.get_embed("welcome", mention=member.mention)
            destination_channel = embed.get_channel()
            if destination_channel:
                await destination_channel.send(embed=embed)
        except Exception as e:
            print(f"Error sending welcome message: {e}")

