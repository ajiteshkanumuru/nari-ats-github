"""
Format-specific resume extractors.
Each extractor handles a specific format and produces the unified ExtractedResume schema.
This is a key component of the "Format-Aware" nature of the NARI Framework.
"""

import os
import json
from typing import Optional, Dict, Any
from pathlib import Path
import PyPDF2
import pytesseract
from PIL import Image
from bs4 import BeautifulSoup
from docx import Document
# Try to import pytesseract, but make it optional for MVP
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

# Try to import PIL, but make it optional
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from bs4 import BeautifulSoup
from docx import Document
import os
import json
from typing import Optional, Dict, Any
from pathlib import Path

# Required imports for core functionality
import PyPDF2
from bs4 import BeautifulSoup
from docx import Document

# Optional imports for OCR and image processing (graceful degradation)
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    pytesseract = None

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

from src.models.schemas import ExtractedResume, SkillEntry


class BaseExtractor:
    """
    Base class for all extractors. Provides common utilities for text extraction.
    """
    def __init__(self, groq_client=None):
        self.groq_client = groq_client

    def extract_name(self, text: str) -> Optional[str]:
        """Extract candidate name using LLM."""
        if not self.groq_client:
            return None
        prompt = f"Extract only the full name of the candidate from the following resume text. If no name is found, return exactly 'UNKNOWN'. Do not include any other text.\n\nResume text:\n{text[:1500]}"
        try:
            response = self.groq_client.invoke(prompt).content.strip()
            if response.upper() in ["UNKNOWN", "UNKNOWN.", ""]:
                return None
            return response
        except Exception as e:
            error_msg = str(e)
            if any(x in error_msg.lower() for x in ["429", "rate limit", "400", "decommissioned"]):
                raise e
            print(f"Error extracting name using LLM: {error_msg}")
            return None


    def _extract_structured_data(self, text: str) -> dict:
        """Use LLM to extract highly structured list entities like experience, education, projects, and skills."""
        if not self.groq_client:
            return {"skills": [], "experience": [], "education": [], "projects": []}
            
        prompt = f"""
You are an expert HR data parser. Extract the following from the resume text into a strict JSON format.
Only output valid JSON. Do not include markdown formatting or explanations.

FORMAT:
{{
  "professional_summary": "1-2 sentence summary",
  "achievements": "List of key honors, awards, or standout accomplishments",
  "experience": [
    {{"job_title": "Title", "company": "Company", "duration_start": "YYYY-MM", "duration_end": "YYYY-MM or Present", "duration_years": 2.5, "description": "Role description", "key_achievements": ["Achievement 1"]}}
  ],
  "education": [
    {{"degree": "Degree", "institution": "School", "field_of_study": "Field", "graduation_year": "YYYY", "gpa": "X.X", "relevant_coursework": ["Course"]}}
  ],
  "projects": [
    {{"project_name": "Name", "description": "Desc", "technologies": ["Tech"], "url": "URL", "date": "Date"}}
  ],
  "skills": [
    {{"skill_name": "Skill", "proficiency_level": "Level", "years_of_experience": 1.0, "context": "Context"}}
  ]
}}

RESUME TEXT:
{text[:4000]}
"""
        import json
        try:
            response = self.groq_client.invoke(prompt).content.strip()
            # Clean up potential markdown formatting
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
                
            return json.loads(response.strip())
        except Exception as e:
            error_msg = str(e)
            if any(x in error_msg.lower() for x in ["429", "rate limit", "400", "decommissioned"]):
                raise e
            print(f"Error extracting structured data using LLM: {error_msg}")
            return {"skills": [], "experience": [], "education": [], "projects": []}

    def extract_email(self, text: str) -> Optional[str]:
        """Extract the first email address from text."""
        import re
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else None

    def extract_phone(self, text: str) -> Optional[str]:
        """Extract the first phone number from text."""
        import re
        phone_pattern = r'(\+?1[-.]?)?(\(?\d{3}\)?[-.]?)?\d{3}[-.]?\d{4}'
        matches = re.findall(phone_pattern, text)
        return matches[0][0] if matches else None

    def sanitize_text(self, text: str) -> str:
        """Sanitize and normalize extracted text."""
        # ...existing code...
        pass
        """Clean up extracted text."""
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text


class PDFExtractor(BaseExtractor):
    """Extracts text from PDF files with OCR support."""
    
    def extract(self, file_path: str) -> ExtractedResume:
        """Extract resume from PDF file."""
        try:
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                full_text = ""
                
                # First, try text extraction
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    full_text += page.extract_text() + "\n"
                
                # If extraction is poor, try OCR
                if len(full_text.strip()) < 100:
                    full_text = self._ocr_pdf(file_path)
                
                return self._parse_extracted_text(full_text, "PDF")
        except Exception as e:
            raise Exception(f"Error extracting PDF: {str(e)}")
    
    def _ocr_pdf(self, file_path: str) -> str:
        """OCR-based extraction for scanned PDFs."""
        if not PYTESSERACT_AVAILABLE:
            return "[OCR not available - Tesseract not installed]"
        
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(file_path)
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image) + "\n"
            return text
        except Exception as e:
            return f"[OCR failed - {str(e)[:50]}]"
    
    def _parse_extracted_text(self, text: str, format_type: str) -> ExtractedResume:
        """Common parsing logic."""
        text = self.sanitize_text(text)
        
        data = self._extract_structured_data(text)
        from src.models.schemas import ExperienceEntry, EducationEntry, ProjectEntry, SkillEntry
        
        return ExtractedResume(
            format=format_type,
            full_text=text,
            candidate_name=self.extract_name(text),
            candidate_email=self.extract_email(text),
            candidate_phone=self.extract_phone(text),
            professional_summary=data.get('professional_summary'),
            achievements=data.get('achievements'),
            skills=[SkillEntry(**s) for s in data.get('skills', [])],
            experience=[ExperienceEntry(**e) for e in data.get('experience', [])],
            education=[EducationEntry(**ed) for ed in data.get('education', [])],
            projects=[ProjectEntry(**p) for p in data.get('projects', [])],
            metadata={"raw_extraction": True}
        )
    
    def _extract_skills_basic(self, text: str) -> list:
        """Basic skill extraction using keywords."""
        common_skills = [
            "Python", "JavaScript", "Java", "C++", "TypeScript",
            "React", "Vue", "Angular", "Node.js", "Django", "Flask",
            "SQL", "MongoDB", "PostgreSQL", "AWS", "Azure", "GCP",
            "Git", "Docker", "Kubernetes", "Machine Learning", "Data Science",
            "Agile", "Scrum", "Leadership", "Communication", "Problem Solving"
        ]
        found_skills = []
        text_lower = text.lower()
        for skill in common_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        return found_skills


class DOCXExtractor(BaseExtractor):
    """Extracts text from DOCX files."""
    
    def extract(self, file_path: str) -> ExtractedResume:
        """Extract resume from DOCX file."""
        try:
            doc = Document(file_path)
            full_text = "\n".join([para.text for para in doc.paragraphs])
            
            # Also extract from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        full_text += "\n" + cell.text
            
            return self._parse_extracted_text(full_text, "DOCX")
        except Exception as e:
            raise Exception(f"Error extracting DOCX: {str(e)}")
    
    def _parse_extracted_text(self, text: str, format_type: str) -> ExtractedResume:
        """Parse extracted text."""
        text = self.sanitize_text(text)
        
        data = self._extract_structured_data(text)
        from src.models.schemas import ExperienceEntry, EducationEntry, ProjectEntry, SkillEntry
        
        return ExtractedResume(
            format=format_type,
            full_text=text,
            candidate_name=self.extract_name(text),
            candidate_email=self.extract_email(text),
            candidate_phone=self.extract_phone(text),
            professional_summary=data.get('professional_summary'),
            achievements=data.get('achievements'),
            skills=[SkillEntry(**s) for s in data.get('skills', [])],
            experience=[ExperienceEntry(**e) for e in data.get('experience', [])],
            education=[EducationEntry(**ed) for ed in data.get('education', [])],
            projects=[ProjectEntry(**p) for p in data.get('projects', [])],
            metadata={"structure_preserved": True}
        )
    
    def _extract_skills_basic(self, text: str) -> list:
        """Basic skill extraction."""
        common_skills = [
            "Python", "JavaScript", "Java", "C++", "TypeScript",
            "React", "Vue", "Angular", "Node.js", "Django", "Flask",
            "SQL", "MongoDB", "PostgreSQL", "AWS", "Azure", "GCP",
            "Git", "Docker", "Kubernetes", "Machine Learning", "Data Science",
            "Agile", "Scrum", "Leadership", "Communication", "Problem Solving"
        ]
        found_skills = []
        text_lower = text.lower()
        for skill in common_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        return found_skills


class HTMLExtractor(BaseExtractor):
    """Extracts text from HTML files."""
    
    def extract(self, file_path: str) -> ExtractedResume:
        """Extract resume from HTML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as html_file:
                soup = BeautifulSoup(html_file, 'html.parser')
                # Remove script and style tags
                for script in soup(["script", "style"]):
                    script.decompose()
                text = soup.get_text(separator="\n")
                return self._parse_extracted_text(text, "HTML")
        except Exception as e:
            raise Exception(f"Error extracting HTML: {str(e)}")
    
    def _parse_extracted_text(self, text: str, format_type: str) -> ExtractedResume:
        text = self.sanitize_text(text)
        
        data = self._extract_structured_data(text)
        from src.models.schemas import ExperienceEntry, EducationEntry, ProjectEntry, SkillEntry
        
        return ExtractedResume(
            format=format_type,
            full_text=text,
            candidate_name=self.extract_name(text),
            candidate_email=self.extract_email(text),
            candidate_phone=self.extract_phone(text),
            professional_summary=data.get('professional_summary'),
            achievements=data.get('achievements'),
            skills=[SkillEntry(**s) for s in data.get('skills', [])],
            experience=[ExperienceEntry(**e) for e in data.get('experience', [])],
            education=[EducationEntry(**ed) for ed in data.get('education', [])],
            projects=[ProjectEntry(**p) for p in data.get('projects', [])],
            metadata={"web_format": True}
        )
    
    def _extract_skills_basic(self, text: str) -> list:
        common_skills = [
            "Python", "JavaScript", "Java", "C++", "TypeScript",
            "React", "Vue", "Angular", "Node.js", "Django", "Flask",
            "SQL", "MongoDB", "PostgreSQL", "AWS", "Azure", "GCP",
            "Git", "Docker", "Kubernetes", "Machine Learning", "Data Science",
            "Agile", "Scrum", "Leadership", "Communication", "Problem Solving"
        ]
        found_skills = []
        text_lower = text.lower()
        for skill in common_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        return found_skills


class TextExtractor(BaseExtractor):
    """Extracts from plain text files."""
    
    def extract(self, file_path: str) -> ExtractedResume:
        """Extract resume from text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as text_file:
                full_text = text_file.read()
            return self._parse_extracted_text(full_text, "TEXT")
        except Exception as e:
            raise Exception(f"Error extracting TEXT: {str(e)}")
    
    def _parse_extracted_text(self, text: str, format_type: str) -> ExtractedResume:
        text = self.sanitize_text(text)
        
        data = self._extract_structured_data(text)
        from src.models.schemas import ExperienceEntry, EducationEntry, ProjectEntry, SkillEntry
        
        return ExtractedResume(
            format=format_type,
            full_text=text,
            candidate_name=self.extract_name(text),
            candidate_email=self.extract_email(text),
            candidate_phone=self.extract_phone(text),
            professional_summary=data.get('professional_summary'),
            achievements=data.get('achievements'),
            skills=[SkillEntry(**s) for s in data.get('skills', [])],
            experience=[ExperienceEntry(**e) for e in data.get('experience', [])],
            education=[EducationEntry(**ed) for ed in data.get('education', [])],
            projects=[ProjectEntry(**p) for p in data.get('projects', [])],
            metadata={"plain_text": True}
        )
    
    def _extract_skills_basic(self, text: str) -> list:
        common_skills = [
            "Python", "JavaScript", "Java", "C++", "TypeScript",
            "React", "Vue", "Angular", "Node.js", "Django", "Flask",
            "SQL", "MongoDB", "PostgreSQL", "AWS", "Azure", "GCP",
            "Git", "Docker", "Kubernetes", "Machine Learning", "Data Science",
            "Agile", "Scrum", "Leadership", "Communication", "Problem Solving"
        ]
        found_skills = []
        text_lower = text.lower()
        for skill in common_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        return found_skills


class ImageExtractor(BaseExtractor):
    """Extracts resume from image files using OCR."""
    
    def extract(self, file_path: str) -> ExtractedResume:
        """Extract resume from image file."""
        try:
            if not PYTESSERACT_AVAILABLE:
                text = "[Image extraction not available - Tesseract not installed]"
                return self._parse_extracted_text(text, "IMAGE")
            
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return self._parse_extracted_text(text, "IMAGE")
        except Exception as e:
            raise Exception(f"Error extracting IMAGE: {str(e)}")
    
    def _parse_extracted_text(self, text: str, format_type: str) -> ExtractedResume:
        text = self.sanitize_text(text)
        
        return ExtractedResume(
            format=format_type,
            full_text=text,
            candidate_email=self.extract_email(text),
            candidate_phone=self.extract_phone(text),
            skills=[SkillEntry(skill_name=s) for s in self._extract_skills_basic(text)],
            extraction_confidence=0.75,  # Lower confidence for OCR
            metadata={"ocr_based": True}
        )
    
    def _extract_skills_basic(self, text: str) -> list:
        common_skills = [
            "Python", "JavaScript", "Java", "C++", "TypeScript",
            "React", "Vue", "Angular", "Node.js", "Django", "Flask",
            "SQL", "MongoDB", "PostgreSQL", "AWS", "Azure", "GCP",
            "Git", "Docker", "Kubernetes", "Machine Learning", "Data Science",
            "Agile", "Scrum", "Leadership", "Communication", "Problem Solving"
        ]
        found_skills = []
        text_lower = text.lower()
        for skill in common_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        return found_skills


class UniversalExtractor:
    """
    Universal extractor that routes to the appropriate format-specific extractor.
    This implements the "Format-Aware" principle of the NARI Framework.
    """
    
    def __init__(self, groq_client=None):
        self.groq_client = groq_client
        self.extractors = {
            '.pdf': PDFExtractor(groq_client),
            '.docx': DOCXExtractor(groq_client),
            '.doc': DOCXExtractor(groq_client),
            '.html': HTMLExtractor(groq_client),
            '.htm': HTMLExtractor(groq_client),
            '.txt': TextExtractor(groq_client),
            '.png': ImageExtractor(groq_client),
            '.jpg': ImageExtractor(groq_client),
            '.jpeg': ImageExtractor(groq_client),
        }
    
    def extract(self, file_path: str) -> ExtractedResume:
        """Route extraction based on file extension."""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext not in self.extractors:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        extractor = self.extractors[file_ext]
        return extractor.extract(file_path)
