import time
import discord
from discord.utils import get
from classes.CourseHandler import NAUCourse

SLEEP = 0.6

# Overarching guild class
class GuildHandler():

   # Custom class to build on top of native guild
    class CustomGuild( ):

        def __init__(self, guild: discord.Guild, required_channels, required_roles):

            # initxfialize semester 
            self.main_course = NAUCourse( guild.name )
            # self.main_course.display()

            # initialize parameters
            self.guild = guild
            self.required_roles = required_roles
            self.required_channels = required_channels
        
        def display( self ):

            print( f'''
            === GUILD INFO ===
            Guild Name: {self.guild.name}
            Required Roles   : [STATUS: {self.validate_roles()}]
            Required Channels: [STATUS: {self.validate_channels()}]
            ==================
            ''')
            self.main_course.display() 

        async def delete_message( self, msg, delete_pinned=False ):

            # Check the pinned condition
            if msg.pinned and not delete_pinned:

                # return false
                return False 
            
            # otherwise, delete the message
            await msg.delete()

            # return true
            return True
            
        async def get_admins( self, ids=False ):
            admins = []
            # Async iterate over the members
            async for member in self.guild.fetch_members():
                if member.guild_permissions.administrator:
                    if ids:
                        admins.append(member.id)
                    else:
                        admins.append(member)

            return admins

        def get_channel_obj(self, channel_name):
            """Get a channel object by name."""
            return get(self.guild.channels, name=channel_name)
        
        def get_channel_obj_by_id( self, channel_id ):
            return get(self.guild.channels, id=channel_id)

        def get_member_by_nick( self, nickname ):
            found_member = None

            for member in self.guild.members:
                if member.display_name == nickname:
                    found_member = member
                    break
            return found_member
        
        def get_members_with_role( self, text, ids=False ):

            members = []
            role = self.get_role_obj( text )

            if role != None:

                for member in self.guild.members:

                    if role in member.roles:
                        
                        if ids:
                            members.append( member.id )
                        else:
                            members.append( member )

            return members

        def get_role_obj(self, role_name):
            """Get a role object by name."""
            return get(self.guild.roles, name=role_name)
        
        def has_role( self, member, role_name):

            for role in member.roles:
                if role.name.lower() == role_name.lower():
                    return True
    
            return False

        async def purge_channel( self, channel:discord.channel, delete_pinned=False):
            '''
            Deletes channel messages in a channel object
            '''

            # intialize variables
            count = 0

            # loop through msg history
            async for msg in channel.history( limit = None ):
                
                # try to delete
                deleted = await self.delete_message( msg, delete_pinned )
            
                # see if deleted
                if deleted:

                    # increase count
                    count += 1

                time.sleep( SLEEP )
            # return count
            return count

        def validate_channel(self, channel_name):
            """Check if a channel exists in the guild."""
            return self.get_channel_obj(channel_name) != None

        def validate_channels(self, channel_names=None, verbose=False):
            """Validate the existence of multiple channels."""
            all_valid = True
            desc = ""

            channel_names = channel_names or self.required_channels
            for channel_name in channel_names:
                if not self.validate_channel(channel_name):
                    all_valid = False
                    desc += f"- Channel Error: `#{channel_name}` not found.\n"

            if verbose and desc:
                print(desc)

            return all_valid

        def validate_role(self, role_name):
            """Check if a role exists in the guild."""
            return self.get_role_obj(role_name) != None

        def validate_roles(self, role_names=None, verbose=False):
            """Validate the existence of multiple roles."""
            all_valid = True
            desc = ""

            role_names = role_names or self.required_roles
            for role_name in role_names:
                if not self.validate_role(role_name):
                    all_valid = False
                    desc += f"- Role Error: '{role_name}' does not exist.\n"

            if verbose and desc:
                print(desc)

            return all_valid

        def validate(self, verbose ):
            """Validate the guild setup."""
            channels_valid = self.validate_channels( verbose=verbose)
            roles_valid = self.validate_roles( verbose=verbose)

            if not (channels_valid and roles_valid) and ( verbose ):

                print(f"Could not validate {self.guild.name}!")
            return channels_valid and roles_valid

        def is_active( self ):
            return self.main_course.is_current_semester()
        

    def __init__(self, required_channels=None, required_roles=None) -> None:
        self.custom_guilds = []
        self.required_channels = required_channels or []
        self.required_roles = required_roles or []

    def add_custom_guild( self, custom_guild, verbose=False, verify=False ):
        
        # verify controls
        if verify:

            # check to verify
            if custom_guild.validate( verbose ):
                self.custom_guilds.append( custom_guild )
                return True
            
            # couldn't verify the server
            return False

        # no verify, so just add it 
        self.custom_guilds.append( custom_guild )

        # added the guild
        return True

    def add_discord_guild( self, guild:discord.Guild, verbose=False):

        # create guild
        new_guild = self.create_guild( guild )

        # Add in valid guild
        if new_guild.validate( verbose ):
            self.custom_guilds.append( guild )
            return True
        
        return False

    def create_guild(self, guild:discord.Guild ):
        return self.CustomGuild( guild, self.required_channels, self.required_roles )

    def get_active_guilds( self ):
        '''
        Retrieves any active guilds that the bot can see.

        A guild is determined to be active if it matches the current term. Multiple terms may be active.
        
        Example: CS126 Spring 2025, INF110 Spring 2025 <- Both active during Spring 2025
        '''

        active_guilds = []

        for custom_guild in self.custom_guilds:

            if custom_guild.is_active():
                active_guilds.append( custom_guild )

        return active_guilds
    
    def get_custom_guild( self, guild:discord.Guild ):
        
        # loop through our guilds
        for custom_guild in self.custom_guilds:
            
            # see if the guild matches
            if guild.id == custom_guild.guild.id:
                
                # return correct guild
                return custom_guild
            
        # No guild found 
        return None
    
    async def get_member_by_msg( self, msg ):
        return await self.get_member_by_author( msg.author )

    async def get_member_by_author( self, author ):
        return await author.guild.fetch_member( author.id )
            
    async def is_admin( self, author ):

        guild = self.get_custom_guild( author.guild )
        admin_ids = await guild.get_admins( ids=True )

        return author.id in admin_ids

    async def is_staff( self, author ):

        # get guild
        guild = self.get_custom_guild( author.guild )
        member = await self.get_member_by_author( author )

        # loop through staff roles
        for rolename in self.staff_roles:

            # get role obj
            role = guild.get_role_obj( rolename )

            # check if role is in member roles
            if role in member.roles:
                return True
            
        # member is not staff
        return False