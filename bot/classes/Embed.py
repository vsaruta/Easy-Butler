import discord
from datetime import datetime

class Embed:

    def __init__(self, dft, success, error) -> None:
        self.dft_color = dft
        self.success_color = success
        self.error_color = error
    
    def clear_embed(self, embed):

        embed.title = ""
        embed.desc  = ""
        embed.color = self.dft_color

    def initialize_embed(self, title="", desc="", color=0xffffff):
        embed = discord.Embed(title=title, description=desc, color=color)
        embed.timestamp = datetime.now()
        return embed
    
    def added_member( self, embed, author, name, integration_id, lab_section ):

        desc = f'''
        **Name**: {name}
        **School ID**: {integration_id}
        **Lab Section:** {lab_section}
        **Discord User:**: {author.mention}
        '''
        embed.set_thumbnail(url=author.avatar_url)
        embed.title = "New Student Added"
        embed.description = desc
        embed.color = self.success_color


    def member_not_found(self, embed, author, integration_id):

        desc = f'''
        Sorry, we could not find **{integration_id}** in our system.

        Double check your school email for your ID - it should be listed as <school-id>@nau.edu
        '''

        embed.title = "School ID Not Found"
        embed.description = desc
        embed.color = self.error_color