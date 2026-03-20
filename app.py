import os
import uuid
import shutil
import json
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from dotenv import load_dotenv

from src.models.schemas import JobDescription
from src.orchestration import NARIATSOrchestrator
from src.utils.exporters import DOCXExporter, PDFExporter

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables")

app = FastAPI(title="NARI ATS API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = NARIATSOrchestrator(groq_api_key)

# Temporary directory for file processing
TEMP_DIR = Path("temp_uploads")
TEMP_DIR.mkdir(exist_ok=True)

@app.post("/api/analyze-jd")
async def analyze_jd(
    jd_text: Optional[str] = Form(None),
    jd_file: Optional[UploadFile] = File(None)
):
    """
    Analyze a job description (text or file) and extract key details.
    """
    content = ""
    print(f"DEBUG: analyze-jd called. jd_text length: {len(jd_text) if jd_text else 0}, jd_file: {jd_file.filename if jd_file else 'None'}")
    
    if jd_file and jd_file.filename:
        file_path = TEMP_DIR / jd_file.filename
        try:
            # Ensure we are at the start of the file
            await jd_file.seek(0)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(jd_file.file, buffer)
            
            print(f"DEBUG: File saved to {file_path}. Size: {file_path.stat().st_size}")

            if jd_file.filename.lower().endswith(".json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        json_data = json.load(f)
                        content = json.dumps(json_data, indent=2)
                        print("DEBUG: JSON file parsed successfully.")
                    except json.JSONDecodeError as je:
                        print(f"DEBUG: JSON decode error: {je}. Reading as text.")
                        f.seek(0)
                        content = f.read()
            else:
                from src.extractors.format_extractors import UniversalExtractor
                extractor = UniversalExtractor(orchestrator.groq_client)
                extracted_resume = extractor.extract(str(file_path))
                content = extracted_resume.full_text
                print(f"DEBUG: File extracted using UniversalExtractor. Content length: {len(content)}")
        except Exception as e:
            print(f"DEBUG: Extraction error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to extract text from file: {str(e)}")
        finally:
            if file_path.exists():
                os.remove(file_path)
    else:
        content = jd_text or ""
        print(f"DEBUG: Using jd_text. Content length: {len(content)}")

    if not content or content.strip() == "":
        print("DEBUG: No content found. Raising 400.")
        raise HTTPException(status_code=400, detail="No content provided for analysis.")

    # Use LLM to extract JD details
    prompt = f"""
    Extract the following details from the job description text into a strict JSON format.
    Fields: job_title, company, department, description (summary of key requirements).
    If a field is not found, return an empty string. Only output valid JSON.

    TEXT:
    {content[:4000]}
    """
    
    try:
        response = orchestrator.groq_client.invoke(prompt).content.strip()
        print(f"DEBUG: LLM Raw Response: {response[:100]}...")
        
        # Robust JSON cleaning
        clean_response = response
        if "```json" in clean_response:
            clean_response = clean_response.split("```json")[-1].split("```")[0]
        elif "```" in clean_response:
            clean_response = clean_response.split("```")[-1].split("```")[0]
        
        extracted_data = json.loads(clean_response.strip())
        return extracted_data
    except Exception as e:
        print(f"DEBUG: LLM extraction failed: {str(e)}")
        # Fallback: if JSON fails, return whatever we have from the text
        return {
            "job_title": "",
            "company": "",
            "department": "",
            "description": content[:1000]
        }

@app.post("/api/analyze")
async def analyze_resumes(
    jd_text: str = Form(""),
    resumes: List[UploadFile] = File(...),
    job_title: str = Form(""),
    company: str = Form(""),
    department: str = Form("")
):
    """
    Analyze multiple resumes against a job description.
    """
    print(f"DEBUG: analyze-resumes called. JD: {job_title} at {company}. Resumes count: {len(resumes)}")
    
    job_desc = JobDescription(
        job_title=job_title or "Unknown Title",
        company=company or "Unknown Company",
        description=jd_text or "No description provided",
        department=department or "General"
    )

    results = []
    for resume in resumes:
        resume_path = TEMP_DIR / resume.filename
        with open(resume_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)
        
        try:
            # Run orchestration
            output = await orchestrator.run(str(resume_path), job_desc)
            results.append({
                "filename": resume.filename,
                "status": "success",
                "data": output
            })
        except Exception as e:
            results.append({
                "filename": resume.filename,
                "status": "error",
                "error": str(e)
            })
        finally:
            # Clean up resume file
            if resume_path.exists():
                os.remove(resume_path)

    return {"results": results}

@app.post("/api/export")
async def export_report(
    analysis_data: str = Form(...),
    format: str = Form(...) # "docx" or "pdf"
):
    """
    Export a report in DOCX or PDF format.
    """
    data = json.loads(analysis_data)
    candidate = data.get('candidate_profile', {})
    if not candidate:
        candidate = data.get('data', {}).get('candidate_profile', {})
        
    filename = candidate.get("candidate_name", "Report").replace(" ", "_")
    output_filename = f"{filename}_report.{format}"
    file_id = f"{uuid.uuid4()}_{output_filename}"
    output_path = TEMP_DIR / file_id
    
    try:
        if format.lower() == 'pdf':
            output_path = PDFExporter.export(data, str(output_path))
        elif format.lower() == 'docx':
            output_path = DOCXExporter.export(data, str(output_path))
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
            
        return {"file_id": file_id, "filename": output_filename}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/api/download/{file_id}")
async def download_report(file_id: str):
    file_path = TEMP_DIR / file_id
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found or expired")
        
    original_filename = file_id.split("_", 1)[1] if "_" in file_id else file_id
    media_type = "application/pdf" if file_path.suffix == '.pdf' else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    return FileResponse(
        path=file_path,
        filename=original_filename,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{original_filename}"'}
    )

if __name__ == "__main__":
    import uvicorn
    # Start the server on port 8000
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
