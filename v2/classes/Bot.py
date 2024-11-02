import discord
import secret as sc
import config as cfg
from datetime import datetime
from classes.Embed import Embed 
from classes.Canvas import Canvas

class Bot:

    '''
    PUBLIC FUNCTIONS
    '''

    def handle_msg( self, msg ):

        # initialize variables
        author_id = msg.author.id

        # Get command - axe.lookup
        argv = msg.content.split()
        command = argv[0].lower()

        # initialize embed
        embed = self.embed.initialize_embed( "Title", "Desc", self.dft_color )
        embed.timestamp = datetime.now()

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
        is_admin = self._is_admin( msg.author )

        # add in all items
        for key, val in self.commands.items():

            # admins see all commands, but if not admin, then just non-admin commands
            if val[2] or is_admin:

                # add a field
                embed.add_field(name=f"{key} - {val[1]}", value="", inline=False)
                

    def process_students(self, msg, embed):
        pass

    def prune(self, msg, embed):
        pass

    '''
    PRIVATE FUNCTIONS
    '''
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

        # establish other classes
        self.embed      = Embed()
        self.canvas     = Canvas()

        # initialize all available commands for users to call
        self.commands = {   self.prefix + "help": ( self.help, # command to run
                                                    "List of commands", # help desc
                                                    False, # is admin-only command
                                                ),
                            self.prefix + "process_students": (
                                                self.process_students,
                                                "Process students - NOT IMPLEMENTED",
                                                True, # is admin-only command
                                                ),
                            self.prefix + "prune": (
                                                self.prune,
                                                "Leave servers without [SEASON] [YEAR] - NOT IMPLEMENTED",
                                                True # is admin-only command
                            )
                        }

    def _is_ta(self, author):
        return author.id in self.ta_list
    
    def _is_admin(self, author):
        return author.id in self.admin_list