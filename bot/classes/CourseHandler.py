import scripts.StringsHandler as strings

# CHATGPT wrote most of this so sorry its ugly
# I just hate string matching

class NAUCourse():

    def calculate_term( self ):

        szn = self.season.lower()

        return "1" + self.year[2:] + self.szn_dict[ szn ]
    
    def display( self ):

        print( f'''
            === NAU COURSE INFO ===
            Associated Discord: {self.guild_name}
            Current Semester: {strings.get_current_semester_string()}
            Active: {self.is_current_semester()}
            Season: {self.season}
            Year: {self.year}
            Term: {self.term}
            =======================
            ''')
        

    # def get_course_ids(self, course_str):

    #     ids = []

    #     for course in self.my_courses:

    #         # get class name  
    #         name = course['name']
            
    #         # grab the course ID
    #         if course_str in name:
    #             id = course['id']
    #             ids.append( id )

    #     return ids 

    def is_current_semester(self):
        # Compare this semester's season and year with the current semester string
        current_semester_str = strings.get_current_semester_string()

        #print( f"{self.season} {self.year} being compared to {current_semester_str}" )
        return f"{self.season} {self.year}" == current_semester_str
    

    def __init__(self, guild_name) -> None:

       # initialize variables
        self.szn_dict = {
                        "spring":"1",
                        "summer":"4",
                        "fall":"7",
                        "winter":"8"
                        }
        
        # sisid format: 1241-NAU00-CS-480-SEC001-3810.NAU-PSSIS
        self.guild_name = guild_name
        self.season = strings.get_season( guild_name )
        self.year   = strings.get_year( guild_name )
        self.course_code = strings.get_classcode( guild_name ) 

        # calculated variables
        self.term   = self.calculate_term()

