import discord
import secret as sc
import config as cfg
from datetime import datetime
from classes.Canvas import Canvas
from classes.Semester import Semester
from classes.EmbedHandler import EmbedHandler 
from classes.SQLHandler import SQLHandler, Course, Student

class Bot( EmbedHandler, Canvas, SQLHandler ):

    '''
    PUBLIC FUNCTIONS
    '''

    def find_course_name_by_id(self, course_list, course_id):
        for course in course_list:
            if course['id'] == course_id:
                return course['name']
        return None

    def get_channel_obj(self, channel_name):
        guild = self.current_semester.guild
        return discord.utils.get(guild.channels, name=channel_name)

    def get_role_obj(self, role_name):
        guild = self.current_semester.guild
        return discord.utils.get(guild.roles, name=role_name)

    async def handle_command( self, msg ):

        # initialize variables
        author_id = msg.author.id

        # Get command 
        argv = msg.content.split()
        command = argv[0].lower()

        # check if command is valid
        if command in self.commands.keys():

            # Grab the command tuple
            selected_option = self.commands.get( command ) 

            # Ensure permissions, currently owner-only
            if author_id != self.owner and selected_option[2] == True:

                embed = await self.get_embed("unauthorized-user", 
                                       channel = msg.channel,
                                       mention=msg.author.mention)

                # set stuff
                # embed.title = "Unauthorized Command"
                # embed.description = "Sorry, only authorized users can use this command."
                # embed_list.append(embed)
                return embed # return early

            # run the selected option
            embed = await selected_option[0]( msg )

            
        # Command not in the command dictionary
        else:  
            embed = await self.get_embed("invalid-command", 
                                            prefix = self.prefix)
            # embed.title = "Invalid Command"
            # embed.description = "Command not recognized."
            # embed.set_footer( text=f"(!) Commands can be found with {self.prefix}help")

        return embed

    async def handle_welcome_channel(self, msg):

        # initialize variables
        student_role_obj = self.get_role_obj(self.student_role_str)
        member = await msg.guild.fetch_member(msg.author.id)
        integration_id = msg.content
        lab = None
        lab_section = None

        # skip staff members
        if msg.author.id in self.staff_list:
            return None
        
        # Okay, then delete the messages so other student's can't snipe it.
        await msg.delete()
        
        # Skip students that have already been processed
        if student_role_obj in member.roles:
            return None
    
        # fail if id is invalid
        if not self.validate_student( integration_id ):
            return await self.get_embed("invalid-integration-id", 
                                        channel = msg.channel,
                                        mention = msg.author.mention,
                                        integration_id=integration_id)

        # get member
        student = self.retrieve(Student, {"id":integration_id})[0]

        print(student)

        if student.lab_class != None:
            lab = self.retrieve(Course, {"id":student.lab_class})[0]
            lab_section = lab.section

        result = await self.process_student( member, student, lab )

        # student was processed
        if result:
            # self.added_member(embed, msg.author, student.name, student.id, student.section)
            return await self.get_embed( "added-student-success",
                                        name = student.name,
                                        integration_id = integration_id,
                                        lab_section = lab_section,
                                        mention = msg.author.mention
                                        )
       
       # student was not processed
        else:
            return await self.get_embed( "added-student-failure",
                                   author = msg.author,
                                   id = student.id,)
        
    
    async def process_student( self, member, student, lab ):

        try:
            # initialize variables
            student_role_obj = self.get_role_obj(self.student_role_str)
            lab_role_str = None
            
            # grab name and labID
            name = student.name

            if lab != None:
                lab_role_str = "Lab " + lab.section

            # Edit their nickname
            await member.edit(nick=name)

            # Edit their main class role
            await member.add_roles(student_role_obj)

            # Edit their lab role, if applicable
            if lab_role_str != None:
                lab_role_obj = self.get_role_obj(lab_role_str)
                await member.add_roles(lab_role_obj)

            return True
        
        except Exception as e:

            print(e)
        
            return False
        

    async def help(self, msg):

        # Help command, sorry this isnt more automatic. 
        # You'll have to write it out for now
        desc=f'''Hi, thanks for using {self.name}! 
        
        This bot was created by Claire Whittington. Try out the list of commands below:
        
        🤖💬
        
        '''

        # iterate through the commands
        for trigger, tuple in self.commands.items():
            
            # get desc
            text = tuple[1]
            admin_only = tuple[2]

            if self._is_admin( msg.author ) or not admin_only:

                desc += f"**{trigger}**: {text}\n"

        return await self.get_embed("help", channel=msg.channel, desc=desc)

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
                
                # set the guild objct for embeds
                self.set_guild(guild)

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

    async def invite(self, msg):
        pass

    async def handle_api_set( self, msg ):

        # grab key
        key = msg.content.split(" ")[1]

        # validate key, set if its good
        if self.set_api_key(key, verbose=True):

            return await self.get_embed("key-sucess",
                                  mention=msg.author.mention)
            
            # embed.title = "Key Success!"
            # embed.description = f"New API key set by {msg.author.mention}."
            # embed.color = self.success_color


        else:
            return await self.get_embed("key-failure",
                                  mention=msg.author.mention)
            # embed.title = "Key Failure."
            # embed.description = f'''
            #                     Failed to set API key.
                                
            #                     **Attempt by**: {msg.author.mention}
            #                     '''
            # embed.color = self.error_color
        
        #await self.current_semester.admin_log_channel_obj.send(embed=embed)
        await msg.delete()
    
    def initialize_students(self):

        student_dict = {}
        student_key = "integration_id"
        student_name = 'name'
        index = 0

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
                                                }
            

        # grab student list for labs
        for course_id in self.current_semester.lab_ids:
            
            # get students in lab
            students = self.retrieve_students( course_id )[0]

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
    
        return student_dict
    
    async def update_database(self, msg=None):

        # initialize variables
        student_dict = self.initialize_students()
        insertions = 0
        num_updates = 0

        # try to update the db
        try: 

             # Loop through courses
            for integration_id, values in student_dict.items():

                # get course ID (int)
                name = values["name"]
                courseID = values["combo_id"]
                labID    = values["lab_id"]
                lab_section = None
                
                # Skip test student
                if name == "Test Student":
                    continue
                
                '''
                STUDENT HANDLING
                '''

                # updates for student
                updates={
                            "name":name, 
                            "main_class":courseID, 
                            "lab_class":labID
                            } 
                
                # insert student if not in db
                if not self.check_exists( Student, {"id":integration_id} ):

                    self.insert(Student(
                                        id=integration_id, 
                                        name=name, 
                                        main_class=courseID, 
                                        lab_class=labID
                                        )
                                )
                    
                    insertions += 1
                    
                # Student is in db, update their info
                elif self.needs_update(Student, record_id=integration_id, updates=updates):
                                        # Define updates
                    
                    self.update(Student, record_id=integration_id, updates=updates)

                    num_updates += 1

                '''
                MAIN COURSE HANDLING
                '''

                # Handle main course
                if courseID != None:

                    # Get the course name
                    full_course_name = self.find_course_name_by_id(self.current_semester.my_courses, courseID)

                    # Define updates
                    updates = {
                            "name":full_course_name,
                            }
                    
                    # Main course is not in the database yet
                    if not self.check_exists( Course, {"id": courseID} ):
                        
                        # Insert it, where section = None
                        self.insert(Course(id=courseID, name=full_course_name, section=None))
                        insertions += 1

                    elif self.needs_update(Course, record_id=courseID, updates=updates):
                        self.update(Course, record_id=courseID, updates=updates)
                        num_updates += 1

                '''
                LAB DATA HANDLING
                '''

                # Handle lab if exists
                if labID != None:

                    # Get the course info
                    full_course_name = self.find_course_name_by_id(self.current_semester.my_courses, labID)
                    lab_section = self.current_semester.get_lab_section(full_course_name)

                    # Define updates
                    updates = {
                            "name":full_course_name,
                            "section":lab_section
                            }
                    
                    # Main course is not in the database yet
                    if not self.check_exists( Course, {"id": labID} ):
                        
                        # Insert it, where section = None
                        self.insert(Course(id=labID, name=full_course_name, section=lab_section))
                        insertions += 1

                    elif self.needs_update(Course, record_id=labID, updates=updates):
                        self.update(Course, record_id=labID, updates=updates)
                        num_updates += 1
            
        
        # Error in updating database
        except Exception as e:
            
            # Bot is not ready :(
            self.ready = False

            # Send failure embed
            return await self.get_embed("update-database-failure", 
                                            e=e)
        
        # Bot is now ready
        self.ready = True

        # get the summary
        summary = self.summary()

        # send the embed
        return await self.get_embed("update-database-success",
                                    course_count=summary["course_count"],
                                    student_count=summary["student_count"],
                                    insertions = insertions,
                                    updates = num_updates
                                    )
    
    def validate_channel(self, channel_name):

        channel_obj = self.get_channel_obj(channel_name)

        return channel_obj != None
    
    def validate_channels(self, channel_names=None, verbose=False):

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
    def validate_roles(self, role_names=None, verbose=False):

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

    def validate_student(self, integration_id):

        results = self.retrieve(Student, {"id":integration_id})

        return len(results) != 0

    '''
    PRIVATE FUNCTIONS
    '''
    def __init__(self, name, client, prefix, dft_color, TOKEN):

        # Define ready flag
        self.ready = False

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
            self.welcome_channel_str,            # channel to welcome new students
            self.added_students_channel_str,     # channel to log any added students
            self.admin_channel_str,              # channel for admin commands
            self.admin_log_channel_str,          # log for admin commands
            self.student_cmds_channel_str,       # channel for student commands
            self.student_cmds_log_channel_str    # log for student commands
        ]

        # initialize general variables
        self.current_semester = None

        # establish other classes
        Canvas.__init__(self)
        SQLHandler.__init__(self)
        EmbedHandler.__init__(self)
        

        # initialize all available commands for users to call
        self.commands = {   self.prefix + "help": ( self.help, # command to run
                                                    "List of commands", # help desc
                                                    False, # is admin-only command
                            ),
                            # self.prefix + "process_students": (
                            #                     self.process_students,
                            #                     "Process students",
                            #                     True, # is admin-only command
                            # ),
                            # self.prefix + "invite" : (
                            #                     self.invite,
                            #                     "Invite the bot to another server",
                            #                     True # is admin-only command
                            # ),
                            # self.prefix + "restart":(
                            #                     self.restart,
                            #                     "Restart Bot",
                            #                     True

                            # ),
                            self.prefix + "update":(
                                                self.update_database,
                                                "Force-updates the database.",
                                                True
                            ),
                            self.prefix + "set_api_key":(
                                                self.handle_api_set,
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