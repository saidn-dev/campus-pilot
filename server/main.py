from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

from server import gemma  # noqa: E402  (needs the .env loaded first)

MAX_IMAGE_BYTES = 15 * 1024 * 1024

app = FastAPI(title="Timetable Assistant")


class TipsRequest(BaseModel):
    analysis: dict


@app.post("/api/extract")
async def extract(image: UploadFile = File(...)):
    if not (image.content_type or "").startswith("image/"):
        raise HTTPException(400, "Please upload an image file (JPG, PNG or WebP).")
    data = await image.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(400, "That image is over 15 MB. Use a smaller photo or a screenshot.")
    try:
        classes = await gemma.extract_classes(data, image.content_type)
    except gemma.GemmaError as err:
        raise HTTPException(502, str(err))
    return {"classes": classes}


@app.post("/api/tips")
async def tips(req: TipsRequest):
    try:
        result = await gemma.generate_tips(req.analysis)
    except gemma.GemmaError as err:
        raise HTTPException(502, str(err))
    return {"tips": result}


app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")
