import requests
from secret import API_KEY

class Canvas:

    def __init__(self) -> None:
    
        #initialize API Key
        self.API_KEY = API_KEY 
        #self.API_KEY = "19664~re629MhEknKm8c2mnQnCCGCTW38zWQ63NnLRaYvyxumAKC8wH3GwrP8Ut8LMwkXV" 

        # set up per-page
        self.per_page = 1000
        self.page = 1 

        # initialize general headers and params
        self.base_url = "https://canvas.nau.edu/api/v1/"
        self.base_headers  = { "Authorization": f"Bearer {self.API_KEY}" }
        self.base_params   = {
            "per_page": self.per_page,
            "page": self.page
        }

    def get_student_names(self):

        pass

    def get_all_courses(self):

        # create course list 
        courses = [] 

        # Create link
        url = self.base_url + "courses"

        # send post
        resp = self._get(url)

        # check if response was good
        if self._resp_200(resp):

            courses = resp.json()

        return courses
        

    def _get(self, url, headers=None, params=None):
        
        # set headers
        if headers==None:
            headers = self.base_headers
        
        # set params
        if params==None:
            params  = self.base_params

        # send get 
        return requests.get(url, headers=headers, params=params)

    def _resp_200(self, resp):
        return resp.status_code == 200

def _main():

    canvas = Canvas()

    courses = canvas.get_all_courses()

    if courses:

        print("Your Courses:")

        for course in courses:
            print(f"- {course['name']} (ID: {course['id']})")
    else:
        print("No courses found.")

#_main()