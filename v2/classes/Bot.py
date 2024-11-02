import discord
from datetime import datetime
import secret as sc
import config as cfg

class Bot:

    def handle_msg( self, msg ):

        # initialize variables
        author_id = msg.author.id

        # Get command - axe.lookup
        argv = msg.content.split()
        command = argv[0].lower()

        # initialize embed
        #embed = self.embed_handler.initialize_embed( "Title", "Desc", self.dft_color )
        embed = discord.Embed(title="Tile", description="Desc", color=self.dft_color)
        embed.timestamp = datetime.now()
        #embed.set_footer( text='\u200b',icon_url=self.client.user.avatar.url )

        # check if command is valid
        if command in self.commands.keys():

            # Grab the command tuple
            selected_option = self.commands.get( command ) 

            # Ensure permissions, currently owner-only
            if author_id != self.owner and selected_option[2] == True:

                # set stuff
                embed.title = "Unauthorized Command"
                embed.description = "Sorry, only authorized users can use this command."

                return embed # return early

            # run the selected option
            selected_option[0]( msg, embed )

            
        # Command not in the command dictionary
        else:  
            embed.title = "Invalid Command"
            embed.description = "Command not recognized."
            embed.set_footer( text=f"(!) Commands can be found with {self.prefix}help")
        

        return embed

    def help(self, msg, embed):

        # help command
        embed.title = f"{self.name} help!"
        desc = ""

        for key, val in self.commands.items():

            embed.add_field(name=f"{key} - {val[1]}", value="", inline=False)

    def process_students(self, msg, embed):

        pass

    def __init__(self, name, client, prefix, dft_color, TOKEN):

        # initialize important stuff
        self.client    = client
        self.name      = name
        self.dft_color = dft_color
        self.prefix    = prefix
        self.token     = TOKEN

        # initialize additional variables
        self.admin_list = cfg.admin_list
        self.ta_list    = cfg.ta_list
        self.owner      = cfg.owner

        self.commands = {   self.prefix + "help": ( self.help, # command to run
                                                    "List of commands", # help desc
                                                    False, # is admin-only command
                                                ),
                            self.prefix + "process_students": (
                                                self.process_students,
                                                "Process students",
                                                True, # is admin-only command
                            )
                        }

    def _is_ta(self, author):
        return author.id in self.ta_list
    
    def _is_admin(self, author):
        return author.id in self.admin_list