import re
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any


class Semester:
    """
    Extracts semester metadata from Discord guild name and finds matching Canvas courses.

    Supports guild names like:
      - "CS126 Fall 2025"
      - "CS 126 S2026"  (S=Spring, U=Summer, F=Fall, W=Winter)
    """

    _TERM_CODE = {"spring": "1", "summer": "4", "fall": "7", "winter": "8"}
    _LETTER_TO_SEASON = {"s": "Spring", "u": "Summer", "f": "Fall", "w": "Winter"}

    # -------------------- parsing --------------------
    def get_classcode(self, name: str) -> Optional[str]:
        # "CS126" or "CS 126" -> "CS-126"
        match = re.search(r"\b([A-Z]{2,})\s*-?\s*(\d{3})\b", name, re.IGNORECASE)
        if not match:
            return None
        return f"{match.group(1).upper()}-{match.group(2)}"

    def get_season_year(self, name: str) -> Tuple[Optional[str], Optional[str]]:
        # Format 1: "Fall 2025"
        m1 = re.search(r"\b(Fall|Spring|Summer|Winter)\b.*\b(20\d{2})\b", name, re.IGNORECASE)
        if m1:
            season = m1.group(1).capitalize()
            year = m1.group(2)
            return season, year

        # Format 2: "S2026" / "F2025"
        m2 = re.search(r"\b([FSUW])\s*(20\d{2})\b", name, re.IGNORECASE)
        if m2:
            season_letter = m2.group(1).lower()
            year = m2.group(2)
            season = self._LETTER_TO_SEASON.get(season_letter)
            return season, year

        return None, None

    def calculate_term(self) -> Optional[str]:
        if not self.season or not self.year:
            return None
        szn = self.season.lower()
        code = self._TERM_CODE.get(szn)
        if not code:
            return None
        # your existing scheme: "1" + YY + code  (e.g., Spring 2026 -> 1261)
        return "1" + self.year[2:] + code

    def get_current_semester_string(self) -> str:
        """
        During the late-Dec/early-Jan break, you typically want the upcoming Spring guild
        to be "current". So if we fall into the "Winter" window, we map it to Spring.
        """
        d = datetime.now()

        sp_start, sp_end = datetime(d.year, 1, 13), datetime(d.year, 5, 3)
        su_start, su_end = datetime(d.year, 5, 4), datetime(d.year, 7, 31)
        f_start, f_end = datetime(d.year, 8, 1), datetime(d.year, 12, 27)

        if sp_start <= d <= sp_end:
            return f"Spring {d.year}"
        if su_start <= d <= su_end:
            return f"Summer {d.year}"
        if f_start <= d <= f_end:
            return f"Fall {d.year}"

        # winter window -> treat as upcoming Spring
        if d.month == 12:
            return f"Spring {d.year + 1}"
        return f"Spring {d.year}"

    def is_current_semester(self) -> bool:
        if not self.season or not self.year:
            return False
        return f"{self.season} {self.year}" == self.get_current_semester_string()

    # -------------------- course matching helpers --------------------
    @staticmethod
    def _norm_text(s: Any) -> str:
        s = "" if s is None else str(s)
        s = s.replace("–", "-").replace("—", "-")
        return " ".join(s.strip().lower().split())

    def _course_text(self, course: Dict[str, Any]) -> str:
        # concatenate common Canvas fields for matching
        parts = [
            course.get("name", ""),
            course.get("course_code", ""),
            course.get("sis_course_id", ""),
        ]
        return self._norm_text(" ".join(str(p) for p in parts if p))

    def _classcode_regex(self) -> Optional[re.Pattern]:
        if not self.classcode:
            return None
        try:
            dept, num = self.classcode.split("-", 1)
        except Exception:
            return None
        return re.compile(rf"\b{re.escape(dept)}\s*-?\s*{re.escape(num)}\b", re.IGNORECASE)

    def _labcode_regex(self) -> Optional[re.Pattern]:
        if not self.classcode:
            return None
        try:
            dept, num = self.classcode.split("-", 1)
        except Exception:
            return None
        # CS-126L / CS 126 L / CS126L
        return re.compile(rf"\b{re.escape(dept)}\s*-?\s*{re.escape(num)}\s*l\b", re.IGNORECASE)

    def _matches_term_markers(self, text: str) -> bool:
        # Common naming patterns:
        #  - "... (1261-2535) ..."
        #  - "... (1261 ..."
        #  - "... Spring 2026 ..."
        if not self.term:
            return False
        t = self.term
        season_year = f"{self.season} {self.year}".lower() if (self.season and self.year) else ""
        return (f"({t}" in text) or (f"{t}-" in text) or (season_year and season_year in text)

    @staticmethod
    def _extract_section(name: str) -> str:
        nm = (name or "").strip()
        m = re.search(r"\b(\d{3})\b\s*$", nm)
        if m:
            return m.group(1)
        return nm[-3:] if len(nm) >= 3 else "???"

    # -------------------- public setters --------------------
    def set_channels(self, welcome_channel, log_channel) -> None:
        self.welcome_channel_obj = welcome_channel
        self.log_channel_obj = log_channel

    def set_courses(self, my_courses: List[Dict[str, Any]]) -> None:
        """
        Finds Canvas courses for this guild.

        Primary behavior:
          - main/roster shell:  "Combo {CS-126} ({term}"
          - lab shells:         "{CS-126}L ({term}"

        Fallback behavior:
          - If no "Combo ..." courses exist (like CS-122 shells),
            match ANY course whose (name/course_code/sis_course_id) contains classcode
            and also contains either the term marker (1261 / 1261-...) or "Spring 2026".
          - If that still yields nothing, match ANY course that contains classcode.
        """
        self.my_courses = my_courses or []

        # defaults
        self.combo_ids = []
        self.lab_ids = []
        self.lab_sections = []

        if not self.classcode or not self.term:
            return

        # -------- main shell (combo) --------
        combo_str = f"Combo {self.classcode} ({self.term}"
        combo_ids = self.get_course_ids(combo_str)

        cc_re = self._classcode_regex()
        if not combo_ids and cc_re:
            # 1) classcode + term markers
            for c in self.my_courses:
                cid = c.get("id")
                if cid is None:
                    continue
                text = self._course_text(c)
                if cc_re.search(text) and self._matches_term_markers(text):
                    combo_ids.append(int(cid))

        if not combo_ids and cc_re:
            # 2) classcode only (last-resort)
            for c in self.my_courses:
                cid = c.get("id")
                if cid is None:
                    continue
                text = self._course_text(c)
                if cc_re.search(text):
                    combo_ids.append(int(cid))

        # de-dupe, stable order
        seen = set()
        self.combo_ids = []
        for cid in combo_ids:
            if cid in seen:
                continue
            seen.add(cid)
            self.combo_ids.append(int(cid))

        # -------- lab shells --------
        lab_str = f"{self.classcode}L ({self.term}"
        lab_ids = self.get_course_ids(lab_str)
        lab_sections = self.get_lab_sections(lab_str, self.my_courses)

        lab_re = self._labcode_regex()
        if not lab_ids and lab_re:
            # fallback: any course that looks like CS-126L and matches term markers
            for c in self.my_courses:
                cid = c.get("id")
                if cid is None:
                    continue
                text = self._course_text(c)
                if lab_re.search(text) and self._matches_term_markers(text):
                    lab_ids.append(int(cid))
                    lab_sections.append(self._extract_section(c.get("name") or c.get("course_code") or ""))

        # de-dupe labs
        seen = set()
        self.lab_ids = []
        self.lab_sections = []
        for cid, sec in zip(lab_ids, lab_sections):
            if cid in seen:
                continue
            seen.add(cid)
            self.lab_ids.append(int(cid))
            self.lab_sections.append(sec)

    # -------------------- old helpers kept --------------------
    def get_course_ids(self, course_str: str) -> List[int]:
        ids: List[int] = []
        for course in self.my_courses or []:
            name = course.get("name", "")
            if course_str in name:
                cid = course.get("id")
                if cid is not None:
                    ids.append(int(cid))
        return ids

    def get_lab_sections(self, needle: str, my_courses: List[Dict[str, Any]]) -> List[str]:
        sections: List[str] = []
        for course in my_courses or []:
            name = course.get("name", "")
            if needle in name:
                sections.append(name[-3:])
        return sections

    def __init__(self, guild) -> None:
        self.guild = guild

        self.classcode = self.get_classcode(guild.name)
        self.season, self.year = self.get_season_year(guild.name)
        self.term = self.calculate_term()
        self.active = self.is_current_semester()

        # course ids
        self.my_courses: Optional[List[Dict[str, Any]]] = None
        self.combo_ids: List[int] = []
        self.lab_ids: List[int] = []
        self.lab_sections: List[str] = []

        # discord channels
        self.welcome_channel_obj = None
        self.log_channel_obj = None
