import React, { useState } from 'react';
import { 
  Upload, FileText, CheckCircle, AlertCircle, 
  Download, Search, Building2, Users, Loader2,
  Trash2, ChevronRight, BarChart3, ShieldCheck
} from 'lucide-react';

const renderMarkdown = (text) => {
  if (!text || typeof text !== 'string') return text;
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} style={{ color: '#fff', fontWeight: '800' }}>{part.slice(2, -2)}</strong>;
    }
    return <React.Fragment key={i}>{part}</React.Fragment>;
  });
};

function App() {
  const [jd, setJd] = useState({
    title: '',
    company: '',
    department: '',
    description: ''
  });
  const [jdFile, setJdFile] = useState(null);
  const [extracting, setExtracting] = useState(false);
  const [resumes, setResumes] = useState([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleJdFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setJdFile(file);
      extractJd(file);
    }
  };

  const extractJd = async (file = null) => {
    setExtracting(true);
    setError(null);
    
    const formData = new FormData();
    if (file) {
      formData.append('jd_file', file);
    } else if (jd.description) {
      formData.append('jd_text', jd.description);
    } else {
      setExtracting(false);
      return;
    }

    try {
      const response = await fetch('/api/analyze-jd', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'JD extraction failed');
      }
      
      const data = await response.json();
      
      if (!data.job_title && !data.company && !data.department) {
        setError("Warning: Could not extract specific details. Please ensure the JD text is descriptive enough.");
      }

      setJd({
        title: data.job_title || jd.title,
        company: data.company || jd.company,
        department: data.department || jd.department,
        description: data.description || jd.description
      });
    } catch (err) {
      setError("Failed to extract JD details: " + err.message);
    } finally {
      setExtracting(false);
    }
  };

  const handleResumeChange = (e) => {
    const files = Array.from(e.target.files);
    setResumes(prev => [...prev, ...files]);
  };

  const removeResume = (index) => {
    setResumes(prev => prev.filter((_, i) => i !== index));
  };

  const runAnalysis = async () => {
    if (!jd.title || !jd.company || resumes.length === 0) {
      setError("Please provide Job Title, Company, and at least one resume.");
      return;
    }

    setAnalyzing(true);
    setError(null);
    setResults(null);

    const formData = new FormData();
    formData.append('job_title', jd.title);
    formData.append('company', jd.company);
    formData.append('department', jd.department || 'General');
    formData.append('jd_text', jd.description);
    
    resumes.forEach(file => {
      formData.append('resumes', file);
    });

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Analysis failed server-side');
      
      const data = await response.json();
      setResults(data.results);
    } catch (err) {
      setError(err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const downloadReport = async (candidateData, format) => {
    try {
      const formData = new FormData();
      formData.append('analysis_data', JSON.stringify(candidateData));
      formData.append('format', format);

      const response = await fetch('/api/export', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Export generation failed');
      const data = await response.json();
      
      // Navigate to the direct download URL
      window.location.href = `/api/download/${data.file_id}`;
    } catch (err) {
      alert("Failed to download report: " + err.message);
    }
  };

  return (
    <div className="container">
      <header className="animate-fade-in" style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <h1 style={{ fontSize: '3rem', fontWeight: '800', marginBottom: '0.5rem', background: 'linear-gradient(to right, #818cf8, #c084fc)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          NARI ATS
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.25rem' }}>Premium Multi-Agent Candidate Intelligence</p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '3rem' }}>
        {/* Job Description Section */}
        <section className="glass-card animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Building2 size={24} color="var(--primary)" />
              <h2 style={{ fontSize: '1.5rem' }}>Job Details</h2>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button 
                className="btn" 
                style={{ padding: '0.4rem 0.8rem', fontSize: '0.75rem', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--card-border)', gap: '0.4rem' }}
                onClick={() => document.getElementById('jd-file-input').click()}
                disabled={extracting}
              >
                <Upload size={14} /> Upload JD File
              </button>
              <input 
                id="jd-file-input"
                type="file"
                hidden
                onChange={handleJdFileChange}
              />
            </div>
          </div>
          
          <div className="input-group">
            <label className="input-label">1. Paste Job Description or Requirements</label>
            <textarea 
              className="input-field" 
              placeholder="Paste the job description here or upload a file above..."
              value={jd.description}
              onChange={e => setJd({...jd, description: e.target.value})}
              style={{ minHeight: '180px' }}
            />
          </div>

          <button 
            className="btn" 
            style={{ width: '100%', marginBottom: '2rem', background: 'rgba(99, 102, 241, 0.1)', border: '1px solid var(--primary)', color: 'var(--primary)', gap: '0.5rem' }}
            onClick={() => extractJd()}
            disabled={extracting || !jd.description}
          >
            {extracting ? <Loader2 className="animate-spin" size={18} /> : <Search size={18} />}
            {extracting ? "Extracting Details..." : "Extract & Auto-Fill Details Below"}
          </button>

          <div style={{ opacity: extracting ? 0.5 : 1, transition: 'opacity 0.2s ease' }}>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1rem', fontWeight: '600' }}>2. Review & Edit Extracted Info</p>
            
            <div className="input-group">
              <label className="input-label">Job Title</label>
              <input 
                className="input-field" 
                placeholder="Extracting..."
                value={jd.title}
                onChange={e => setJd({...jd, title: e.target.value})}
              />
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="input-group">
                <label className="input-label">Company</label>
                <input 
                  className="input-field" 
                  placeholder="Extracting..."
                  value={jd.company}
                  onChange={e => setJd({...jd, company: e.target.value})}
                />
              </div>
              <div className="input-group">
                <label className="input-label">Department</label>
                <input 
                  className="input-field" 
                  placeholder="Extracting..."
                  value={jd.department}
                  onChange={e => setJd({...jd, department: e.target.value})}
                />
              </div>
            </div>
          </div>
        </section>

        {/* Resume Upload Section */}
        <section className="glass-card animate-fade-in" style={{ animationDelay: '0.2s' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
            <Users size={24} color="var(--primary)" />
            <h2 style={{ fontSize: '1.5rem' }}>Resumes</h2>
          </div>

          <div 
            style={{ 
              border: '2px dashed var(--card-border)', 
              borderRadius: '0.75rem', 
              padding: '2rem', 
              textAlign: 'center',
              cursor: 'pointer',
              background: 'rgba(255,255,255,0.02)',
              transition: 'background 0.2s ease'
            }}
            onMouseOver={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
            onMouseOut={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
            onClick={() => document.getElementById('resume-input').click()}
          >
            <Upload size={40} color="var(--text-muted)" style={{ marginBottom: '1rem' }} />
            <p style={{ color: 'var(--text-muted)' }}>Click or drag to upload candidate resumes</p>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>PDF, DOCX, TXT, Images supported</p>
            <input 
              id="resume-input"
              type="file" 
              multiple 
              hidden 
              onChange={handleResumeChange}
            />
          </div>

          <div style={{ marginTop: '1.5rem', maxHeight: '200px', overflowY: 'auto' }}>
            {resumes.map((file, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '0.5rem', marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <FileText size={18} color="var(--primary)" />
                  <span style={{ fontSize: '0.875rem' }}>{file.name}</span>
                </div>
                <button 
                  onClick={(e) => { e.stopPropagation(); removeResume(idx); }}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--danger)' }}
                >
                  <Trash2 size={18} />
                </button>
              </div>
            ))}
          </div>

          <div style={{ marginTop: '2rem' }}>
            <button 
              className="btn btn-primary" 
              style={{ width: '100%', gap: '0.5rem' }}
              onClick={runAnalysis}
              disabled={analyzing}
            >
              {analyzing ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  Analyzing with Multi-Agent Workflow...
                </>
              ) : (
                <>
                  <Search size={20} />
                  Start Smart Screening
                </>
              )}
            </button>
          </div>
          
          {error && (
            <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--danger)', borderRadius: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#f87171' }}>
              <AlertCircle size={20} />
              <span style={{ fontSize: '0.875rem' }}>{error}</span>
            </div>
          )}
        </section>
      </div>

      {/* Results Section */}
      {results && (
        <section className="animate-fade-in">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '2rem' }}>
            <BarChart3 size={24} color="var(--primary)" />
            <h2 style={{ fontSize: '1.75rem' }}>Analysis Results</h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {results.map((res, idx) => (
              <div key={idx} className="glass-card" style={{ display: 'flex', flexDirection: 'column', padding: '2rem' }}>
                {res.status === 'success' ? (
                  <>
                    {/* TOP HEADER SECTION */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2rem', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '1.5rem', marginBottom: '1.5rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                        <div style={{ 
                          width: '70px', height: '70px', display: 'flex', alignItems: 'center', justifyContent: 'center',
                          background: res.data.overall_match_score >= 7 ? 'rgba(34, 197, 94, 0.15)' : res.data.overall_match_score >= 5 ? 'rgba(245, 158, 11, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                          color: res.data.overall_match_score >= 7 ? '#4ade80' : res.data.overall_match_score >= 5 ? '#fbbf24' : '#f87171',
                          border: `2px solid ${res.data.overall_match_score >= 7 ? 'var(--success)' : res.data.overall_match_score >= 5 ? 'var(--warning)' : 'var(--danger)'}`,
                          borderRadius: '50%', fontWeight: '800', fontSize: '1.5rem'
                        }}>
                          {res.data.overall_match_score}
                        </div>
                        <div>
                          <h3 style={{ fontSize: '1.75rem', fontWeight: '800', marginBottom: '0.25rem' }}>
                            {res.data.candidate_profile.candidate_name || 'Unknown Candidate'}
                          </h3>
                          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                             <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>{res.filename}</span>
                          </div>
                        </div>
                      </div>

                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2.5rem', alignItems: 'center' }}>
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '600', letterSpacing: '0.05em' }}>Hiring Recommendation</span>
                          <span style={{ fontSize: '1.25rem', fontWeight: '800', color: res.data.hiring_recommendation === 'STRONG_YES' ? 'var(--success)' : res.data.hiring_recommendation === 'NO' ? 'var(--danger)' : 'var(--warning)', marginTop: '0.25rem' }}>
                            {res.data.hiring_recommendation.replace('_', ' ')}
                          </span>
                        </div>
                        <div style={{ display: 'flex', gap: '1rem', height: 'fit-content' }}>
                          <button className="btn" style={{ border: '1px solid var(--card-border)', background: 'rgba(255,255,255,0.03)', gap: '0.5rem', padding: '0.5rem 1rem', fontSize: '0.875rem' }} onClick={() => downloadReport(res.data, 'docx')}>
                            <Download size={16} /> DOCX
                          </button>
                          <button className="btn" style={{ border: '1px solid var(--card-border)', background: 'rgba(255,255,255,0.03)', gap: '0.5rem', padding: '0.5rem 1rem', fontSize: '0.875rem' }} onClick={() => downloadReport(res.data, 'pdf')}>
                            <Download size={16} /> PDF
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* TWO-COLUMN DETAILS SECTION */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '2.5rem' }}>
                      
                      {/* Left: Formatted Consensus Reasoning */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <h4 style={{ fontSize: '0.9rem', fontWeight: '700', color: 'var(--text-main)', textTransform: 'uppercase', letterSpacing: '0.05em', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <Loader2 size={16} className="animate-spin" style={{ animationDuration: '3s' }} /> Consensus Final Report
                        </h4>
                        <div style={{ background: 'rgba(255,255,255,0.015)', padding: '1.5rem', borderRadius: '0.75rem', borderLeft: '3px solid var(--primary)', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                            {(() => {
                              const text = res.data.reasoning;
                              if (text.startsWith("Multi-agent consensus:")) {
                                const withoutPrefix = text.replace("Multi-agent consensus:", "").trim();
                                const parts = withoutPrefix.split(';');
                                return parts.map((part, i) => {
                                  if (!part.trim()) return null;
                                  const colonIdx = part.indexOf(':');
                                  if (colonIdx > -1 && colonIdx < 30) {
                                     const agent = part.slice(0, colonIdx).trim();
                                     const detail = part.slice(colonIdx + 1).trim();
                                     return (
                                       <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                         <span style={{ fontWeight: '800', color: '#a5b4fc', fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                           <CheckCircle size={14} /> {agent.replace(/([A-Z])/g, ' $1').trim()}
                                         </span>
                                         <p style={{ fontSize: '0.95rem', color: 'var(--text-main)', lineHeight: '1.6' }}>{renderMarkdown(detail)}</p>
                                       </div>
                                     )
                                  }
                                  return <p key={i} style={{ fontSize: '0.95rem', color: 'var(--text-main)', lineHeight: '1.6' }}>{renderMarkdown(part.trim())}</p>
                                });
                              }
                              return <p style={{ fontSize: '0.95rem', color: 'var(--text-main)', fontStyle: 'italic', lineHeight: '1.6' }}>"{text}"</p>
                            })()}
                        </div>
                      </div>

                      {/* Right: Individual Agent Scores Grid */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <h4 style={{ fontSize: '0.9rem', fontWeight: '700', color: 'var(--text-main)', textTransform: 'uppercase', letterSpacing: '0.05em', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <Users size={16} /> Individual Agent Breakdown
                        </h4>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1rem' }}>
                           {Object.entries(res.data.individual_scores).map(([name, score]) => (
                             <div key={name} style={{ background: 'rgba(255,255,255,0.025)', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid rgba(255,255,255,0.05)' }}>
                               <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                                 <p style={{ fontSize: '0.9rem', color: 'var(--text-main)', fontWeight: '700' }}>{name.replace(/([A-Z])/g, ' $1').trim()}</p>
                                 <div style={{ background: 'rgba(99, 102, 241, 0.1)', color: '#818cf8', padding: '0.35rem 0.75rem', borderRadius: '2rem', fontWeight: '800', fontSize: '0.875rem', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
                                    {score.score}/10
                                 </div>
                               </div>
                               {score.reasoning && (
                                 <p style={{ fontSize: '0.85rem', color: 'rgba(255,255,255,0.7)', marginBottom: '0.75rem', lineHeight: '1.5' }}>{renderMarkdown(score.reasoning)}</p>
                               )}
                               {score.key_factors && score.key_factors.length > 0 && (
                                 <ul style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.8)', paddingLeft: '1.25rem', listStyleType: 'circle', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                   {score.key_factors.map((factor, idx) => (
                                     <li key={idx}><span style={{ color: 'var(--success)', marginRight: '0.25rem' }}>✓</span> {renderMarkdown(factor)}</li>
                                   ))}
                                 </ul>
                               )}
                             </div>
                           ))}
                        </div>
                      </div>

                    </div>
                  </>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: '2rem', textAlign: 'center' }}>
                    <AlertCircle size={48} color="var(--danger)" style={{ marginBottom: '1rem' }} />
                    <h3 style={{ marginBottom: '0.5rem' }}>Processing Error</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>{res.error}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      <footer style={{ marginTop: '5rem', textAlign: 'center', color: 'var(--text-muted)', paddingBottom: '2rem' }}>
        <p>© 2026 NARI ATS Intelligence Framework. Built for visual excellence.</p>
      </footer>

      {/* Tailwind-like utility classes that I defined in index.css */}
      <style>{`
        .animate-spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default App;
