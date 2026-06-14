"""Календар (секретний iCal-URL, read-only) і пошта (IMAP, read-only)."""
import datetime
import email
import imaplib
from email.header import decode_header

import requests

import config
from db import cache_get, cache_set

_TIMEOUT = 10


def _parse_ical_dt(value: str):
    """Розбирає DTSTART у форматах '20260614T090000Z', '20260614T090000', '20260614'."""
    value = value.strip()
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S", "%Y%m%d"):
        try:
            return datetime.datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def get_calendar(limit=5):
    """Найближчі події з секретного iCal-URL. Без сторонніх бібліотек — простий парсер VEVENT."""
    if not config.ICAL_URL:
        return {"ok": False, "error": "ICAL_URL не заданий"}
    cached = cache_get("calendar", 900)  # 15 хв
    if cached is not None:
        return cached
    try:
        r = requests.get(config.ICAL_URL, timeout=_TIMEOUT)
        r.raise_for_status()
        events = []
        cur = {}
        in_event = False
        for raw in r.text.splitlines():
            line = raw.strip()
            if line == "BEGIN:VEVENT":
                in_event, cur = True, {}
            elif line == "END:VEVENT":
                if cur.get("start"):
                    events.append(cur)
                in_event = False
            elif in_event:
                if line.startswith("SUMMARY"):
                    cur["title"] = line.split(":", 1)[-1]
                elif line.startswith("DTSTART"):
                    cur["start"] = _parse_ical_dt(line.split(":", 1)[-1])

        now = datetime.datetime.now()
        upcoming = sorted(
            (e for e in events if e.get("start") and e["start"] >= now),
            key=lambda e: e["start"],
        )[:limit]
        result = {"ok": True, "events": [
            {"title": e.get("title", "(без назви)"), "when": e["start"].strftime("%d.%m %H:%M")}
            for e in upcoming
        ]}
    except Exception as e:
        result = {"ok": False, "error": str(e)}
    cache_set("calendar", result)
    return result


def _decode(value):
    parts = decode_header(value or "")
    out = ""
    for text, enc in parts:
        out += text.decode(enc or "utf-8", errors="replace") if isinstance(text, bytes) else text
    return out


def get_mail(limit=5):
    """IMAP read-only: кількість непрочитаних + останні теми."""
    if not (config.IMAP_USER and config.IMAP_PASSWORD):
        return {"ok": False, "error": "IMAP не налаштований"}
    cached = cache_get("mail", 300)  # 5 хв
    if cached is not None:
        return cached
    try:
        M = imaplib.IMAP4_SSL(config.IMAP_HOST)
        M.login(config.IMAP_USER, config.IMAP_PASSWORD)
        M.select("INBOX", readonly=True)
        _, unseen = M.search(None, "UNSEEN")
        unseen_ids = unseen[0].split()
        recent = unseen_ids[-limit:][::-1] if unseen_ids else []
        subjects = []
        for mid in recent:
            _, data = M.fetch(mid, "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM)])")
            msg = email.message_from_bytes(data[0][1])
            subjects.append({
                "subject": _decode(msg.get("Subject")),
                "from": _decode(msg.get("From")),
            })
        M.logout()
        result = {"ok": True, "unseen": len(unseen_ids), "messages": subjects}
    except Exception as e:
        result = {"ok": False, "error": str(e)}
    cache_set("mail", result)
    return result
