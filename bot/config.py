# define some common ids
claire=343857226982883339
owner=claire

# debug status
dbg = True 
reset_db = False

#json file - for discord embed formatting
json_file = "json/embeds.json"

# path to database
db_path = "database/new_CS126.db"

# bot strings
name="LunaBot"
prefix="luna."
student_role = "Students"

# channel strings
welcome_channel_str          = "welcome"
added_students_channel_str   = "processed-students"
admin_channel_str            = "admin-commands"
admin_log_channel_str        = "admin-logs"
student_cmds_channel_str     = "student-commands"
student_cmds_log_channel_str = "student-command-logs"
dft_color     = 0x6495ED # hex
success_color = 0x21D375 # hex
error_color   = 0xF95C52 # hex

# how often the bot updates (in hours)
HOURS_UPDATE = 12

# roles which we consider to be staff
staff_roles = [ 
                "Instructor",
                "Supplementary Instructor",
                "TA", 
                "Lab Instructor"
                ]

# emojis
thumbs_up = '👍'

'''
# old config stuff
#CSV_FILE = "cs126_student_list.csv"
#LOG_FILE = "discord_log.txt"
#STUDENT_ROLE = "Students"
#FORMER_ROLE = "Former Students"
#WELCOME_CHANNEL_NAME = "welcome"
#BOT_CHANNEL_NAME = "bot_log"
#NEUTRAL_COLOR = 0x4895FF # hex
#CAUTION_COLOR = 0xFFF253 # hex
SUCCESS_COLOR = 0x21D375 # hex
ERROR_COLOR   = 0xF95C52 # hex
#WAIT_FOR_RATE_LIMIT = 0 # in seconds
#BOT_REACTION = '👍'
'''