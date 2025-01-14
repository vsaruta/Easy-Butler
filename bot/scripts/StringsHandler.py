import re
from datetime import datetime

def extract_sec_pattern( text ):
    '''
    Regular expression to match SEC00 followed by any number of digits
    '''
    pattern = r"SEC00\d+"
    matches = re.findall(pattern, text)

    if len(matches) == 0:
        return None
    
    return matches

def find_course_name_by_id( course_list, course_id):
    for course in course_list:
        if course['id'] == course_id:
            return course['name']
    return None

def get_discord_id( text ):
    id = None
    match = re.search(r"<@(\d+)>", text) 

    if match:
        id = match.group(1)  # The first captured group
    return id
def get_classcode(name):
    # Extracts the class code and formats it with a hyphen (e.g., "CS-126")
    match = re.search(r"\b([A-Z]{2,})(\d{3})\b", name)
    return f"{match.group(1)}-{match.group(2)}" if match else None

def get_section(name):
    '''
    Calculates NAU course section given a string. Matches to anything with "00" plus a number.
    '''

    pattern = r"00\d+"
    matches = re.findall(pattern, name)

    if len(matches) != 0:
        return matches[0]
    
    return None

def get_season(name):
    # Extracts the season (e.g., "Fall")
    match = re.search(r"\b(Fall|Spring|Summer|Winter)\b", name, re.IGNORECASE)
    return match.group(0).capitalize() if match else None

def get_year(name):
    # Extracts the year (e.g., "2024")
    match = re.search(r"\b\d{4}\b", name)
    return match.group(0) if match else None

def get_current_semester_string():

    # Get the current date
    current_date = datetime.now()

    # Define season date ranges
    sp_start, sp_end = datetime(current_date.year, 1, 1), datetime(current_date.year, 5, 1)
    su_start, su_end = datetime(current_date.year, 5, 2), datetime(current_date.year, 8, 1)
    f_start, f_end = datetime(current_date.year, 8, 2), datetime(current_date.year, 12, 27)
    w_start, w_end = datetime(current_date.year, 12, 28), datetime(current_date.year, 12, 31)

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

    season_year_str = f"{current_season} {current_date.year}"
    return season_year_str
    

def is_lab( text ):

    '''
    Takes a string which contains something like "CS-126L" and determines if it is a lab or not
    '''
    pattern = r"\dL"
    matches = re.findall(pattern, text)

    return len( matches ) > 0
