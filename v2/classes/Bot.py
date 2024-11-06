import discord
import secret as sc
import config as cfg
from datetime import datetime
from classes.Embed import Embed 
from classes.Canvas import Canvas
from classes.Semester import Semester


class Bot:

    '''
    PUBLIC FUNCTIONS
    '''

    def get_channel_obj(self, guild, channel_name):
        return discord.utils.get(guild.channels, name=channel_name)

    def get_role_obj(self, guild, role_name):
        return discord.utils.get(guild.roles, name=role_name)

    async def handle_msg( self, msg ):

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
            await selected_option[0]( msg, embed )

            
        # Command not in the command dictionary
        else:  
            embed.title = "Invalid Command"
            embed.description = "Command not recognized."
            embed.set_footer( text=f"(!) Commands can be found with {self.prefix}help")

        return embed

    async def help(self, msg, embed):

        # help command
        embed.title = f"{self.name} help!"
        desc = ""
        is_admin = self._is_admin( msg.author )

        # add in all items
        for key, val in self.commands.items():

            # admins see all commands, but if not admin, then just non-admin commands
            if is_admin or not val[2]:

                # add a field
                embed.add_field(name=f"{key} - {val[1]}", value="", inline=False)
            

    async def initialize_guilds(self):

        # initialize variables
        guilds = self.client.guilds
        my_courses = self.canvas.get_my_courses()

        # loop through guilds
        for guild in guilds:

            # create new object
            semester = Semester(guild)

            # leave any inactive guilds
            if not semester.is_current_semester():
                await guild.leave()

            # Reset current_semester variable if we are in no more guilds
            elif len(guilds) == 0:
                self.current_semester = None

            # else we have found the active guild
            else:
                # grab welcome channel
                welcome_channel_obj = self.get_channel_obj( guild, self.welcome_channel_str )

                # grab bot log channel
                log_channel_obj = self.get_channel_obj( guild, self.log_channel_str )

                # set up the current semester
                semester.set_courses( my_courses )
                semester.set_channels( welcome_channel_obj, log_channel_obj )

                # assign to bot
                self.current_semester = semester    

    async def invite(self, msg, embed):
        pass

            
    async def process_students(self, command, embed):

        # initialize variables 
        student_role_obj = self.get_role_obj( command.guild, self.student_role_str )
        student_dict = {}
        student_key = 'integration_id'
        student_name = 'name'
        index = 0
        processed = 0

        title = "Error"
        desc = ""
        
        # ensure welcome channel and bot channel are not null
        if self.current_semester.welcome_channel_obj == None or \
           self.current_semester.log_channel_obj     == None or \
           student_role_obj == None:

            if self.current_semester.welcome_channel_obj == None:

                desc += f"(!) Welcome channel not set. Please create a channel named #{self.welcome_channel_str}\n"

            if self.current_semester.log_channel_obj     == None:
                desc += f"(!) Log channel not set. Please create a channel named #{self.log_channel_str}\n"

            if student_role_obj == None:
                desc += f"(!) Role '{self.student_role_str}' not found. Please create this role. \n"

            embed.description = desc + "\n** RESTART BOT **"
            embed.title = title
            return False
        
        # grab student lists for main class
        for course_id in self.current_semester.combo_ids:

            # get students in combo class
            students = self.canvas.retrieve_students( course_id )[0]

            # loop thru each student
            for student in students:

                # grab their integration iD
                integration_id = student[student_key]

                # add them to the dict
                student_dict[ integration_id ] = {
                                                    "name": student[student_name],
                                                    "combo_id": course_id,
                                                    "lab_id": None,
                                                    "lab_section":None,
                                                    "lab_role":None
                                                }
            

        # grab student list for labs
        for course_id in self.current_semester.lab_ids:
            
            # get students in lab
            students = self.canvas.retrieve_students( course_id )[0]

            # grab lab name
            lab_section = self.current_semester.lab_sections[index]
            index += 1

            # loop thru each student
            for student in students:

                # grab their integration iD
                integration_id = student[student_key]

                # if student is not in the main class, add them but main class is NONE
                if integration_id not in student_dict.keys():
        
                    student_dict[ integration_id] = {
                                                    "name": student[student_name],
                                                    "combo_id": None
                                                    }
                # update their lab
                student_dict[ student[student_key] ]["lab_id"] = course_id
                student_dict[ student[student_key] ]["lab_section"] = lab_section
                student_dict[ student[student_key] ]["lab_role"] = self.get_role_obj( command.guild, 
                                                                                     f"Lab {lab_section}")

        # loop through message history
        async for msg in self.current_semester.welcome_channel_obj.history():
            
            # ignore self
            if msg.author.id == self.client.user.id:
                continue

            # grab member
            member = await msg.guild.fetch_member(msg.author.id)

            if student_role_obj not in member.roles:

                # grab the message 
                content = msg.content.lower()

                # grab the student's data from our custom dictionary
                student_data = student_dict.get(content)
                
                # We have found student
                if student_data != None:

                    # grab details
                    integration_id = content
                    name = student_data['name']
                    lab_section = student_data['lab_section']
                    lab_role = student_data['lab_role']


                    # rename to canvas name
                    await member.edit(nick=name)

                    # add student role
                    await member.add_roles(student_role_obj)

                    # error if lab sections dont exist
                    if lab_section != None and lab_role == None:
                        desc  = f"Processed {processed} students.\n"
                        desc += f"Role 'Lab {lab_section}' does not exist. Please add and restart bot."
                        embed.description = desc
                        embed.title = title
                        return False
                    
                    # give lab role, some students actually might not be enrolled
                    elif lab_role != None:
                        await member.add_roles(lab_role)

                    self.embed.added_member(embed, msg.author, name, content, lab_section)
                    await self.current_semester.log_channel_obj.send(embed=embed)

                    # increase processed
                    processed += 1

                    # delete message?
                    # await msg.delete()
                else:
                    self.embed.member_not_found(embed, msg.author, content)
                    await self.current_semester.welcome_channel_obj.send(content=f"{msg.author.mention}", embed=embed)


        embed.title = "Finished Processing Students"
        embed.description = f"Processed {processed} students."
    
        return True

    async def prune(self, msg, embed):

        # leave inactive serveres
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

        # initialize additional file variables
        self.admin_list = cfg.admin_list
        self.owner      = cfg.owner
        self.student_role_str    = cfg.student_role
        self.welcome_channel_str = cfg.welcome_channel
        self.log_channel_str     = cfg.log_channel

        # initialize empty lists

        # initialize general variables
        self.current_semester = None

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
                            ),
                            self.prefix + "invite" : (
                                                self.invite,
                                                "Invite the bot to another server",
                                                True # is admin-only command
                            )
                        }

    def _is_ta(self, author):
        return author.id in self.ta_list
    
    def _is_admin(self, author):
        return author.id in self.admin_list