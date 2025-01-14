import discord
import secret as sc
import config as cfg
from classes.GuildHandler import GuildHandler
from classes.EmbedHandler import EmbedHandler 
from classes.CanvasHandler import CanvasHandler
from classes.DatabaseHandler import DatabaseHandler
import scripts.StringsHandler as strings

class Bot( EmbedHandler, CanvasHandler, DatabaseHandler, GuildHandler ):

    '''
    COMMAND HANDLER
    '''

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
            if not await self.is_admin( msg.author ) and selected_option[2] == True:

                embed = self.get_embed("unauthorized-user", 
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
            embed = self.get_embed("invalid-command", 
                                            prefix = self.prefix)
            # embed.title = "Invalid Command"
            # embed.description = "Command not recognized."
            # embed.set_footer( text=f"(!) Commands can be found with {self.prefix}help")

        return embed
    
    '''
    LUNABOT USER COMMANDS
    '''
    async def clear_channel( self, msg ):

        # initialize variables
        args = msg.content.lower().split()
        guild = self.get_custom_guild(msg.guild)

        # ensure enough args
        if len( args ) < 2:

            return self.get_embed( "too-few-args-clear",
                                  reply_to=msg 
                                  )
        
        # get channel object
        channel_name = args[1].strip("#<>") # remove #<> if applicable

        # is channel ID
        if channel_name.isnumeric():
            channel_obj = guild.get_channel_obj_by_id( int(channel_name) )

        # is channel name
        else:
            channel_obj = guild.get_channel_obj( channel_name )

        # ensure channel exists
        if channel_obj != None:

            # delete messages
            deleted = await guild.purge_channel( channel_obj, delete_pinned=False )

            # return success
            return self.get_embed( "clear-success",
                                    reply_to=msg,
                                    deleted=deleted,
                                    channel_name=channel_name
                                )

        # channel does not exist, return clear error
        return self.get_embed( "clear-failure",
                        reply_to=msg,
                        channel_name=channel_name)


    async def force_update( self, msg ):
        '''
        User command to manually update the database.
        '''

        if self.update_database():

            embed = self.get_embed( "update-database-success",
                                            reply_to = msg
                                        )
        else:
            embed = self.get_embed( "update-database-failure",
                                            reply_to = msg
                                        )

        return embed
    
    async def handle_api_set( self, msg ):
        '''
        User command to set a new API key: currently stored in program memory, not environmental

        TODO: Make this an environmental variable
        '''

        # grab key
        key = msg.content.split(" ")[1]
        author = msg.author

        # delete message right away
        await msg.delete()

        # validate key, set if its good
        if self.set_api_key(key, verbose=self.dbg):

            return self.get_embed("key-sucess",
                                  mention=author.mention)
            

        else:
            return self.get_embed("key-failure",
                                  mention=author.mention)
    
        
    async def help(self, msg):
        '''
        User command to look up all implemented user commands
        '''

        # Help command, sorry this isnt more automatic. 
        # You'll have to write it out for now
        desc=f'''Hi, thanks for using {self.name}! 
        
        This bot was created by Claire Whittington. Try out the list of commands below:
        
        🤖💬
        '''

        # calculate admin status
        is_admin = await self.is_admin( msg.author )

        # iterate through the commands
        for trigger, (command, description, example_usage, admin_only ) in self.commands.items():

            if is_admin or not admin_only:

                desc += f''' ➭ **{trigger}**
                                ⋅ {description}
                                ⋅ Usage: `{example_usage}`\n
                        '''

        return self.get_embed("help", 
                              reply_to=msg,
                              desc=desc)
    
    async def lookup( self, msg):
        '''
        User command to look up a student within the database and return their info
        '''
        # initialize variables
        desc = ""
        args = msg.content.split()
        guild = self.get_custom_guild( msg.guild )
        filters = {
            "id": args[1] # integration ID
        }
        
        # get records for student
        records = self.retrieve_student( filters )

        # check we grabbed anything
        if len(records) > 0:
            
            # grab identifiers
            name = records[0].name
            sis_id = records[0].sis_id
            pronouns = records[0].pronouns

            # get discord member
            member = guild.get_member_by_nick( name ) 

            # create desc
            desc += f'''
            **Student Info**
            ⋅ Name: {name}
            ⋅ SIS ID: {sis_id}
            ⋅ School ID: {args[1]}
            ⋅ Pronouns: {pronouns}'''

            # if member != None:
            #     desc += f'''
            #     ⋅ Discord User: {member.mention}
            #     '''

            desc += '''

            ** Enrollments **
            '''

            for record in records:

                # course ID
                course_id = record.course_id

                # get ID for the record
                course = self.retrieve_course( {"id":course_id} )[0]

                # create desc
                desc += f"⋅ {course.name}\n"

            # return student found
            return self.get_embed( "lookup-student-success",
                                    reply_to=msg,
                                    desc=desc )
        # no records found, return student not found
        return self.get_embed( "lookup-student-failure",
                                    reply_to=msg,
                                    )

    async def manual_welcome( self, original_msg ):

        # initialize variables
        guild = self.get_custom_guild( original_msg.guild )
        channel = guild.get_channel_obj( self.welcome_channel_str )
        student_role = guild.get_role_obj( self.student_role_str )

        # loop through the channel
        async for msg in channel.history( limit = None ):

            # reset embed variable
            embed = None

            # check if sent by botself  
                # delete msg if pinged student is a student
            if msg.author == self.client.user:

                # roll thru embeds
                for iter_embed in msg.embeds:

                    # extract member from embed desc
                    discord_id = strings.get_discord_id( iter_embed.description )

                    # continue if no ID found in this specific message
                    if discord_id == None:
                        continue

                    # grab member in discord
                    member = await msg.guild.fetch_member( int(discord_id) )

                    # check if member has student role
                    if student_role in member.roles:
                        
                        # delete message
                        await msg.delete()

            else:
                # handle the welcome channel
                embed = await self.welcome( msg, guild=guild, student_role=student_role)

            # send the embed
            if embed != None:
                await embed.send( original_msg.guild )
        

        # return Nothing
        return None

    async def prune(self, msg):
        '''
        User command to prune inactive servers
        '''
        return None
    
    '''
    LUNABOT PUBLIC FUNCTIONS, NON-USER COMMANDS
    '''
    async def delete_embeds_in( self, channel, text=None, where=None ):

        # ensure lowercase
        if text != None:
            text = text.lower()

        # loop through channel history
        async for msg in channel.history( limit = None ):

            # look for text, where
            if text:
                await self.delete_embed_with( msg, text, where )
            
            # just delete the message
            else:
                await msg.delete()

    async def delete_embed_with(self, msg, text, where=None):
        """
        Deletes messages containing specific text in the specified field of embeds.

        Parameters:
            msg (discord.Message): The message object to process.
            text (str): The text to search for.
            where (str): The field to search in (e.g., "description", "title"). Defaults to None (search all fields).
        """
        # loop through embeds
        for embed in msg.embeds:

            # Normalize the `where` parameter for case-insensitivity
            where = where.lower() if where else None

            # Check the specified field or all fields if `where` is None

            # "description"
            if where == "description" and text.lower() in (embed.description or "").lower():
                await msg.delete()
                return
            
            # "title"
            elif where == "title" and text.lower() in (embed.title or "").lower():
                await msg.delete()
                return
            
            # "footer"
            elif where == "footer" and text.lower() in (embed.footer.text or "").lower():
                await msg.delete()
                return

            # "author"
            elif where == "author" and text.lower() in (embed.author.name or "").lower():
                await msg.delete()
                return

            # where not specified
            elif where is None:  # Search all fields
                if (text.lower() in (embed.description or "").lower() or
                        text.lower() in (embed.title or "").lower() or
                        text.lower() in (embed.footer.text or "").lower() or
                        text.lower() in (embed.author.name or "").lower()):
                    await msg.delete()
                    return
                
    async def initialize_guilds( self ):

        # initialize variables
        guilds = self.client.guilds

        # loop through guilds
        for guild in guilds:

            # make new custom guild obj
            new_guild = self.create_guild( guild )

            # add the new guild to list of guilds
            self.add_custom_guild( new_guild, verbose=self.dbg, verify=False )
                
        # return success
        return len( guilds ) > 0
    
    def verify_guilds( self ):

        for guild in self.custom_guilds:

            if not guild.validate( verbose = self.dbg ):

                return False
            
        return True
        

    def initialize_students( self, course_id ):

        # initialize variables
        student_dict = {}
        student_key = "integration_id"
        student_name = 'name'

        # get students for course ID
        students = self.get_students( course_id )[0]

        # loop thru each student
        for student in students:

            # grab their integration ID
            integration_id = student[student_key]

            # handle bad integration key
            if integration_id != None:

                # add them to the dict
                student_dict[ integration_id ] = {
                                                    "name": student[student_name],
                                                    "course_id": course_id,
                                                    "sis_id": student["sis_user_id"], #if "sis_user_id" in student else None,
                                                    "pronouns": student["pronouns"] if "pronouns" in student else None
                                                }
        # return the student dict
        return student_dict
        
    async def update_database( self, msg ):

        student_insertions, course_insertions = self._update_database()

        return self.get_embed("update-database-success",
                              reply_to=msg,
                              student_insertions=student_insertions,
                              course_insertions=course_insertions)
        
    async def welcome(self, msg, guild=None, student_role=None):

        # initialize variables
        args = msg.content.lower().split()
        added = False

        # initialize guild if not added 
        if guild==None:
            guild = self.get_custom_guild( msg.guild )

        assert( guild != None )

        # initialize student role if not added
        if student_role == None:
            student_role = guild.get_role_obj( self.student_role_str )
        
        # get member object
        member = await self.get_member_by_msg( msg )

        # ignore messages sent by staff
        if await self.is_staff( msg.author ) or msg.author == self.client:
            return None

        # Ignore if member already has student role
        if student_role in member.roles:
            return None
        
        # get integration_id from message
        integration_id = args[0]

        # create filters to find student
        filters = {
                "id":integration_id
        }

        # retrieve records for student ID - Include, integration ID, and term 
            # records could include: Main class, one (?) lab section
        records = self.retrieve_student( filters )

        # check length of records > 0
        if len( records ) > 0:

            # if so, process student
                # function: self._process_student()
            embed = await self._process_student( member, records, guild )
            added = True
        
        # otherwise, no records found
            # create failure embed
        else:
            
            # reply to student
            embed = self.get_embed( "added-student-failure-reply",
                                    reply_to=msg,
                                    mention = msg.author.mention
                                   )
            await embed.send( msg.guild, msg.channel )

            # auto send failure to designated channel
            embed = self.get_embed( "added-student-failure",
                                            # reply_to=msg,
                                            integration_id=msg.content,
                                            mention = msg.author.mention
                                        )
        # delete student message 
        await msg.delete()

        # delete messages 
        if added:
            await self.delete_embeds_in( msg.channel, text=f"<@{msg.author.id}>" )

        # return embed
        return embed
    '''

    PRIVATE FUNCTIONS
    '''
    async def _process_student( self, member, records, guild ):

        # initialize variables
        name = records[0].name
        integration_id = records[0].id
        lab_section = None

        # get role object
        student_role = guild.get_role_obj( self.student_role_str )

        # rename student in discord
        await member.edit(nick=name)

        # add "student" role
        await member.add_roles( student_role )
            
        # loop through records
        for record in records:

            # grab course 
            course = self.retrieve_course( {"id":record.course_id} )[0]

            # grab section
            section = course.section

            #print( f"Record name: {record.name} - is lab: {strings.is_lab( record.name )}" )

            # Check if is record is a lab
            if strings.is_lab( course.name ):

                # get lab role
                lab_role = guild.get_role_obj( f"Lab {section}" )
                
                # add the lab role
                await member.add_roles( lab_role )

                # assign for embed
                lab_section = section
        return self.get_embed( "added-student-success", 
                              name=name,
                              integration_id=integration_id,
                              lab_section=lab_section,
                              mention=member.mention
                              )
    def _update_database( self, ):

        # Get active guilds
        active_guilds = self.get_active_guilds()
        course_insertions = 0
        student_insertions = 0
        updates = 0

        # confirmation message
        if self.dbg:
            print("Updating database...")
            print(f"Total active guilds: { len(active_guilds) }")

        # loop through active guilds
        for guild in active_guilds:

            # display the guild
            if self.dbg:
                print("Updating database for current guild:")
                guild.display()

            # Get course code
            course_code = guild.main_course.course_code
            term = guild.main_course.term
        
            # grab all my courses related to course_code 
                # Labs included
            courses = self.get_all_courses_with( course_code )

            # Loop through courses
            for course in courses:
                
                # get section
                section = strings.get_section( course[ "name" ] )

                # initialize the course in course db
                updates = {
                            "id":course["id"],
                            "term":term
                }

                # insert the course in db if not in 
                if not self.exists( "Course", updates ):
                    self.insert_course( course, term, section )
                    course_insertions += 1

                # initialize students for that course code
                student_dict = self.initialize_students( course["id"] )
            
                # Loop through the student dict items
                for integration_id, values in student_dict.items():

                    # Get name
                    name = values["name"]

                    # get course id
                    course_id = values["course_id"]

                    # get pronouns
                    pronouns = values[ "pronouns" ]

                    # get sis id
                    sis_id = values[ "sis_id" ]

                    # create updates dict
                    student_info = {
                            "id":integration_id,
                            "course_id":course_id,
                            "name":name,
                            "pronouns":pronouns,
                            "sis_id":sis_id,
                    }

                    # insert student if not in db
                    if not self.exists( "Student", student_info ):
                        student_insertions += 1
                        self.insert_student( student_info )

                    # Otherwise, student is in db, so check to update their info
                        # TODO: Implement this
                    else:
                        self.update_student( student_info )
                    
        # confirmation message
        if self.dbg:
            print("Finished updating db")

        # Return success for now
        return student_insertions, course_insertions
    
    def __init__(self, name, client, prefix, TOKEN):

        # Define ready flag
        self.ready = False

        # initialize important stuff
        self.client     = client    # discord client o bject
        self.name       = name      # str
        self.prefix     = prefix    # str
        self.token      = TOKEN     # str | TODO: make this environmental variable
        self.dbg        = cfg.dbg   # bool
        self.staff_roles = cfg.staff_roles # string of roles
        self.reset_db   = cfg.reset_db     # bool; resets the db on start

        # initialize additional file variables
        self.invite_link = sc.invite_link # str
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
        ] + self.staff_roles

        self.required_channels = [
            self.welcome_channel_str,            # channel to welcome new students
            self.added_students_channel_str,     # channel to log any added students
            self.admin_channel_str,              # channel for admin commands
            self.admin_log_channel_str,          # log for admin commands
            self.student_cmds_channel_str,       # channel for student commands
            self.student_cmds_log_channel_str    # log for student commands
        ]

        # initialize general variables
        self.active_guild = None

        # establish other classes
        GuildHandler.__init__( self, self.required_channels, self.required_roles)
        EmbedHandler.__init__( self ) 
        CanvasHandler.__init__( self )
        DatabaseHandler.__init__(self, cfg.db_path, dbg=cfg.dbg, reset_db=self.reset_db)
        
        # initialize all available commands for users to call
        self.commands = {   self.prefix + "help": ( self.help, # command to run
                                                    "List of commands", # help desc
                                                    f"{self.prefix}help", # example usage
                                                    False, # is admin-only command
                            ),
                            # ),
                            # self.prefix + "restart":(
                            #                     self.restart,
                            #                     "Restart Bot",
                            #                     True
                            # ),
                            self.prefix + "prune":(
                                                self.prune,
                                                "Force bot to leave all inactive discords. NOTE: NOT IMPLEMENTED BUT SUPER EASY",
                                                f"{self.prefix}prune", # example usage
                                                True
                            ),
                            self.prefix + "clear":(
                                                self.clear_channel,
                                                f"Clear all messages in a given channel except for pinned messages. Usage: {prefix}.clear <#channel>",
                                                f"{self.prefix}clear <#channel-name>", # example usage
                                                True
                            ),
                            self.prefix + "welcome":(
                                                self.manual_welcome,
                                                "Manually process every student in the #welcome channel. NOTE: Weird bug happening here",
                                                f"{self.prefix}welcome", # example usage
                                                True
                            ),
                            self.prefix + "update":(
                                                self.update_database,
                                                "Force-updates the database.",
                                                f"{self.prefix}update", # example usage
                                                True
                            ),
                            self.prefix + "set_api_key":(
                                                self.handle_api_set,
                                                "Reset the Canvas API key. Deletes immediately when called.",
                                                f"{self.prefix}set_api_key <api key>", # example usage
                                                True
                            ),
                            # self.prefix + "update_lab":(
                            #                     self.update_lab,
                            #                     "Update a student's lab section",
                            #                     True
                            #),
                            self.prefix + "lookup":(
                                                self.lookup,
                                                "View a student's current profile",
                                                f"{self.prefix}lookup <student-id>", # example usage
                                                True
                            )


                        }
    