from sqlmodel import SQLModel, Field, create_engine, Session, Relationship, select

# Custom handler
class SQLHandler:
    def __init__(self) -> None:
        self.engine = create_engine('sqlite:///database/CS126.db')
        SQLModel.metadata.drop_all(self.engine)
        SQLModel.metadata.create_all(self.engine)

    def check_exists(self, model: SQLModel, filters: dict) -> bool:
        """
        Check if a record exists in the database based on filters.

        Args:
            model (SQLModel): The model class to query.
            filters (dict): A dictionary of field names and values to filter by.

        Returns:
            bool: True if a record exists, False otherwise.

        Example Usage:
            exists = self.check_exists(Student, {"id": "S001"})
        """
        with Session(self.engine) as session:
            query = select(model)
            for key, value in filters.items():
                query = query.where(getattr(model, key) == value)
            result = session.exec(query).first()
            return result is not None
        
    def insert(self, model_instance: SQLModel) -> bool:
        """
        Insert a new record into the database, if it doesn't already exist.
        
        Example Usage: 
            handler.insert(Course(id=1, name="CS126"))
            handler.insert(Student(id="S001", name="John Doe", main_class=1, lab_class=1))

        """
        model = type(model_instance)
        filters = {"id": model_instance.id}  # Assuming 'id' is the unique field
        if self.check_exists(model, filters):
            return False
        else:
            with Session(self.engine) as session:
                session.add(model_instance)
                session.commit()
                return True

    def remove(self, model: SQLModel, record_id: int) -> bool:
        """Remove a record from the database by ID."""
        with Session(self.engine) as session:
            statement = select(model).where(model.id == record_id)
            result = session.exec(statement).first()
            if result:
                session.delete(result)
                session.commit()
                return True
        return False

    def update(self, model: SQLModel, record_id: int, updates: dict) -> bool:
        """Update a record in the database."""
        with Session(self.engine) as session:
            # Retrieve the record by ID
            statement = select(model).where(model.id == record_id)
            record = session.exec(statement).first()

            if record:
                # Apply updates
                for key, value in updates.items():
                    setattr(record, key, value)
                session.add(record)
                session.commit()
                return True
            
        return False


    def retrieve(self, model: SQLModel, filters: dict = None) -> list[SQLModel]:
        """
        Retrieve records from the database based on optional filters.
        
        Args:
            model (SQLModel): The SQLModel class to query.
            filters (dict, optional): A dictionary of column-value pairs for filtering.
        
        Returns:
            list[SQLModel]: A list of records that match the filters.
        """
        with Session(self.engine) as session:
            # Start with a base query
            query = select(model)

            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    # Use getattr to dynamically access model fields
                    query = query.where(getattr(model, key) == value)

            # Execute the query and return results as a list
            results = session.exec(query).all()
            return results

# Student Table
class Course(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, default=None )
    section: str = Field(max_length=3, default=None, nullable=True)

class Student(SQLModel, table=True):
    id: str = Field(max_length=10, default=None, primary_key=True)
    name: str = Field(max_length=100, default=None)
    main_class: int = Field(default=None, foreign_key="course.id", nullable=True)
    lab_class: int = Field(default=None, foreign_key="course.id",  nullable=True)


def _main():

    # Initialize handler
    handler = SQLHandler()

    # Insert a course and a student
    handler.insert(Course(id=1))
    handler.insert(Student(id="S001", name="John Doe", main_class=1, lab_class=1))

    # Update a student's name
    handler.update(Student, record_id="S001", updates={"name": "oop Doe"})

    # Retrieve all students
    students = handler.retrieve(Student)
    print(students)

    # Retrieve students with a specific main_class
    students_in_main_class = handler.retrieve(Student, filters={"main_class": 1})
    print(students_in_main_class)

#_main()