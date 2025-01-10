from classes.SQLHandler import SQLHandler, Course, Student

class DatabaseHandler( SQLHandler ):

    def __init__(self, db_path, dbg=False, reset_db=False) -> None:

        # initialize variables
        self.db_path = db_path
        self.dbg = dbg
        self.reset_db = reset_db

        # Initialize inherited classes
        SQLHandler.__init__(self, self.db_path,  dbg=self.dbg, reset=self.reset_db )

    def exists( self, model_str:str, filters:dict ):

        if model_str == "Course":
            model = Course
        
        elif model_str == "Student":
            model = Student
 
        return self.check_exists( model, filters )


    def insert_course( self, course, term, section ):

        return self.insert( Course( 
                                    id = course["id"],
                                    name = course["name"],
                                    term = term,
                                    section = section
                                    ) 
                            )

    def insert_student( self, updates ):

        return self.insert( Student( 
                                    id = updates["id"],
                                    name = updates["name"],
                                    course_id = updates["course_id"],
                                    pronouns = updates["pronouns"],
                                    sis_id = updates["sis_id"]
                                    ) 
                            )
    def retrieve_student( self, filters ):
        return self.retrieve( Student, filters )

    def retrieve_student_extended( self, filters, course_filters):


        # initialize variables
        return_list = []
        
        # retrieve records for student
        records = self.retrieve_student( filters ) # TODO: this will only work when we can search by "CS-126"

        
        
        return return_list
            

    def retrieve_course( self, filters ):
        return self.retrieve( Course, filters )
    
    def update_student( self, filters ):
        pass

    def update_course( self, filters ):
        pass

     