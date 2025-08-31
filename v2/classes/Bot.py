import discord
import secret as sc
import config as cfg
from datetime import datetime
from classes.Embed import Embed
from classes.Canvas import Canvas
from classes.Semester import Semester


class Bot:
    '''
    PUBLIC FUNCTIONS
    '''

    def get_channel_obj(self, guild, channel_name):
        return discord.utils.get(guild.channels, name=channel_name)

    def get_role_obj(self, guild, role_name):
        return discord.utils.get(guild.roles, name=role_name)

    async def handle_msg(self, msg):
        # initialize variables
        author_id = msg.author.id

        # Get command
        argv = msg.content.split()
        command = argv[0].lower()

        # initialize embed
        embed = self.embed.initialize_embed("Title", "Desc", self.dft_color)
        embed.timestamp = datetime.now()

        # check if command is valid
        if command in self.commands.keys():
            # Grab the command tuple
            selected_option = self.commands.get(command)

            # --- permission check (owner OR admin) ---
            is_owner = (author_id == self.owner)
            is_admin = self._is_admin(msg.author)  # uses cfg.admin_list
            if selected_option[2] and not (is_owner or is_admin):
                embed.title = "Unauthorized Command"
                embed.description = "Sorry, only authorized users can use this command."
                return embed  # return early
            # -----------------------------------------

            # run the selected option
            await selected_option[0](msg, embed)

        else:
            embed.title = "Invalid Command"
            embed.description = "Command not recognized."
            embed.set_footer(text=f"(!) Commands can be found with {self.prefix}help")

        return embed

    async def help(self, msg, embed):
        # help command
        embed.title = f"{self.name} help!"
        is_admin = self._is_admin(msg.author)

        # add in all items
        for key, val in self.commands.items():
            # admins see all commands, non-admins only non-admin commands
            if is_admin or not val[2]:
                embed.add_field(name=f"{key} - {val[1]}", value="", inline=False)

    async def initialize_guilds(self):
        """Pick the active guild/semester and cache course names; log details."""
        guilds = self.client.guilds
        my_courses = self.canvas.get_my_courses()  # expect list[dict] with 'id','name' etc.

        # Build a map for pretty logging / lookups
        self.course_names = {}
        try:
            for c in my_courses or []:
                cid = c.get("id")
                nm = c.get("name") or c.get("course_code") or str(cid)
                if cid is not None:
                    self.course_names[int(cid)] = str(nm)
        except Exception:
            # stay resilient even if shape is different
            pass

        self._log(f"[Canvas] get_my_courses -> {len(self.course_names)} course(s) cached for name lookup.")

        for guild in guilds:
            semester = Semester(guild)

            if not semester.is_current_semester():
                self._log(f"[Semester] Leaving inactive guild: {guild.name} ({guild.id})")
                await guild.leave()
            elif len(guilds) == 0:
                self.current_semester = None
            else:
                welcome_channel_obj = self.get_channel_obj(guild, self.welcome_channel_str)
                log_channel_obj = self.get_channel_obj(guild, self.log_channel_str)

                semester.set_courses(my_courses)
                semester.set_channels(welcome_channel_obj, log_channel_obj)

                self.current_semester = semester
                self._log(f"[Semester] ACTIVE guild: {guild.name} ({guild.id})")
                self._log(f"[Semester] welcome=#{getattr(welcome_channel_obj,'name',None)}  "
                          f"bot_log=#{getattr(log_channel_obj,'name',None)}")

                # If your Semester exposes combo_ids / lab_ids / lab_sections here, log them:
                try:
                    self._log(f"[Semester] combo_ids={getattr(semester,'combo_ids',[])} "
                              f"lab_ids={getattr(semester,'lab_ids',[])} "
                              f"lab_sections={getattr(semester,'lab_sections',[])}")
                    for cid in getattr(semester, 'combo_ids', []):
                        self._log(self._fmt_course(cid, prefix="  combo → "))
                    for cid in getattr(semester, 'lab_ids', []):
                        self._log(self._fmt_course(cid, prefix="  lab   → "))
                except Exception:
                    pass

    async def invite(self, msg, embed):
        pass

    async def canvas_info(self, msg, embed):
        """Admin: show which guild/semester is active and list course IDs/names."""
        if self.current_semester is None:
            embed.title = "Canvas / Semester Info"
            embed.description = "Not initialized. Try again after startup."
            return

        sem = self.current_semester
        embed.title = "Canvas / Semester Info"
        embed.add_field(name="Guild", value=f"{sem.guild.name} ({sem.guild.id})", inline=False)

        combos = getattr(sem, "combo_ids", []) or []
        labs   = getattr(sem, "lab_ids", []) or []
        sects  = getattr(sem, "lab_sections", []) or []

        if combos:
            lines = []
            for cid in combos:
                lines.append(self._fmt_course(cid, as_text=True))
            embed.add_field(name="Combo course IDs", value="\n".join(lines), inline=False)

        if labs:
            lines = []
            for i, cid in enumerate(labs):
                sec = sects[i] if i < len(sects) else "?"
                lines.append(self._fmt_course(cid, as_text=True) + f"  (Lab section: {sec})")
            embed.add_field(name="Lab course IDs", value="\n".join(lines), inline=False)

        # Also mirror in console
        self._log("[Canvas] ---- canvas_info ----")
        self._log(f"Guild: {sem.guild.name} ({sem.guild.id})")
        for cid in combos:
            self._log(self._fmt_course(cid, prefix="combo → "))
        for i, cid in enumerate(labs):
            sec = sects[i] if i < len(sects) else "?"
            self._log(self._fmt_course(cid, prefix=f"lab[{sec}] → "))

    async def process_students(self, command, embed):
        """Batch process #welcome messages and assign roles based on Canvas IDs."""

        # ---------- Guards ----------
        if self.current_semester is None:
            embed.title = "Not Initialized"
            embed.description = (
                "No active semester is set.\n"
                "• Make sure the bot finished starting (check console for READY).\n"
                "• Verify on_ready() calls initialize_guilds().\n"
                "• Check Semester.is_current_semester() so at least one guild is considered current."
            )
            return False

        student_role_obj = self.get_role_obj(command.guild, self.student_role_str)
        if self.current_semester.welcome_channel_obj is None or \
           self.current_semester.log_channel_obj is None or \
           student_role_obj is None:

            desc = ""
            if self.current_semester.welcome_channel_obj is None:
                desc += f"(!) Welcome channel not set. Please create a channel named #{self.welcome_channel_str}\n"
            if self.current_semester.log_channel_obj is None:
                desc += f"(!) Log channel not set. Please create a channel named #{self.log_channel_str}\n"
            if student_role_obj is None:
                desc += f"(!) Role '{self.student_role_str}' not found. Please create this role.\n"

            embed.title = "Error"
            embed.description = desc + "\n** RESTART BOT **"
            return False

        # ---------- Build lookup from Canvas ----------
        student_key_candidates = ("integration_id", "sis_user_id", "login_id", "email")
        student_name_key = "name"

        student_dict = {}   # normalized_id -> record

        def _norm(v):
            if v is None:
                return None
            return " ".join(str(v).strip().lower().split())

        # Log which courses we're about to hit
        self._log("[Canvas] Building student lookup dict…")
        self._log(f"[Canvas] combo_ids={getattr(self.current_semester,'combo_ids',[])}")
        self._log(f"[Canvas] lab_ids={getattr(self.current_semester,'lab_ids',[])}")

        # main (combo) courses
        for course_id in self.current_semester.combo_ids:
            self._log(self._fmt_course(course_id, prefix="GET combo → "))
            students = self.canvas.retrieve_students(course_id)[0]
            self._log(f"[Canvas]   returned {len(students)} student(s)")
            for s in students:
                rec = {
                    "name": s.get(student_name_key),
                    "combo_id": course_id,
                    "lab_id": None,
                    "lab_section": None,
                    "lab_role": None
                }
                for k in student_key_candidates:
                    key_val = _norm(s.get(k))
                    if key_val:
                        student_dict[key_val] = rec

        # lab courses
        for idx, course_id in enumerate(self.current_semester.lab_ids):
            self._log(self._fmt_course(course_id, prefix="GET lab   → "))
            students = self.canvas.retrieve_students(course_id)[0]
            self._log(f"[Canvas]   returned {len(students)} student(s)")
            lab_section = self.current_semester.lab_sections[idx]

            for s in students:
                # find existing rec by any id
                rec = None
                for k in student_key_candidates:
                    key_val = _norm(s.get(k))
                    if key_val and key_val in student_dict:
                        rec = student_dict[key_val]
                        break

                if rec is None:
                    rec = {
                        "name": s.get(student_name_key),
                        "combo_id": None,
                        "lab_id": None,
                        "lab_section": None,
                        "lab_role": None
                    }
                    for k in student_key_candidates:
                        key_val = _norm(s.get(k))
                        if key_val:
                            student_dict[key_val] = rec

                rec["lab_id"] = course_id
                rec["lab_section"] = lab_section
                rec["lab_role"] = self.get_role_obj(command.guild, f"Lab {lab_section}")

        # ---------- Process recent messages in #welcome ----------
        processed = 0
        not_found = 0

        self._log("[Welcome] Scanning last 500 messages (oldest first)…")
        async for msg in self.current_semester.welcome_channel_obj.history(limit=500, oldest_first=True):
            if msg.author.id == self.client.user.id:
                continue

            member = await msg.guild.fetch_member(msg.author.id)

            if student_role_obj in member.roles:
                continue

            content_key = _norm(msg.content)
            if not content_key:
                continue

            student_data = student_dict.get(content_key)

            if student_data:
                name = student_data.get("name")
                lab_section = student_data.get("lab_section")
                lab_role = student_data.get("lab_role")

                try:
                    if name:
                        await member.edit(nick=name)
                except Exception:
                    pass

                await member.add_roles(student_role_obj)
                if lab_role is not None:
                    await member.add_roles(lab_role)

                log_emb = self.embed.initialize_embed("Student processed", "", self.dft_color)
                self.embed.added_member(log_emb, msg.author, name or "(no name)", msg.content, lab_section)
                await self.current_semester.log_channel_obj.send(embed=log_emb)
                self._log(f"[Welcome] OK → {member}  ids matched: '{msg.content}'  lab={lab_section}")
                processed += 1
            else:
                not_found += 1
                nf = self.embed.initialize_embed("Student not found", "", self.dft_color)
                self.embed.member_not_found(nf, msg.author, msg.content)
                await self.current_semester.welcome_channel_obj.send(
                    content=f"{msg.author.mention}", embed=nf
                )
                self._log(f"[Welcome] MISS → {msg.author}  text='{msg.content}'")

        embed.title = "Finished Processing Students"
        embed.description = (
            f"Processed {processed} students. Not found: {not_found}. "
            f"(Indexed {len(student_dict)} Canvas IDs across integration/sis/login/email.)"
        )
        self._log(f"[Summary] processed={processed} not_found={not_found} indexed={len(student_dict)}")
        return True

    async def prune(self, msg, embed):
        # leave inactive servers
        pass

    '''
    PRIVATE FUNCTIONS
    '''
    def __init__(self, name, client, prefix, dft_color, TOKEN):
        # initialize important stuff
        self.client = client
        self.name = name
        self.dft_color = dft_color
        self.prefix = prefix
        self.token = TOKEN

        # initialize additional file variables
        self.admin_list = cfg.admin_list
        self.owner = cfg.owner
        self.student_role_str = cfg.student_role
        self.welcome_channel_str = cfg.welcome_channel
        self.log_channel_str = cfg.log_channel
        self.debug = getattr(cfg, "debug", True)  # turn off to silence logs

        # initialize general variables
        self.current_semester = None
        self.course_names = {}

        # establish other classes
        self.embed = Embed()
        self.canvas = Canvas()

        # initialize all available commands for users to call
        self.commands = {
             self.prefix + "clear_welcome": (
                self.clear_welcome,
                "Wipe all messages in the welcome channel",
                True,   # admin only
            ),
            self.prefix + "help": (
                self.help,
                "List of commands",
                False,
            ),
            self.prefix + "process_students": (
                self.process_students,
                "Process students (scan #welcome, match integration_id/sis_user_id/login_id/email, assign roles)",
                True,
            ),
            self.prefix + "canvas_info": (
                self.canvas_info,
                "Show current guild/semester and Canvas course IDs/names",
                True,
            ),
            self.prefix + "prune": (
                self.prune,
                "Leave servers without [SEASON] [YEAR] - NOT IMPLEMENTED",
                True
            ),
            self.prefix + "invite": (
                self.invite,
                "Invite the bot to another server",
                True
            )
        }

    def _is_ta(self, author):
        return getattr(self, "ta_list", []) and author.id in self.ta_list

    def _is_admin(self, author):
        # Treat the owner as admin as well
        return author.id == self.owner or author.id in self.admin_list

    # --------- helpers ---------
    def _log(self, *args):
        if self.debug:
            print(*args)

    def _fmt_course(self, course_id, prefix="", as_text=False):
        """Pretty-print a course id + name using cached course_names."""
        try:
            cid = int(course_id)
        except Exception:
            cid = course_id
        name = self.course_names.get(cid, None)
        s = f"{prefix}course_id={cid}"
        if name:
            s += f"  name='{name}'"
        return s if as_text else s
























    # ========= LIVE LISTENER SUPPORT =========
    async def _build_student_lookup(self):
        """Build (or reuse) a normalized id -> student record dict from Canvas."""
        # Use a simple cache to avoid hammering Canvas on every message
        if getattr(self, "_student_lookup", None) is not None:
            return self._student_lookup

        def _norm(v):
            if v is None:
                return None
            return " ".join(str(v).strip().lower().split())

        student_key_candidates = ("integration_id", "sis_user_id", "login_id", "email")
        student_name_key = "name"

        lookup = {}

        # main (combo) courses
        for course_id in getattr(self.current_semester, "combo_ids", []):
            students = self.canvas.retrieve_students(course_id)[0]
            for s in students:
                rec = {
                    "name": s.get(student_name_key),
                    "combo_id": course_id,
                    "lab_id": None,
                    "lab_section": None,
                    "lab_role": None
                }
                for k in student_key_candidates:
                    key_val = _norm(s.get(k))
                    if key_val:
                        lookup[key_val] = rec

        # lab courses
        for idx, course_id in enumerate(getattr(self.current_semester, "lab_ids", [])):
            students = self.canvas.retrieve_students(course_id)[0]
            lab_section = self.current_semester.lab_sections[idx]
            for s in students:
                # attach to existing rec if found by any id; else create
                rec = None
                for k in student_key_candidates:
                    key_val = _norm(s.get(k))
                    if key_val and key_val in lookup:
                        rec = lookup[key_val]
                        break
                if rec is None:
                    rec = {"name": s.get(student_name_key), "combo_id": None,
                           "lab_id": None, "lab_section": None, "lab_role": None}
                    for k in student_key_candidates:
                        key_val = _norm(s.get(k))
                        if key_val:
                            lookup[key_val] = rec

                rec["lab_id"] = course_id
                rec["lab_section"] = lab_section
                rec["lab_role"] = self.get_role_obj(self.current_semester.guild, f"Lab {lab_section}")

        self._student_lookup = lookup
        return lookup

    async def process_single_welcome_message(self, message: discord.Message) -> bool:
        """
        Handle exactly one message in #welcome. Returns True if we handled it
        (matched or replied 'not found'); False lets other handlers run.
        """
        # sanity checks
        if self.current_semester is None:
            return False
        if self.current_semester.welcome_channel_obj is None \
           or message.channel.id != self.current_semester.welcome_channel_obj.id:
            return False

        # ignore the bot itself
        if message.author.id == self.client.user.id:
            return True

        # require member perms (for role assignment / nickname)
        student_role = self.get_role_obj(message.guild, self.student_role_str)
        if student_role is None:
            await message.channel.send(f"(!) Role '{self.student_role_str}' not found. Please create it.")
            return True

        member = await message.guild.fetch_member(message.author.id)
        if student_role in member.roles:
            return True  # already processed

        content = (message.content or "").strip()
        if not content:
            return True

        # normalize and look up
        key = " ".join(content.lower().split())
        lookup = await self._build_student_lookup()
        student = lookup.get(key)

        if not student:
            # polite 'not found' ping + log to help students correct typos
            nf = self.embed.initialize_embed("Student not found", "", self.dft_color)
            self.embed.member_not_found(nf, message.author, content)
            await self.current_semester.welcome_channel_obj.send(
                content=f"{message.author.mention}", embed=nf
            )
            return True

        name = student.get("name")
        lab_role = student.get("lab_role")
        lab_section = student.get("lab_section")

        # nickname (ignore failures due to hierarchy)
        try:
            if name:
                await member.edit(nick=name)
        except Exception:
            pass

        # give roles
        await member.add_roles(student_role)
        if lab_role is not None:
            await member.add_roles(lab_role)

        # log success
        ok = self.embed.initialize_embed("Student processed", "", self.dft_color)
        self.embed.added_member(ok, message.author, name or "(no name)", content, lab_section)
        await self.current_semester.log_channel_obj.send(embed=ok)
        return True

    def invalidate_roster_cache(self):
        """Optional: call this if you need to force a Canvas refresh."""
        self._student_lookup = None


    async def clear_welcome(self, msg, embed):
        """Admin: bulk delete messages in the welcome channel."""
        if self.current_semester is None or self.current_semester.welcome_channel_obj is None:
            embed.title = "Error"
            embed.description = "Welcome channel not set. Did you run initialize_guilds()?"
            return False

        channel = self.current_semester.welcome_channel_obj
        count = 0

        try:
            async for m in channel.history(limit=None):
                if m.author.id == self.client.user.id or m.author.bot or m.content:
                    await m.delete()
                    count += 1
        except Exception as e:
            embed.title = "Error"
            embed.description = f"Failed to wipe: {e}"
            return False

        embed.title = "Welcome Channel Wiped"
        embed.description = f"Deleted {count} messages from #{channel.name}."
        return True
