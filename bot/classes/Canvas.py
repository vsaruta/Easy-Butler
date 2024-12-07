import requests
from secret import API_KEY

class Canvas:

    def __init__(self) -> None:
    
        #initialize API Key
        self.API_KEY = API_KEY 

        # set up per-page
        self.per_page = 100
        self.page = 1

        # initialize general headers and params
        self.base_url = "https://canvas.nau.edu/api/v1/"
        self.base_headers  = { "Authorization": f"Bearer {self.API_KEY}" }
        self.base_params   = {
            "per_page": self.per_page,
            "page": self.page
        }

    
    def get_my_courses(self):

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

    def retrieve_students(self, course_id):
        
        # initialize variables 
        url = self.base_url + f'/courses/{course_id}/students' 
        students = []
        not_done = True

        # loop
        while not_done:

            # make request
            resp = self._get(url)

            # append to students
            students.append(resp.json())

            # get next url
            if 'next' in resp.links.keys():

                url = resp.request.links['next']['href']
            
            # nope we are good!
            else:

                not_done = False

        return students
    
    def retrieve_tas(self, course_id):
        ta_list = []
        return ta_list
    
    def validate_api_key(self, key=None, keep_resp=None, verbose=False):

        url = self.base_url + "users/self"

        if key==None:
            headers=self.base_headers
        else:
            headers  = { "Authorization": f"Bearer {key}" }
        
        resp = self._get(url, headers=headers)

        if self._resp_200(resp):
            return True
        else:
            if verbose:
                print(f"Invalid API key. Status Code: {resp.status_code}")
                print("Response:", resp.json())
            return False

    def set_api_key(self, api_key, verbose=False):
        if self.validate_api_key(key=api_key, verbose=verbose):
            self.API_KEY=api_key
            return True
        return False


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
    # combo_class = 28980
    # result = canvas.get(combo_class)
    # print(result)

#_main()