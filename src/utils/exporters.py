import json
from pathlib import Path
from typing import Dict, Any

from fpdf import FPDF
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

class PDFReport(FPDF):
    def header(self):
        # Arial bold 15
        self.set_font('Helvetica', 'B', 15)
        # Title
        self.cell(0, 10, 'NARI ATS Candidate Evaluation Report', border=0, ln=1, align='C')
        # Line break
        self.ln(5)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Helvetica', 'I', 8)
        # Page number
        self.cell(0, 10, f'Page {self.page_no()}', border=0, align='C')


class PDFExporter:
    """Exports ATS JSON output to a beautifully formatted PDF report."""
    
    @staticmethod
    def export(output_data: Dict[str, Any], output_path: str) -> str:
        pdf = PDFReport()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        def sanitize(text):
            text = str(text).replace('**', '')
            text = text.replace('\u2022', '-').replace('\u2013', '-').replace('\u2014', '--')
            text = text.replace('\u2018', "'").replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
            return text.encode('latin-1', 'replace').decode('latin-1')

        def m_cell(h, txt):
            pdf.multi_cell(0, h, sanitize(txt))
            pdf.set_x(15)

        def add_section_title(title):
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 10, sanitize(title), border=0, ln=1, align='L', fill=True)
            pdf.ln(2)
            
        def add_field(label, value):
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(50, 8, sanitize(label) + ":", border=0)
            pdf.set_font('Helvetica', '', 10)
            val_str = sanitize(value)
            if len(val_str) > 70:
                pdf.multi_cell(0, 8, val_str)
                pdf.set_x(15)
            else:
                pdf.cell(0, 8, val_str, border=0, ln=1)

        candidate = output_data.get('candidate_profile', {})
        name = candidate.get('candidate_name') or "Unknown Candidate"
        email = candidate.get('candidate_email') or "N/A"
        
        # 1. Candidate Info
        add_section_title("Candidate Profile")
        add_field("Name", name)
        add_field("Email", email)
        add_field("Applied For (Job)", output_data.get('job_title', 'Unknown'))
        add_field("Processed On", output_data.get('timestamp', 'Unknown').split('T')[0])
        pdf.ln(2)
        
        # 2. Results Summary (Moved up as requested)
        add_section_title("RESULT SUMMARY")
        add_field("Overall Match Score", f"{output_data.get('overall_match_score', 0)} / 10.0")
        add_field("Confidence", f"{int(output_data.get('confidence_level', 0) * 100)}%")
        add_field("Recommendation", str(output_data.get('hiring_recommendation', 'N/A')).upper())
        
        bias_data = output_data.get('bias_analysis', {})
        add_field("Bias Risk Level", str(bias_data.get('risk_level', 'N/A')).upper())
        pdf.ln(2)
        
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 8, "Primary Reasoning:", border=0, ln=1)
        pdf.set_font('Helvetica', '', 10)
        
        reasoning = str(output_data.get('reasoning', 'None provided.'))
        if reasoning.startswith("Multi-agent consensus:"):
            # Strip the prefix and split by agent
            content = reasoning.replace("Multi-agent consensus:", "").strip()
            parts = content.split("; ")
            for part in parts:
                if ":" in part:
                    agent, text = part.split(":", 1)
                    pdf.set_font('Helvetica', 'B', 10)
                    pdf.cell(0, 6, f"{agent.strip()}:", border=0, ln=1)
                    pdf.set_font('Helvetica', '', 10)
                    m_cell(6, text.strip())
                    pdf.ln(2)
                else:
                    m_cell(6, part.strip())
        else:
            m_cell(6, reasoning)
        pdf.ln(3)
        
        # 3. Individual Agent Scores
        add_section_title("Detailed Agent Scores")
        scores = output_data.get('individual_scores', {})
        for agent, details in scores.items():
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(0, 8, f"{agent} - Score: {details.get('score')}/10", border=0, ln=1)
            pdf.set_font('Helvetica', '', 9)
            m_cell(6, f"Reasoning: {details.get('reasoning', '')}")
            if details.get('key_factors'):
                m_cell(6, f"Key Factors: {', '.join(details.get('key_factors', []))}")
            pdf.ln(2)
            
        # 4. Bias Analysis Details
        add_section_title("Bias Analysis & Fairness Check")
        pdf.set_font('Helvetica', '', 9)
        m_cell(6, f"Assessment: {bias_data.get('overall_assessment', 'None')}")
        
        if bias_data.get('reasoning'):
            pdf.ln(1)
            pdf.set_font('Helvetica', 'I', 9)
            m_cell(6, f"Detailed Reasoning: {bias_data.get('reasoning')}")
        pdf.ln(2)
        
        if bias_data.get('recommendations'):
            pdf.set_font('Helvetica', 'B', 9)
            pdf.cell(0, 8, "Recommendations for Process:", border=0, ln=1)
            pdf.set_font('Helvetica', '', 9)
            for rec in bias_data.get('recommendations', []):
                m_cell(6, f"• {rec}")
        
        # Save output
        pdf.output(output_path)
        return output_path


class DOCXExporter:
    """Exports ATS JSON output to a beautifully formatted Word document."""
    
    @staticmethod
    def export(output_data: Dict[str, Any], output_path: str) -> str:
        doc = Document()
        
        # Document Title
        title = doc.add_heading('NARI ATS Candidate Evaluation Report', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph()
        
        def add_heading(text, level=1):
            h = doc.add_heading(text, level=level)
            for run in h.runs:
                run.font.color.rgb = RGBColor(0, 51, 102)
                
        def add_key_value(key, value):
            p = doc.add_paragraph()
            p.add_run(f"{key}: ").bold = True
            p.add_run(str(value))
            
        def append_markdown(p, text):
            parts = str(text).split('**')
            for i, part in enumerate(parts):
                run = p.add_run(part)
                if i % 2 == 1:
                    run.bold = True
            
        candidate = output_data.get('candidate_profile', {})
        name = candidate.get('candidate_name') or "Unknown Candidate"
        email = candidate.get('candidate_email') or "N/A"
        
        # 1. Candidate Info
        add_heading("Candidate Profile", level=1)
        add_key_value("Name", name)
        add_key_value("Email", email)
        add_key_value("Applied For (Job)", output_data.get('job_title', 'Unknown'))
        date_str = output_data.get('timestamp', 'Unknown').split('T')[0]
        add_key_value("Processed On", date_str)
        
        # 2. Results Summary (Moved up as requested)
        add_heading("RESULT SUMMARY", level=1)
        add_key_value("Overall Match Score", f"{output_data.get('overall_match_score', 0)} / 10.0")
        add_key_value("Confidence", f"{int(output_data.get('confidence_level', 0) * 100)}%")
        
        p = doc.add_paragraph()
        p.add_run("Recommendation: ").bold = True
        rec_run = p.add_run(str(output_data.get('hiring_recommendation', 'N/A')).upper())
        rec_run.bold = True
        
        bias_data = output_data.get('bias_analysis', {})
        add_key_value("Bias Risk Level", str(bias_data.get('risk_level', 'N/A')).upper())
        
        reasoning = str(output_data.get('reasoning', 'None provided.'))
        if reasoning.startswith("Multi-agent consensus:"):
            p = doc.add_paragraph()
            p.add_run("Multi-agent consensus:").bold = True
            
            content = reasoning.replace("Multi-agent consensus:", "").strip()
            parts = content.split("; ")
            for part in parts:
                if ":" in part:
                    agent, text = part.split(":", 1)
                    p = doc.add_paragraph()
                    p.add_run(f"{agent.strip()}: ").bold = True
                    append_markdown(p, text.strip())
                else:
                    p = doc.add_paragraph()
                    append_markdown(p, part.strip())
        else:
            p = doc.add_paragraph()
            append_markdown(p, reasoning)
        
        doc.add_paragraph()
        
        # 3. Individual Scores
        add_heading("Detailed Agent Scores", level=1)
        scores = output_data.get('individual_scores', {})
        for agent, details in scores.items():
            add_heading(f"{agent} (Score: {details.get('score')}/10)", level=2)
            p_reasoning = doc.add_paragraph("Reasoning: ")
            append_markdown(p_reasoning, details.get('reasoning', ''))
            factors = details.get('key_factors', [])
            if factors:
                p_factors = doc.add_paragraph("Key Factors:\n")
                for f in factors:
                    if f.strip():
                        p_factors.add_run("• ")
                        append_markdown(p_factors, f.strip() + "\n")
                        
        # 4. Bias Analysis Details
        add_heading("Bias Analysis & Fairness Check", level=1)
        doc.add_paragraph(f"Assessment: {bias_data.get('overall_assessment', 'None')}")
        
        if bias_data.get('reasoning'):
            p_reason = doc.add_paragraph()
            p_reason.add_run("Detailed Reasoning: ").bold = True
            append_markdown(p_reason, str(bias_data.get('reasoning')))
        
        recs = bias_data.get('recommendations', [])
        if recs:
            doc.add_paragraph("Process Recommendations:").bold = True
            for r in recs:
                doc.add_paragraph(r, style='List Bullet')

        # Save the file
        doc.save(output_path)
        return output_path
