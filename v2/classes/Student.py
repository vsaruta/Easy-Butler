class Student:

    def __init__(self, author) -> None:

        # Canvas side of things
        self.name           = None     # Ex: "Claire Whittington"
        self.integration_id = None     # Ex: "cew374"
        self.numeric_id     = None     # Ex: "006168904"
        self.combo_class_id = None     # ID For their combo class
        self.lab_id         = None     # ID For their lab class

        # Discord side of things
        self.author = author           # discord object

    def initialize_student( self ):
        pass