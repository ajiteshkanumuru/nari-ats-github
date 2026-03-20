"""
Main entry point for the NARI ATS System.
Run resumes against job descriptions and get structured output.
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

from src.models.schemas import JobDescription
from src.orchestration import NARIATSOrchestrator


def load_job_description(jd_path: str) -> JobDescription:
    """Load job description from JSON file."""
    with open(jd_path, 'r') as f:
        data = json.load(f)
    return JobDescription(**data)


def process_resume(orchestrator: NARIATSOrchestrator, resume_path: str, 
                   job_description: JobDescription) -> dict:
    """Process a single resume against a job description."""
    
    print(f"\n{'='*70}")
    print(f"Processing: {Path(resume_path).name}")
    print(f"Job: {job_description.job_title}")
    print(f"{'='*70}\n")
    
    try:
        # Run the orchestrator (synchronous)
        output = orchestrator.run_sync(resume_path, job_description)
        return output
    except Exception as e:
        print(f"Error processing resume: {str(e)}")
        return {"error": str(e), "resume": Path(resume_path).name}


def save_output(output: dict, output_dir: str, resume_name: str) -> str:
    """Save output to JSON file."""
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate output filename
    output_filename = Path(resume_name).stem + "_output.json"
    output_path = Path(output_dir) / output_filename
    
    # Save the output
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Output saved to: {output_path}")
    return str(output_path)


def main():
    """Main execution function."""
    
    # Load environment variables
    load_dotenv()
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    
    # Initialize orchestrator
    print("Initializing NARI ATS System...")
    orchestrator = NARIATSOrchestrator(groq_api_key)
    print("✓ System initialized\n")
    
    export_format = input("Do you also want human-readable reports? (None / DOCX / PDF / Both) [None]: ").strip().lower()
    export_docx = export_format in ['docx', 'both']
    export_pdf = export_format in ['pdf', 'both']

    
    # Define paths
    base_dir = Path(__file__).parent
    samples_input_dir = base_dir / "samples" / "input"
    samples_output_dir = base_dir / "samples" / "output"
    
    # Load job descriptions
    jd_files = list(samples_input_dir.glob("job_description_*.json"))
    
    if not jd_files:
        print("No job descriptions found in samples/input/")
        print("Please create job_description_*.json files in samples/input/")
        return
    
    from src.utils.exporters import DOCXExporter, PDFExporter
    
    # Process each job description
    for jd_file in jd_files:
        print(f"\nLoading job description: {jd_file.name}")
        job_description = load_job_description(jd_file)
        print(f"✓ Loaded: {job_description.job_title} at {job_description.company}")
        
        # Find all resume files
        resume_files = []
        for ext in ['*.pdf', '*.docx', '*.doc', '*.txt', '*.html', '*.htm', '*.png', '*.jpg', '*.jpeg']:
            resume_files.extend(samples_input_dir.glob(ext))
        
        # Remove job description files from resume list
        resume_files = [f for f in resume_files if not f.name.startswith('job_description')]
        
        if not resume_files:
            print("No resume files found in samples/input/")
            continue
        
        # Process each resume
        for resume_path in resume_files:
            output = process_resume(orchestrator, str(resume_path), job_description)
            
            # Save output
            save_output(output, str(samples_output_dir), resume_path.name)
            
            # Print summary and export reports
            if "error" not in output:
                if export_docx or export_pdf:
                    try:
                        if export_docx:
                            docx_path = Path(samples_output_dir) / (Path(resume_path.name).stem + "_report.docx")
                            DOCXExporter.export(output, str(docx_path))
                            print(f"✓ DOCX Report saved to: {docx_path}")
                        if export_pdf:
                            pdf_path = Path(samples_output_dir) / (Path(resume_path.name).stem + "_report.pdf")
                            PDFExporter.export(output, str(pdf_path))
                            print(f"✓ PDF Report saved to: {pdf_path}")
                    except Exception as e:
                        print(f"Error generating reports for {resume_path.name}: {str(e)}")

                print(f"\nRESULT SUMMARY for {resume_path.name}:")
                match_score = output.get('overall_match_score', 'N/A')
                confidence = output.get('confidence_level', 0)
                recommendation = output.get('hiring_recommendation', 'N/A')
                bias_risk = output.get('bias_analysis', {}).get('risk_level', 'N/A').upper()
                
                print(f"  Overall Match Score: {match_score}/10")
                print(f"  Confidence: {confidence*100:.0f}%")
                print(f"  Recommendation: {recommendation}")
                print(f"  Bias Risk Level: {bias_risk}")
                print("-" * 40)
            else:
                print(f"Skipping report generation for {resume_path.name} due to processing error.")


if __name__ == "__main__":
    main()
