import requests

API_KEY = "19664~re629MhEknKm8c2mnQnCCGCTW38zWQ63NnLRaYvyxumAKC8wH3GwrP8Ut8LMwkXV"
# Replace with your Canvas API URL and API key
CANVAS_API_URL = "https://canvas.nau.edu/api/v1/courses"

def get_courses():
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    courses = []
    page = 1
    per_page = 100  # You can set this to a lower number if needed

    while True:
        params = {
            "per_page": per_page,
            "page": page
        }
        response = requests.get(CANVAS_API_URL, headers=headers, params=params)

        if response.status_code == 200:
            page_courses = response.json()
            if not page_courses:
                break  # Exit the loop if no more courses are found
            courses.extend(page_courses)
            page += 1  # Move to the next page
        else:
            print(f"Error: {response.status_code} - {response.text}")
            break

    return courses

def display_courses(courses):
    if courses:
        print("Your Courses:")
        for course in courses:
            print(f"- {course['name']} (ID: {course['id']})")
    else:
        print("No courses found.")

if __name__ == "__main__":
    courses = get_courses()
    display_courses(courses)
