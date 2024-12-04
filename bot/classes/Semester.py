import re 
from datetime import datetime
from classes.Canvas import Canvas

# CHATGPT wrote most of this so sorry its ugly
# I just hate string matching

class Semester:

    def calculate_term( self ):

        szn = self.season.lower()

        szn_dict = {
                    "spring":"1",
                    "summer":"4",
                    "fall":"7",
                    "winter":"8"
                    }

        return "1" + self.year[2:] + szn_dict[szn]
    
    def extract_sec_pattern(self, text):
        # Regular expression to match SEC00 followed by any number of digits
        pattern = r"SEC00\d+"
        matches = re.findall(pattern, text)
        return matches

    def get_classcode(self, name):
        # Extracts the class code and formats it with a hyphen (e.g., "CS-126")
        match = re.search(r"\b([A-Z]{2,})(\d{3})\b", name)
        return f"{match.group(1)}-{match.group(2)}" if match else None

    def get_lab_sections(self, search_str=None, my_courses=None):

        sections = []

        if my_courses == None:
            my_courses = self.my_courses

        for course in my_courses:
            name = course['name']
            if search_str in name:
                section = f"Lab " + name[-3:]
                sections.append(section)

        return sections

    def get_season(self, name):
        # Extracts the season (e.g., "Fall")
        match = re.search(r"\b(Fall|Spring|Summer|Winter)\b", name, re.IGNORECASE)
        return match.group(0).capitalize() if match else None

    def get_year(self, name):
        # Extracts the year (e.g., "2024")
        match = re.search(r"\b\d{4}\b", name)
        return match.group(0) if match else None
    
    def get_current_semester_string(self):
        # Get the current date
        current_date = datetime.now()

        # Define season date ranges
        sp_start, sp_end = datetime(current_date.year, 1, 13), datetime(current_date.year, 5, 3)
        su_start, su_end = datetime(current_date.year, 5, 4), datetime(current_date.year, 7, 31)
        f_start, f_end = datetime(current_date.year, 8, 1), datetime(current_date.year, 12, 27)
        w_start, w_end = datetime(current_date.year, 12, 28), datetime(current_date.year + 1, 1, 12)

        # Determine current season
        if sp_start <= current_date <= sp_end:
            current_season = 'Spring'
        elif su_start <= current_date <= su_end:
            current_season = 'Summer'
        elif f_start <= current_date <= f_end:
            current_season = 'Fall'
        elif w_start <= current_date or current_date <= w_end:
            current_season = 'Winter'
        else:
            current_season = None

        season_year_str = f"{current_season} {current_date.year if current_season != 'Winter' else current_date.year + 1}"
        return season_year_str

    def get_course_ids(self, course_str):

        ids = []

        for course in self.my_courses:

            # get class name  
            name = course['name']
            
            # grab the course ID
            if course_str in name:
                id = course['id']
                ids.append( id )

        return ids 

    
    def is_current_semester(self):
        # Compare this semester's season and year with the current semester string
        current_semester_str = self.get_current_semester_string()
        return f"{self.season} {self.year}" == current_semester_str
    
    def set_channels( self, welcome_channel, added_students_channel, 
                                             admin_channel,
                                             admin_log_channel,
                                             student_cmds_channel,
                                             student_cmds_log_channel):
        
        self.welcome_channel_obj          = welcome_channel
        self.added_students_channel_obj   = added_students_channel
        self.admin_channel_obj            = admin_channel
        self.admin_log_channel_obj        = admin_log_channel
        self.student_cmds_channel_obj     = student_cmds_channel
        self.student_cmds_log_channel_obj = student_cmds_log_channel
        
    def set_courses(self, my_courses):

        # set courses
        self.my_courses = my_courses

        # get main course IDs
        str = f"Combo {self.classcode} ({self.term}"
        self.combo_ids = self.get_course_ids(str)  # str of main combo class id

        # get lab ids
        str = f"{self.classcode}L ({self.term}"
        self.lab_ids   = self.get_course_ids(str)  # list of lab ids
        self.lab_sections =  self.get_lab_sections(str, self.my_courses) # list of lab names

    def __init__(self, guild) -> None:

        # sisid format: 1241-NAU00-CS-480-SEC001-3810.NAU-PSSIS
        self.guild  = guild  
        self.season = self.get_season(guild.name)
        self.year   = self.get_year(guild.name)
        self.term   = self.calculate_term()
        self.active = self.is_current_semester()
        self.classcode = self.get_classcode(guild.name)  

        # set class IDs
        self.my_courses = None
        self.combo_ids  = None
        self.lab_ids    = None
        self.lab_sections = None

        # set discord channels
        self.welcome_channel_obj          = None
        self.added_students_channel_obj   = None
        self.admin_channel_obj            = None
        self.admin_log_channel_obj        = None
        self.student_cmds_channel_obj     = None
        self.student_cmds_log_channel_obj = None

        # log - student adding success channel
        # log - failure adding channel
        # 
        self.student_role_obj  = None

        #self._display_guild()

    def _display_guild(self):
        string = f'''
        Guild name: {self.guild.name}
            Active: {self.active}
            Code: {self.classcode}
            Season: {self.season}
            Year: {self.year}
        '''

        print(string)