import discord
import secret as sc
import config as cfg
from datetime import datetime
from classes.Embed import Embed 
from classes.Canvas import Canvas
from classes.Semester import Semester

class Bot( Canvas, Embed ):

    '''
    PUBLIC FUNCTIONS
    '''
    
    def get_channel_obj(self, channel_name):
        guild = self.current_semester.guild
        return discord.utils.get(guild.channels, name=channel_name)

    def get_role_obj(self, role_name):
        guild = self.current_semester.guild
        return discord.utils.get(guild.roles, name=role_name)

    async def handle_command( self, msg ):

        # Embeds
        embed_list = []

        # initialize variables
        author_id = msg.author.id

        # Get command - axe.lookup
        argv = msg.content.split()
        command = argv[0].lower()

        # initialize embed
        embed = self.initialize_embed( embed_list )

        # check if command is valid
        if command in self.commands.keys():

            # Grab the command tuple
            selected_option = self.commands.get( command ) 

            # Ensure permissions, currently owner-only
            if author_id != self.owner and selected_option[2] == True:

                # set stuff
                embed.title = "Unauthorized Command"
                embed.description = "Sorry, only authorized users can use this command."

                return embed_list # return early

            # run the selected option
            await selected_option[0]( msg, embed )

            
        # Command not in the command dictionary
        else:  
            embed.title = "Invalid Command"
            embed.description = "Command not recognized."
            embed.set_footer( text=f"(!) Commands can be found with {self.prefix}help")

        return embed_list

    async def help(self, msg, embed):

        # help command
        embed.title = f"{self.name} help!"
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
        my_courses = self.get_my_courses()

        # loop through guilds
        for guild in guilds:

            # create new object
            semester = Semester(guild)

            # leave any inactive guilds
            if not semester.is_current_semester():
                await guild.leave()

            # Reset current_semester variable if we are in no more guilds
            elif len(guilds) == 0:
                print("Left all guilds.")
                print("Invite the bot again with this link:")
                print( self.invite_link )
                self.current_semester = None

            # else we have found the active guild
            else:

                # assign to bot
                self.current_semester = semester    
                
                # set up the current semester's courses
                self.current_semester.set_courses( my_courses )

                # set up the current semester's channels
                self.current_semester.set_channels( 
                    self.get_channel_obj( self.welcome_channel_str ), 
                    self.get_channel_obj( self.added_students_channel_str ), 
                    self.get_channel_obj( self.admin_channel_str ), 
                    self.get_channel_obj( self.admin_log_channel_str ),
                    self.get_channel_obj( self.student_cmds_channel_str ), 
                    self.get_channel_obj( self.student_cmds_log_channel_str ) 
                    )

                # add the lab roles to the required roles
                self.required_roles += self.current_semester.lab_sections

                # validate everything in the server
                if not self.validate_setup():
                    return False

        return True

    async def invite(self, msg, embed):
        pass

    async def set_api_key( self, msg, embed):

        # grab key
        key = msg.content.split(" ")[1]

        # validate key, set if its good
        if self.set_api_key(key, verbose=False):
            
            embed.title = "Key Success!"
            embed.description = f"New API key set by {msg.author.mention}."
            embed.color = self.success_color


        else:
            embed.title = "Key Failure."
            embed.description = "Failed to set API key. Key has not been changed."
            embed.color = self.error_color
        
        await self.current_semester.admin_log_channel_obj.send(embed=embed)
        #await msg.delete()


    async def process_student(self, msg, member, student_dict, student_role_obj, embed):

        # grab the student's data from our custom dictionary
        integration_id = msg.content.lower()
        student_data = student_dict.get(integration_id)
        
        # We have found student
        if student_data != None:

            # grab details
            name = student_data['name']
            lab_section = student_data['lab_section']
            lab_role = student_data['lab_role']


            print(student_data)
            # rename to canvas name
            await member.edit(nick=name)

            # add student role
            await member.add_roles(student_role_obj)
            
            # give lab role, some students actually might not be enrolled
            if lab_role != None:
                await member.add_roles(self.get_role_obj(lab_role))

            self.added_member(embed, msg.author, name, integration_id, lab_section)
            
            # Don't know where this will go yet
            await self.current_semester.added_student_channel_obj.send(embed=embed)

            # delete message?
            # await msg.delete()

            # success!
            return True
        
        # student not in class
        else:
            self.member_not_found(embed, msg.author, integration_id)
            await self.current_semester.welcome_channel_obj.send(content=f"{msg.author.mention}", embed=embed)

        return False
    
    async def process_students(self, command, embed):

        # initialize variables 
        student_role_obj = None
        student_dict = {}
        student_key = 'integration_id'
        student_name = 'name'
        index = 0
        processed = 0
        
        # grab student lists for main class, really it might be more than 1 class
        for course_id in self.current_semester.combo_ids:

            # get students in combo class
            students = self.retrieve_students( course_id )[0]

            # loop thru each student
            for student in students:

                # grab their integration ID
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
            students = self.retrieve_students( course_id )[0]

            # grab lab name
            lab_section = self.current_semester.lab_sections[index]

            # increment index
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
                student_dict[ integration_id ]["lab_id"] = course_id
                student_dict[ integration_id ]["lab_section"] = lab_section
                student_dict[ integration_id ]["lab_role"] = self.get_role_obj( f"Lab {lab_section}")

        # loop through message history
        async for msg in self.current_semester.welcome_channel_obj.history():
            
            # ignore self
            if msg.author.id == self.client.user.id:
                continue

            # grab member : discord's method of adding roles/nicknames
            member = await msg.guild.fetch_member(msg.author.id)

            # student hasnt been processed yet
            if student_role_obj not in member.roles:

                success = await self.process_student(msg, member, student_dict, student_role_obj, embed)


        embed.title = "Finished Processing Students"
        embed.description = f"Processed {processed} students."
    
        return True

    
    async def process_welcome_msg(self, msg):

        # initialize variables 
        student_role_obj = self.current_semester.student_role_obj
        student_dict = {}
        student_key = 'integration_id'
        student_name = 'name'
        index = 0
        desc = ""
        title = "Error in processing students"
        embed_list = []

        # ignore owners
        if msg.author.id in self.staff_list:
            return embed_list

        # grab member : discord's method of adding roles/nicknames
        member = await msg.guild.fetch_member(msg.author.id)

        # initialize embed
        embed = self.initialize_embed(embed_list, desc, title)
        
        # TODO: 
        # grab student lists for main class, really it might be more than 1 class
        for course_id in self.current_semester.combo_ids:

            # get students in combo class
            students = self.retrieve_students( course_id )[0]

            # loop thru each student
            for student in students:

                # grab their integration ID
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
            students = self.retrieve_students( course_id )[0]

            # grab lab name
            lab_section = self.current_semester.lab_sections[index]

            # increment index
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
                student_dict[ integration_id ]["lab_id"] = course_id
                student_dict[ integration_id ]["lab_section"] = lab_section
                student_dict[ integration_id ]["lab_role"] = self.get_role_obj( f"Lab {lab_section}")
            

        # student hasnt been processed yet
        if self.current_semester.student_role_obj not in member.roles:

            success = await self.process_student(msg, member, student_dict, student_role_obj, embed)

        return embed_list
    
    def validate_channel(self, channel_name):

        channel_obj = self.get_channel_obj(channel_name)

        return channel_obj != None
    
    def validate_channels(self, channel_names=None, embed=None, verbose=False):

        # initialize variables
        all_valid = True
        desc = ""

        # set channel names if not given
        if channel_names == None:
            channel_names = self.required_channels

        # loop through channel names
        for channel_name in channel_names:

            # validate channel
            if not self.validate_channel( channel_name ):
                
                # channel not valid, add information
                all_valid = False
                desc += f"- Channel Error: `#{channel_name}` not found.\n"
            
        # set embed desc if applicable
        if embed != None and not all_valid:
            embed.description = desc

        # print to terminal if applicable
        if verbose and desc != "":
            print(desc)

        # return valid status
        return all_valid
    
    # Validates that a role is present in server by its name
    def validate_role(self, role_name):
        role_obj = self.get_role_obj(role_name)
        return role_obj != None
    
    # Validates either all required roles or a passed set of roles
    def validate_roles(self, role_names=None, embed=None, verbose=False):

        # initialize variables
        all_valid = True
        desc = ""

        # set role names if not provided
        if role_names == None:
            role_names = self.required_roles

        # check every role
        for role_name in role_names:

            # validate the role
            if not self.validate_role( role_name ):
                
                # role not valid, add information
                all_valid = False
                desc += f"- Role Error: '{role_name}' does not exist.\n"

        # set embed desc if applicable
        if embed != None and not all_valid:
            embed.description = desc

        # print to terminal if applicable
        if verbose and desc != "":
            print(desc)

        # return valid status
        return all_valid
    
    # validates server is properly setup
    def validate_setup(self):
        
        # validate API key
        print("Validating Canvas API key...")
        canvas = self.validate_api_key( verbose=True )

        # validate channels
        print("Validating all channels...")
        channels = self.validate_channels( verbose=True )

        # validate roles
        print("Validating all roles...")
        roles    = self.validate_roles( verbose=True )

        # return true/false
        return canvas and channels and roles

    '''
    PRIVATE FUNCTIONS
    '''
    def __init__(self, name, client, prefix, dft_color, TOKEN):

        # initialize important stuff
        self.client     = client    # discord client o bject
        self.name       = name      # str
        self.dft_color  = dft_color # hex
        self.prefix     = prefix    # str
        self.token      = TOKEN     # str | TODO: make this environmental variable

        # initialize additional file variables
        self.invite_link = sc.invite_link # str
        self.admin_list = cfg.admin_list  # list of ints (discord IDs)
        self.staff_list = cfg.staff_list  # list of ints (discord IDs)
        self.owner      = cfg.owner       # int (discord ID)
        self.student_role_str    = cfg.student_role # str

        # all channel strings
        self.welcome_channel_str          = cfg.welcome_channel_str          # str
        self.added_students_channel_str   = cfg.added_students_channel_str   # str
        self.admin_channel_str            = cfg.admin_channel_str            # str
        self.admin_log_channel_str        = cfg.admin_log_channel_str        # str
        self.student_cmds_channel_str     = cfg.student_cmds_channel_str      # str
        self.student_cmds_log_channel_str = cfg.student_cmds_log_channel_str # str

        # validation stuff
        self.required_roles    = [
            self.student_role_str
        ]

        self.required_channels = [
            self.welcome_channel_str,           # channel to welcome new students
            self.added_students_channel_str,     # channel to log any added students
            self.admin_channel_str,             # channel for admin commands
            self.admin_log_channel_str,          # log for admin commands
            self.student_cmds_channel_str,      # channel for student commands
            self.student_cmds_log_channel_str   # log for student commands
        ]

        # initialize general variables
        self.current_semester = None

        # establish other classes
        Embed.__init__(self, dft_color, cfg.success_color, cfg.error_color)
        Canvas.__init__(self)

        # initialize all available commands for users to call
        self.commands = {   self.prefix + "help": ( self.help, # command to run
                                                    "List of commands", # help desc
                                                    False, # is admin-only command
                            ),
                            self.prefix + "process_students": (
                                                self.process_students,
                                                "Process students - Kind of implemented",
                                                True, # is admin-only command
                            ),
                            self.prefix + "invite" : (
                                                self.invite,
                                                "Invite the bot to another server",
                                                True # is admin-only command
                            ),
                            # self.prefix + "restart":(
                            #                     self.restart,
                            #                     "Restart Bot",
                            #                     True

                            # ),
                            self.prefix + "set_api_key":(
                                                self.set_api_key,
                                                "Reset the Canvas API key",
                                                True
                            ),
                            # self.prefix + "update_lab":(
                            #                     self.update_lab,
                            #                     "Update a student's lab section",
                            #                     True
                            #),
                            # self.prefix + "view_student":(
                            #                     self.view_student,
                            #                     "View a student's current profile",
                            #                     True
                            # )


                        }

    def _is_staff(self, author):
        return author.id in self.staff_list
    
    def _is_admin(self, author):
        return author.id in self.admin_list