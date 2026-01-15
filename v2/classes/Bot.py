from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import discord
import config as cfg

from classes.Embed import Embed
from classes.Canvas import Canvas
from classes.Semester import Semester


class Bot:
    """
    Main Bot logic class (commands + semester binding + welcome processing).

    Key behaviors:
      - Supports MULTIPLE active guilds (e.g., CS-126 + CS-122 at the same time).
      - Binds each guild to Canvas courses via Semester.set_courses().
      - Live #welcome handling: when a student posts an identifier, assign roles + nickname.
      - Roster building is cached PER-GUILD and never crashes if lab rosters fail.
    """

    # -------------------- discord helpers --------------------
    def get_channel_obj(self, guild, channel_name: str):
        return discord.utils.get(guild.channels, name=channel_name)

    def get_role_obj(self, guild, role_name: str):
        return discord.utils.get(guild.roles, name=role_name)

    # -------------------- small utils --------------------
    @staticmethod
    def _norm(v: Any) -> Optional[str]:
        if v is None:
            return None
        return " ".join(str(v).strip().lower().split())

    def _log(self, s: str) -> None:
        if getattr(self, "debug", True):
            print(s)

    # -------------------- command router --------------------
    async def handle_msg(self, msg: discord.Message):
        author_id = msg.author.id

        argv = (msg.content or "").split()
        command = argv[0].lower() if argv else ""

        embed = self.embed.initialize_embed("Title", "Desc", self.dft_color)
        embed.timestamp = datetime.now()

        if command in self.commands.keys():
            selected_option = self.commands.get(command)

            is_owner = (author_id == self.owner)
            is_admin = self._is_admin(msg.author)
            if selected_option[2] and not (is_owner or is_admin):
                embed.title = "Unauthorized Command"
                embed.description = "Sorry, only authorized users can use this command."
                return embed

            await selected_option[0](msg, embed)
        else:
            embed.title = "Invalid Command"
            embed.description = "Command not recognized."
            embed.set_footer(text=f"(!) Commands can be found with {self.prefix}help")

        return embed

    async def help(self, msg, embed):
        embed.title = f"{self.name} help!"
        is_admin = self._is_admin(msg.author)

        for key, val in self.commands.items():
            if is_admin or not val[2]:
                embed.add_field(name=f"{key} - {val[1]}", value="", inline=False)

    # -------------------- guild/semester binding --------------------
    def _merge_courses(self, a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        out: List[Dict[str, Any]] = []
        for lst in (a or [], b or []):
            for c in lst:
                cid = c.get("id") if isinstance(c, dict) else None
                if cid is None:
                    continue
                try:
                    cid_int = int(cid)
                except Exception:
                    continue
                if cid_int in seen:
                    continue
                seen.add(cid_int)
                out.append(c)
        return out

    def _build_course_name_cache(self, courses: List[Dict[str, Any]]) -> None:
        self.course_names = {}
        for c in courses or []:
            if not isinstance(c, dict):
                continue
            cid = c.get("id")
            nm = c.get("name") or c.get("course_code") or str(cid)
            if cid is None:
                continue
            try:
                self.course_names[int(cid)] = str(nm)
            except Exception:
                pass

    def _fmt_course(self, course_id: int, prefix: str = "", as_text: bool = False) -> str:
        nm = self.course_names.get(int(course_id), str(course_id))
        s = f"{prefix}{course_id} :: {nm}"
        return s if as_text else s

    def _semester_for_message(self, msg: discord.Message) -> Optional[Semester]:
        if msg.guild is None:
            return None
        return self.semesters_by_guild_id.get(int(msg.guild.id))

    async def initialize_guilds(self):
        """
        Binds ALL active guilds to Canvas courses (primary + optional backup) and caches
        course names for logging.
        """
        guilds = list(self.client.guilds or [])
        self.semesters_by_guild_id = {}
        self.current_semester = None  # legacy: first active semester

        if not guilds:
            self._log("[WARN] Bot is in 0 guilds.")
            return

        # --- get Canvas course lists (primary + optional backup) ---
        primary_courses, meta_p = self.canvas.get_my_courses(use_backup=False)
        backup_courses: List[Dict[str, Any]] = []
        meta_b = None

        if self.canvas.backup_token:
            backup_courses, meta_b = self.canvas.get_my_courses(use_backup=True)

        merged_courses = self._merge_courses(primary_courses, backup_courses)
        self._build_course_name_cache(merged_courses)

        self._log(f"[Canvas] primary courses fetched: ok={meta_p.get('ok')} count={meta_p.get('count')}")
        if meta_b is not None:
            self._log(f"[Canvas] backup  courses fetched: ok={meta_b.get('ok')} count={meta_b.get('count')}")
        self._log(f"[Canvas] merged courses cached for lookup: {len(self.course_names)}")

        primary_ids = set(
            int(c["id"]) for c in (primary_courses or []) if isinstance(c, dict) and c.get("id") is not None
        )
        backup_ids = set(
            int(c["id"]) for c in (backup_courses or []) if isinstance(c, dict) and c.get("id") is not None
        )

        # --- bind each active guild ---
        for guild in guilds:
            try:
                sem = Semester(guild)
            except Exception as e:
                self._log(
                    f"[Semester] Failed to parse guild '{getattr(guild,'name',None)}' ({getattr(guild,'id',None)}): {e}"
                )
                continue

            parsed_ok = bool(sem.season and sem.year and sem.classcode)

            if not sem.is_current_semester():
                self._log(f"[Semester] Inactive guild: {guild.name} ({guild.id})")
                if getattr(cfg, "auto_leave_inactive_guilds", False) and parsed_ok:
                    try:
                        await guild.leave()
                        self._log(f"[Semester] Left guild: {guild.name} ({guild.id})")
                    except Exception as e:
                        self._log(f"[Semester] Failed to leave guild {guild.name} ({guild.id}): {e}")
                continue

            welcome_channel_obj = self.get_channel_obj(guild, self.welcome_channel_str)
            log_channel_obj = self.get_channel_obj(guild, self.log_channel_str)

            sem.set_courses(merged_courses)
            sem.set_channels(welcome_channel_obj, log_channel_obj)

            self.semesters_by_guild_id[int(guild.id)] = sem
            if self.current_semester is None:
                self.current_semester = sem

            # ---- binding printout ----
            self._log(f"[Semester] ACTIVE guild: {guild.name} ({guild.id})")
            self._log(f"[Semester] season={sem.season} year={sem.year} term={sem.term} classcode={sem.classcode}")
            self._log(
                f"[Semester] welcome=#{getattr(welcome_channel_obj,'name',None)}  bot_log=#{getattr(log_channel_obj,'name',None)}"
            )

            self._log("[Canvas] ---- guild → canvas binding ----")
            combos = getattr(sem, "combo_ids", []) or []
            labs = getattr(sem, "lab_ids", []) or []
            sects = getattr(sem, "lab_sections", []) or []

            if not combos and not labs:
                self._log("[Canvas] No matching Combo/Lab courses found for this guild.")
                # debug: show a few candidates that contain the classcode
                if sem.classcode and "-" in sem.classcode:
                    dept, num = sem.classcode.split("-", 1)
                    import re as _re
                    cc_re = _re.compile(rf"\b{_re.escape(dept)}\s*-?\s*{_re.escape(num)}\b", _re.IGNORECASE)
                    candidates = []
                    for c in merged_courses or []:
                        text = " ".join(
                            [str(c.get("name", "")), str(c.get("course_code", "")), str(c.get("sis_course_id", ""))]
                        )
                        if cc_re.search(text):
                            candidates.append((int(c.get("id")), c.get("name") or c.get("course_code") or ""))
                    for cid, nm in candidates[:8]:
                        origin = "primary" if cid in primary_ids else ("backup" if cid in backup_ids else "unknown")
                        self._log(f"[Canvas] candidate ({origin}) {cid} :: {nm}")
            else:
                for cid in combos:
                    origin = "primary" if int(cid) in primary_ids else ("backup" if int(cid) in backup_ids else "unknown")
                    self._log(self._fmt_course(int(cid), prefix=f"  main({origin}) → "))
                for i, cid in enumerate(labs):
                    sec = sects[i] if i < len(sects) else "?"
                    origin = "primary" if int(cid) in primary_ids else ("backup" if int(cid) in backup_ids else "unknown")
                    self._log(self._fmt_course(int(cid), prefix=f"  lab[{sec}]({origin}) → "))

            # verify access quickly (non-fatal)
            try:
                for cid in combos[:1]:
                    info = self.canvas.get_course(int(cid))
                    if info and info.get("id"):
                        self._log(f"[Canvas] Verified main course_id={cid} name='{info.get('name')}'")
                for cid in labs[:1]:
                    info = self.canvas.get_course(int(cid))
                    if info and info.get("id"):
                        self._log(f"[Canvas] Verified lab  course_id={cid} name='{info.get('name')}'")
            except Exception as e:
                self._log(f"[Canvas] verification error: {e}")

        self.invalidate_roster_cache()

        if not self.semesters_by_guild_id:
            self._log("[WARN] No ACTIVE guilds detected (Semester.is_current_semester()).")

    # -------------------- admin info commands --------------------
    async def canvas_info(self, msg, embed):
        sem = self._semester_for_message(msg)
        embed.title = "Canvas / Semester Info"

        if sem is None:
            embed.description = (
                "No active semester is bound for this guild.\n"
                "Check the console logs from initialize_guilds() for binding diagnostics."
            )
            return

        embed.add_field(name="Guild", value=f"{sem.guild.name} ({sem.guild.id})", inline=False)

        combos = getattr(sem, "combo_ids", []) or []
        labs = getattr(sem, "lab_ids", []) or []
        sects = getattr(sem, "lab_sections", []) or []

        if combos:
            lines = [self._fmt_course(cid, as_text=True) for cid in combos]
            embed.add_field(name="Main course IDs", value="\n".join(lines), inline=False)
        if labs:
            lines = []
            for i, cid in enumerate(labs):
                sec = sects[i] if i < len(sects) else "?"
                lines.append(self._fmt_course(cid, as_text=True) + f"  (Lab section: {sec})")
            embed.add_field(name="Lab course IDs", value="\n".join(lines), inline=False)

    # -------------------- roster lookup (per guild) --------------------
    async def _build_student_lookup(self, sem: Semester, force: bool = False) -> Dict[str, Dict[str, Any]]:
        gid = int(sem.guild.id)

        ttl = float(getattr(cfg, "roster_cache_ttl_seconds", 6 * 60 * 60))  # 6 hours
        now = datetime.now().timestamp()

        if not force and gid in self._student_lookup_by_guild:
            built_at = self._student_lookup_built_at_by_guild.get(gid, 0.0)
            if (now - built_at) < ttl:
                return self._student_lookup_by_guild[gid]

        student_key_candidates = ("integration_id", "sis_user_id", "login_id", "email")
        student_name_key = "name"

        lookup: Dict[str, Dict[str, Any]] = {}

        combo_ids = getattr(sem, "combo_ids", []) or []
        lab_ids = getattr(sem, "lab_ids", []) or []
        lab_sections = getattr(sem, "lab_sections", []) or []

        # --- main rosters first ---
        for course_id in combo_ids:
            self._log(self._fmt_course(int(course_id), prefix="[Canvas] roster main → "))
            try:
                students, meta = self.canvas.retrieve_students_flat(int(course_id), allow_backup=True, prefer_backup=False)
            except Exception as e:
                self._log(f"[Canvas] ERROR main roster course_id={course_id}: {e}")
                continue

            if not meta.get("ok"):
                self._log(f"[Canvas] main roster FAILED course_id={course_id}: {meta.get('error')}")
                continue

            for s in students:
                rec = {
                    "name": s.get(student_name_key),
                    "main_id": course_id,
                    "lab_id": None,
                    "lab_section": None,
                    "lab_role": None,
                }
                for k in student_key_candidates:
                    key_val = self._norm(s.get(k))
                    if key_val:
                        lookup[key_val] = rec

        # --- labs (never crash if they fail) ---
        for idx, course_id in enumerate(lab_ids):
            sec = lab_sections[idx] if idx < len(lab_sections) else None
            self._log(self._fmt_course(int(course_id), prefix=f"[Canvas] roster lab[{sec or '???'}] → "))

            try:
                students, meta = self.canvas.retrieve_students_flat(
                    int(course_id),
                    allow_backup=True,
                    prefer_backup=bool(self.canvas.backup_token),
                )
            except Exception as e:
                self._log(f"[Canvas] ERROR lab roster course_id={course_id}: {e}")
                continue

            if not meta.get("ok"):
                self._log(f"[Canvas] lab roster FAILED course_id={course_id}: {meta.get('error')}")
                continue

            for s in students:
                rec = None
                for k in student_key_candidates:
                    key_val = self._norm(s.get(k))
                    if key_val and key_val in lookup:
                        rec = lookup[key_val]
                        break

                if rec is None:
                    rec = {
                        "name": s.get(student_name_key),
                        "main_id": None,
                        "lab_id": None,
                        "lab_section": None,
                        "lab_role": None,
                    }
                    for k in student_key_candidates:
                        key_val = self._norm(s.get(k))
                        if key_val:
                            lookup[key_val] = rec

                rec["lab_id"] = course_id
                rec["lab_section"] = sec
                rec["lab_role"] = self.get_role_obj(sem.guild, f"Lab {sec}") if sec else None

        self._student_lookup_by_guild[gid] = lookup
        self._student_lookup_built_at_by_guild[gid] = now
        return lookup

    def invalidate_roster_cache(self, guild_id: Optional[int] = None):
        if guild_id is None:
            self._student_lookup_by_guild = {}
            self._student_lookup_built_at_by_guild = {}
            return
        gid = int(guild_id)
        self._student_lookup_by_guild.pop(gid, None)
        self._student_lookup_built_at_by_guild.pop(gid, None)

    # -------------------- welcome processing --------------------
    async def process_single_welcome_message(self, message: discord.Message) -> bool:
        """
        Live handler for a single message in #welcome.
        Returns True if it handled the message (match or 'not found' response).
        """
        sem = self._semester_for_message(message)
        if sem is None or sem.welcome_channel_obj is None:
            return False

        if message.channel.id != sem.welcome_channel_obj.id:
            return False

        # console proof it is listening in this channel
        self._log(
            f"[Discord] #welcome message guild='{message.guild.name}' channel='#{message.channel.name}' "
            f"author='{message.author}' text='{(message.content or '').strip()}'"
        )

        if message.author.id == self.client.user.id:
            return True

        student_role = self.get_role_obj(message.guild, self.student_role_str)
        if student_role is None:
            try:
                await message.channel.send(f"(!) Role '{self.student_role_str}' not found. Please create it.")
            except Exception:
                pass
            return True

        try:
            member = await message.guild.fetch_member(message.author.id)
        except Exception as e:
            self._log(f"[Welcome] fetch_member failed for author={message.author}: {e}")
            return True

        if student_role in member.roles:
            return True

        content = (message.content or "").strip()
        if not content:
            return True

        key = self._norm(content)
        lookup = await self._build_student_lookup(sem, force=False)
        student = lookup.get(key)

        if not student:
            try:
                nf = self.embed.initialize_embed("Student not found", "", self.dft_color)
                self.embed.member_not_found(nf, message.author, content)
                await sem.welcome_channel_obj.send(content=f"{message.author.mention}", embed=nf)
            except Exception as e:
                self._log(f"[Welcome] member_not_found embed/send failed: {e}")
            self._log(f"[Welcome] MISS guild='{message.guild.name}' author={message.author} text='{content}'")
            return True

        name = student.get("name")
        lab_section = student.get("lab_section")
        lab_role = student.get("lab_role")

        try:
            if name:
                await member.edit(nick=name)
        except Exception:
            pass

        try:
            await member.add_roles(student_role)
        except Exception as e:
            self._log(f"[Welcome] add student role failed: {e}")

        if lab_role is not None:
            try:
                await member.add_roles(lab_role)
            except Exception as e:
                self._log(f"[Welcome] add lab role failed: {e}")

        try:
            ok = self.embed.initialize_embed("Student processed", "", self.dft_color)
            self.embed.added_member(ok, message.author, name or "(no name)", content, lab_section)
            if sem.log_channel_obj is not None:
                await sem.log_channel_obj.send(embed=ok)
        except Exception as e:
            self._log(f"[Welcome] success log send failed: {e}")

        return True

    # -------------------- batch commands --------------------
    async def process_students(self, command, embed):
        sem = self._semester_for_message(command)
        if sem is None:
            embed.title = "Not Initialized"
            embed.description = "No active semester is bound for this guild."
            return False

        student_role_obj = self.get_role_obj(command.guild, self.student_role_str)
        if sem.welcome_channel_obj is None or sem.log_channel_obj is None or student_role_obj is None:
            desc = ""
            if sem.welcome_channel_obj is None:
                desc += f"(!) Welcome channel not set. Please create a channel named #{self.welcome_channel_str}\n"
            if sem.log_channel_obj is None:
                desc += f"(!) Log channel not set. Please create a channel named #{self.log_channel_str}\n"
            if student_role_obj is None:
                desc += f"(!) Role '{self.student_role_str}' not found. Please create this role.\n"
            embed.title = "Error"
            embed.description = desc + "\n** RESTART BOT **"
            return False

        lookup = await self._build_student_lookup(sem, force=True)

        channel = sem.welcome_channel_obj
        processed = 0
        not_found = 0

        async for msg in channel.history(limit=None):
            if msg.author.bot:
                continue
            if not (msg.content or "").strip():
                continue

            try:
                member = await command.guild.fetch_member(msg.author.id)
            except Exception:
                continue

            if student_role_obj in member.roles:
                continue

            key = self._norm(msg.content)
            student = lookup.get(key)

            if not student:
                not_found += 1
                try:
                    nf = self.embed.initialize_embed("Student not found", "", self.dft_color)
                    self.embed.member_not_found(nf, msg.author, msg.content)
                    await sem.welcome_channel_obj.send(content=f"{msg.author.mention}", embed=nf)
                except Exception as e:
                    self._log(f"[Welcome] batch not_found send failed: {e}")
                continue

            name = student.get("name")
            lab_section = student.get("lab_section")
            lab_role = student.get("lab_role")

            try:
                if name:
                    await member.edit(nick=name)
            except Exception:
                pass

            try:
                await member.add_roles(student_role_obj)
            except Exception as e:
                self._log(f"[Welcome] batch add student role failed: {e}")

            if lab_role is not None:
                try:
                    await member.add_roles(lab_role)
                except Exception as e:
                    self._log(f"[Welcome] batch add lab role failed: {e}")

            try:
                log_emb = self.embed.initialize_embed("Student processed", "", self.dft_color)
                self.embed.added_member(log_emb, msg.author, name or "(no name)", msg.content, lab_section)
                await sem.log_channel_obj.send(embed=log_emb)
            except Exception as e:
                self._log(f"[Welcome] batch log send failed: {e}")

            processed += 1

        embed.title = "Finished Processing Students"
        embed.description = f"Processed {processed} students. Not found: {not_found}. Indexed IDs: {len(lookup)}."
        self._log(
            f"[Summary] guild='{command.guild.name}' processed={processed} not_found={not_found} indexed={len(lookup)}"
        )
        return True

    async def clear_welcome(self, msg, embed):
        sem = self._semester_for_message(msg)
        if sem is None or sem.welcome_channel_obj is None:
            embed.title = "Error"
            embed.description = "Welcome channel not set / no active semester for this guild."
            return False

        channel = sem.welcome_channel_obj
        count = 0

        try:
            async for m in channel.history(limit=None):
                if m.author.id == self.client.user.id or m.author.bot or (m.content or "").strip():
                    await m.delete()
                    count += 1
        except Exception as e:
            embed.title = "Error"
            embed.description = f"Failed to wipe: {e}"
            return False

        embed.title = "Welcome Channel Wiped"
        embed.description = f"Deleted {count} messages from #{channel.name}."
        return True

    # -------------------- permissions helpers --------------------
    def _is_admin(self, member) -> bool:
        try:
            if self.owner is not None and int(member.id) == int(self.owner):
                return True
            return int(member.id) in set(self.admin_list or [])
        except Exception:
            return False

    # -------------------- ctor --------------------
    def __init__(self, name, client, prefix, dft_color, TOKEN):
        self.client = client
        self.name = name
        self.dft_color = dft_color
        self.prefix = prefix
        self.token = TOKEN

        self.admin_list = getattr(cfg, "admin_list", [])
        self.owner = getattr(cfg, "owner", None)
        self.student_role_str = getattr(cfg, "student_role", "Students")
        self.welcome_channel_str = getattr(cfg, "welcome_channel", "welcome")
        self.log_channel_str = getattr(cfg, "log_channel", "bot_logs")
        self.debug = getattr(cfg, "debug", True)

        # multi-guild state
        self.semesters_by_guild_id: Dict[int, Semester] = {}
        self.current_semester: Optional[Semester] = None  # legacy: first active

        # roster cache per guild
        self._student_lookup_by_guild: Dict[int, Dict[str, Dict[str, Any]]] = {}
        self._student_lookup_built_at_by_guild: Dict[int, float] = {}

        self.course_names: Dict[int, str] = {}

        self.embed = Embed()
        self.canvas = Canvas()

        # command table (keeps your existing command names)
        self.commands = {
            f"{self.prefix}clear_welcome": (self.clear_welcome, "Wipe all messages in the welcome channel", True),
            f"{self.prefix}help": (self.help, "List of commands", False),
            f"{self.prefix}process_students": (self.process_students, "Process students in #welcome (batch)", True),
            f"{self.prefix}canvas_info": (self.canvas_info, "Show Canvas course bindings for this guild", True),
        }
