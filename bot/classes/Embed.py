import discord

class Embed:

    def __init__(self) -> None:
        pass
    
    def initialize_embed(self, title, desc, color):
        
        return discord.Embed(title=title, description=desc, color=color)
    
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


    def member_not_found(self, embed, author, integration_id):

        desc = f'''
        Sorry, we could not find **{integration_id}** in our system.

        Double check your school email for your ID - it should be listed as <school-id>@nau.edu
        '''

        embed.title = "School ID Not Found"
        embed.description = desc