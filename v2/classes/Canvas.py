import requests
import secret as sc
from typing import Any, Dict, List, Optional, Tuple


class Canvas:
    """
    Minimal Canvas API helper with:
    - primary token (API_KEY)
    - optional BACKUP_CAN_API_TOKEN fallback
    - safe pagination
    """

    def __init__(self, base_url: str = "https://canvas.nau.edu/api/v1/") -> None:
        self.base_url = base_url.rstrip("/") + "/"

        # Primary token (existing)
        self.primary_token: Optional[str] = getattr(sc, "API_KEY", None)

        # Backup token (new) – used only if present
        self.backup_token: Optional[str] = getattr(sc, "BACKUP_CAN_API_TOKEN", None)

        self.per_page = 100
        self.timeout = 30
        self.session = requests.Session()

    def _headers(self, token: Optional[str]) -> Dict[str, str]:
        tok = token or self.primary_token
        if not tok:
            return {}
        return {"Authorization": f"Bearer {tok}"}

    def _get(self, url: str, *, token: Optional[str], params: Optional[Dict[str, Any]] = None) -> requests.Response:
        return self.session.get(url, headers=self._headers(token), params=params, timeout=self.timeout)

    def _paginate_json(
        self,
        url: str,
        *,
        token: Optional[str],
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Follow Canvas Link headers; return (items, meta).
        """
        items: List[Any] = []
        meta: Dict[str, Any] = {
            "ok": False,
            "pages": 0,
            "count": 0,
            "http_statuses": [],
            "error": None,
            "used_backup": False,
        }

        next_url = url
        next_params = params

        while next_url:
            try:
                resp = self._get(next_url, token=token, params=next_params)
            except Exception as e:
                meta["error"] = f"request error: {e}"
                break

            meta["pages"] += 1
            meta["http_statuses"].append(resp.status_code)

            if resp.status_code != 200:
                # Keep a bit of text for debugging
                try:
                    meta["error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
                except Exception:
                    meta["error"] = f"HTTP {resp.status_code}"
                break

            try:
                data = resp.json()
            except Exception as e:
                meta["error"] = f"json decode error: {e}"
                break

            if isinstance(data, list):
                items.extend(data)
            else:
                items.append(data)

            # Follow "next" link if present
            nxt = resp.links.get("next", {})
            next_url = nxt.get("url")

            # When using next_url (already includes querystring), don't pass params again
            next_params = None

        meta["ok"] = meta["error"] is None
        meta["count"] = len(items)
        return items, meta

    def get_my_courses(self, *, use_backup: bool = False) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Returns (courses, meta). Safe: returns [] on failure.
        """
        token = self.backup_token if use_backup else self.primary_token
        url = self.base_url + "courses"
        courses, meta = self._paginate_json(url, token=token, params={"per_page": self.per_page})
        meta["used_backup"] = bool(use_backup)
        # Canvas returns list of dicts for courses
        return [c for c in courses if isinstance(c, dict)], meta

    def get_course(self, course_id: int, *, allow_backup: bool = True) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """
        Returns (course_dict_or_None, meta). Tries primary; optionally fallback to backup.
        """
        url = self.base_url + f"courses/{course_id}"

        # 1) primary
        course_items, meta = self._paginate_json(url, token=self.primary_token, params=None)
        course = course_items[0] if course_items and isinstance(course_items[0], dict) else None
        if meta["ok"] and course is not None:
            meta["used_backup"] = False
            return course, meta

        # 2) backup fallback
        if allow_backup and self.backup_token:
            course_items2, meta2 = self._paginate_json(url, token=self.backup_token, params=None)
            course2 = course_items2[0] if course_items2 and isinstance(course_items2[0], dict) else None
            meta2["used_backup"] = True
            return course2, meta2

        meta["used_backup"] = False
        return None, meta

    def retrieve_students_flat(
        self,
        course_id: int,
        *,
        allow_backup: bool = True,
        prefer_backup: bool = False,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Returns (students, meta). Never raises; returns [] + meta on failure.
        Tries primary (or backup if prefer_backup=True), then optionally fallback.
        """
        url = self.base_url + f"courses/{course_id}/students"
        params = {"per_page": self.per_page}

        def run(token: Optional[str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
            raw, meta = self._paginate_json(url, token=token, params=params)
            return [x for x in raw if isinstance(x, dict)], meta

        # choose first token
        first_token = self.backup_token if prefer_backup else self.primary_token
        second_token = self.primary_token if prefer_backup else self.backup_token

        students, meta = run(first_token)
        meta["used_backup"] = bool(prefer_backup)

        if meta["ok"]:
            return students, meta

        if allow_backup and second_token and second_token != first_token:
            students2, meta2 = run(second_token)
            meta2["used_backup"] = not bool(prefer_backup)
            # carry the first error for debugging
            meta2["primary_attempt_error"] = meta.get("error")
            meta2["primary_attempt_statuses"] = meta.get("http_statuses")
            return students2, meta2

        return students, meta
