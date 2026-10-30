"""Talks to Gemma 4 through the Gemini API and cleans up what it sends back."""

import asyncio
import base64
import json
import os
import re

import httpx

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

EXTRACT_PROMPT = """You are reading a photo or screenshot of a university timetable.
List every class you can see. Reply with ONLY a JSON array, no other text.
Each item must look like this:
{"course": "Data Structures", "code": "CSC2101", "type": "Lecture", "day": "Mon",
 "start": "09:00", "end": "11:00", "room": "B12", "lecturer": "Dr. Okello"}
Rules:
- day is one of Mon, Tue, Wed, Thu, Fri, Sat, Sun.
- start and end use 24-hour HH:MM.
- If a class happens on several days, make one item per day.
- type is Lecture, Lab, Tutorial or Other.
- Use "" for anything you cannot read. Do not invent classes."""

TIPS_PROMPT = """You are a friendly study coach for a university student.
Here is their weekly timetable, the problems found in it, and their free time.
Give 5 to 7 short, practical tips that are specific to THIS timetable:
fix each clash first, then suggest study blocks in the free gaps, breaks on heavy days,
and anything else useful. Mention real days, times and course codes.
Reply with ONLY a JSON array, no other text, like:
[{"title": "Fix the Monday clash", "detail": "CSC2101 and MTH2102 both run 10:00-11:00..."}]

Timetable and analysis:
"""


class GemmaError(Exception):
    pass


def _models():
    main = os.getenv("GEMMA_MODEL", "gemma-4-31b-it")
    backup = "gemma-4-26b-a4b-it" if main != "gemma-4-26b-a4b-it" else "gemma-4-31b-it"
    return [main, backup]


async def _generate(parts):
    keys = [k.strip() for k in (os.getenv("GEMINI_API_KEY"), os.getenv("GEMINI_API_KEY_2")) if k and k.strip()]
    if not keys:
        raise GemmaError("GEMINI_API_KEY is missing. Add it to the .env file and restart the server.")

    body = {
        "contents": [{"role": "user", "parts": parts}],
        # long "thinking" made answers take over 2 minutes; keep it minimal
        "generationConfig": {"thinkingConfig": {"thinkingLevel": "minimal"}},
    }
    async with httpx.AsyncClient(timeout=180) as client:
        # when Google is busy (500/503) or a key hits its free limit (429),
        # try the next key, then the backup model
        for model, key in [(m, k) for m in _models() for k in keys]:
            try:
                res = await client.post(
                    API_URL.format(model=model),
                    headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                    json=body,
                )
            except httpx.TimeoutException:
                raise GemmaError("Gemma took too long to answer. Try again in a moment.")
            except httpx.HTTPError:
                raise GemmaError("Could not reach Gemma. Check your internet connection.")
            if res.status_code not in (429, 500, 503):
                break
            await asyncio.sleep(2)

    data = res.json()
    if res.status_code != 200:
        message = data.get("error", {}).get("message", res.text)
        raise GemmaError(f"Gemma request failed ({res.status_code}): {message}")

    try:
        out_parts = data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError):
        raise GemmaError("Gemma sent back an empty answer. Try again.")

    # skip "thinking" parts, keep only the final answer text
    return "".join(p.get("text", "") for p in out_parts if not p.get("thought"))


def parse_json_array(text):
    """Pull the JSON array out of a model reply, even if it is wrapped in ``` fences."""
    text = re.sub(r"```(?:json)?", "", text)
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end <= start:
        raise GemmaError("Gemma did not reply with a list. Try again.")
    try:
        items = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        raise GemmaError("Gemma's reply was not valid JSON. Try again.")
    return [item for item in items if isinstance(item, dict)]


def normalize_day(value):
    value = str(value).strip().lower()[:3]
    for day in DAYS:
        if day.lower() == value:
            return day
    return ""


def normalize_time(value):
    """Turn '9:00 AM', '9am', '0900', '14.30' into '09:00' / '14:30'. Returns '' if unreadable."""
    text = str(value).strip().lower().replace(".", ":")
    match = re.match(r"^(\d{1,2})(?::?(\d{2}))?\s*(am|pm|a\.m|p\.m)?", text)
    if not match:
        return ""
    hour, minute, ampm = int(match.group(1)), int(match.group(2) or 0), match.group(3)
    if ampm and ampm.startswith("p") and hour < 12:
        hour += 12
    if ampm and ampm.startswith("a") and hour == 12:
        hour = 0
    if hour > 23 or minute > 59:
        return ""
    return f"{hour:02d}:{minute:02d}"


def normalize_class(item):
    kind = str(item.get("type", "")).strip().title()
    return {
        "course": str(item.get("course", "")).strip(),
        "code": str(item.get("code", "")).strip().upper(),
        "type": kind if kind in ("Lecture", "Lab", "Tutorial") else ("Other" if kind else "Lecture"),
        "day": normalize_day(item.get("day", "")),
        "start": normalize_time(item.get("start", "")),
        "end": normalize_time(item.get("end", "")),
        "room": str(item.get("room", "")).strip(),
        "lecturer": str(item.get("lecturer", "")).strip(),
    }


async def extract_classes(image_bytes, mime_type):
    parts = [
        {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}},
        {"text": EXTRACT_PROMPT},
    ]
    reply = await _generate(parts)
    return [normalize_class(item) for item in parse_json_array(reply)]


async def generate_tips(analysis):
    reply = await _generate([{"text": TIPS_PROMPT + json.dumps(analysis, indent=1)}])
    tips = []
    for item in parse_json_array(reply):
        title, detail = str(item.get("title", "")).strip(), str(item.get("detail", "")).strip()
        if title or detail:
            tips.append({"title": title, "detail": detail})
    return tips
