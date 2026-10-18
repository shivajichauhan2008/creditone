"""HTTP API. Run: uvicorn app.main:app --reload (from backend/)."""
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .models import InsightsRequest, ParsedReport
from .parsing import PasswordRequired, UnsupportedBureau, WrongPassword, parse_report
from .rules import compute

MAX_UPLOAD_BYTES = 15 * 1024 * 1024

app = FastAPI(title="Credit Report Insights API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/api/reports/parse", response_model=ParsedReport)
async def parse(file: UploadFile = File(...), password: str | None = Form(None)):
    """Parse an uploaded report in memory. Nothing is written to disk or logged."""
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File too large")
    if not data.startswith(b"%PDF"):
        raise HTTPException(415, "Please upload the PDF report")
    try:
        return parse_report(data, password)
    except PasswordRequired:
        raise HTTPException(401, "This report is password-protected")
    except WrongPassword:
        raise HTTPException(401, "Wrong password")
    except UnsupportedBureau as e:
        raise HTTPException(422, f"Reports from '{e.bureau}' aren't supported yet")
    finally:
        del data


@app.post("/api/insights")
def insights(req: InsightsRequest):
    """Compute the dashboard from a (user-confirmed) parsed report and the user's inputs."""
    return compute(req.report, req.inputs)
