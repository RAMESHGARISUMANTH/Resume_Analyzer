from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import PyPDF2
import io
import json
from datetime import datetime
import re

# Comprehensive skill catalog
SKILL_SET = {
    # Programming Languages
    "python", "java", "c++", "c", "c#", ".net", "javascript", "typescript", "php", "ruby", "rust",
    "golang", "go", "kotlin", "swift", "dart", "r", "scala", "shell", "bash", "powershell",
    
    # Web & Frontend
    "html", "html5", "css", "css3", "sass", "scss", "react", "react.js", "next.js", "vue", "vue.js",
    "angular", "svelte", "redux", "tailwind", "tailwindcss", "bootstrap", "material ui", "mui",
    "webpack", "vite", "responsive design",
    
    # Backend & Frameworks
    "node.js", "express", "fastapi", "flask", "django", "spring", "spring boot", "nestjs",
    "rest api", "graphql", "microservices", "grpc",
    
    # Databases & Storage
    "sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "sqlite", "oracle", "nosql",
    "elasticsearch", "dynamodb", "cassandra", "firebase",
    
    # Cloud & DevOps
    "docker", "kubernetes", "aws", "azure", "gcp", "google cloud", "terraform", "ci/cd",
    "git", "github", "gitlab", "linux", "unix", "nginx", "jenkins", "ansible",
    
    # AI, ML & Data Science
    "machine learning", "deep learning", "artificial intelligence", "nlp", "computer vision",
    "tensorflow", "keras", "pytorch", "pandas", "numpy", "scikit-learn", "data analysis",
    "data science", "tableau", "power bi", "excel", "opencv", "llm", "huggingface", "scipy",
    
    # Methodologies & Tools
    "agile", "scrum", "jira", "figma", "postman", "unit testing", "tdd", "system design",
    
    # Soft & Leadership Skills
    "communication", "leadership", "project management", "problem solving", "teamwork",
    "critical thinking", "time management", "adaptability", "mentoring"
}

app = FastAPI(title="Resume Analyzer API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobMatchAnalysis(BaseModel):
    match_score: int
    compatibility_level: str
    matching_skills: List[str]
    missing_skills: List[str]
    job_skills: List[str]
    suggestions: List[str]
    job_summary: Optional[str] = None

class ResumeAnalysis(BaseModel):
    skills: List[str]
    education: List[str]
    experience: List[str]
    certifications: List[str]
    recommendations: Optional[List[str]] = None
    score: Optional[int] = None
    issues: Optional[List[str]] = None
    job_match: Optional[JobMatchAnalysis] = None

def extract_text_from_pdf(pdf_file: bytes) -> str:
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file))
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

def extract_skills(text: str) -> list:
    found_skills = set()
    text_lower = " " + text.lower() + " "
    
    for skill in SKILL_SET:
        skill_lower = skill.lower()
        if any(c in skill_lower for c in ["+", "#", ".", " "]):
            escaped = re.escape(skill_lower)
            if re.search(r'(?:\b|[^\w])' + escaped + r'(?:\b|[^\w])', text_lower):
                found_skills.add(skill)
        elif len(skill_lower) <= 2:
            # Short / single-char skills like 'c' or 'r': avoid false positives from stray letters
            if re.search(r'(?:^|[\s,;/|])' + re.escape(skill_lower) + r'(?:[\s,;/|]|$)', text_lower):
                found_skills.add(skill)
        else:
            if re.search(r'\b' + re.escape(skill_lower) + r'\b', text_lower):
                found_skills.add(skill)
                
    return sorted(list(found_skills))

HEADER_MAP = {
    "education": [
        "education", "academics", "academic background", "academic qualification",
        "academic qualifications", "qualifications", "educational background",
        "educational qualifications", "degrees", "degree", "education & certifications",
        "education and certifications", "education & training", "education and training"
    ],
    "experience": [
        "experience", "work experience", "professional experience", "employment history",
        "work history", "relevant experience", "employment", "career history",
        "internship", "internships", "professional background", "experience & projects",
        "work & experience", "experience / projects", "training & experience",
        "industrial experience", "practical experience"
    ],
    "projects": [
        "projects", "technical projects", "key projects", "academic projects",
        "personal projects", "portfolio", "notable projects", "project work",
        "selected projects", "major projects"
    ],
    "certifications": [
        "certifications", "certification", "certificates", "licenses & certifications",
        "certifications & licenses", "courses & certifications", "accreditations",
        "trainings", "licenses", "online courses", "certificates & achievements",
        "achievements & certifications", "certifications and courses", "courses",
        "certifications & trainings", "certificates & licenses", "awards & achievements",
        "achievements", "honors & awards", "credentials"
    ],
    "skills": [
        "skills", "technical skills", "key skills", "core competencies",
        "technologies", "tools & technologies", "technical proficiencies",
        "areas of expertise", "competencies", "programming skills"
    ],
    "summary": [
        "summary", "professional summary", "career objective", "objective",
        "about me", "profile", "overview", "executive summary"
    ]
}

def clean_header_line(line: str) -> str:
    cleaned = re.sub(r'^[•\*\-\–\—\d\.\s#_\|\:\>]+', '', line)
    cleaned = re.sub(r'[\:\-\–\—#_\|\*\s]+$', '', cleaned)
    return cleaned.strip().lower()

def identify_header(line: str) -> str:
    trimmed = line.strip()
    if not trimmed or len(trimmed) > 50:
        return ""
    cleaned = clean_header_line(trimmed)
    if not cleaned:
        return ""
    for section_type, keywords in HEADER_MAP.items():
        for kw in keywords:
            if cleaned == kw or cleaned == f"{kw}s":
                return section_type
            if cleaned.startswith(kw + " ") or cleaned.endswith(" " + kw):
                return section_type
            if cleaned.startswith(kw + ":") or cleaned.startswith(kw + " -"):
                return section_type
    return ""

def is_contact_info(line: str) -> bool:
    lower = line.lower()
    if '@' in lower or 'linkedin.com' in lower or 'github.com' in lower or 'github.io' in lower or 'twitter.com' in lower:
        return True
    if re.search(r'https?://', lower):
        return True
    line_without_years = re.sub(r'(?:19|20)\d{2}\s*[\-–—]\s*(?:(?:19|20)\d{2}|present|current)', '', lower)
    phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', line_without_years)
    if phone_match and any(kw in lower for kw in ['phone', 'tel', 'cell', 'mobile', '+']) or (phone_match and len(re.sub(r'\D', '', phone_match.group(0))) >= 10):
        if len(line.strip()) < 50:
            return True
    return False

def clean_bullet(line: str) -> str:
    line = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', line)
    cleaned = re.sub(r'^[•\*\-\–\—►▪\>\d+\.]\s*', '', line).strip()
    return re.sub(r'\s+', ' ', cleaned)

def parse_resume_sections(text: str) -> dict:
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.strip() for line in text.splitlines()]
    sections = {k: [] for k in HEADER_MAP.keys()}
    current_section = None
    
    for line in lines:
        if not line:
            continue
        detected_section = identify_header(line)
        if detected_section:
            current_section = detected_section
            continue
        if current_section and not is_contact_info(line):
            cleaned = clean_bullet(line)
            if cleaned and len(cleaned) > 2:
                if re.match(r'^(page\s+\d+(\s+of\s+\d+)?|\d+\s*/\s*\d+)$', cleaned, re.IGNORECASE):
                    continue
                sections[current_section].append(cleaned)
    return sections

DEGREE_KEYWORDS = [
    "bachelor", "master", "phd", "ph.d", "doctorate", "b.tech", "btech", "m.tech", "mtech",
    "b.e", "b.s", "b.sc", "bsc", "m.s", "m.sc", "msc", "bba", "mba", "bca", "mca",
    "diploma", "intermediate", "high school", "secondary", "matriculation", "university",
    "college", "institute", "school of", "polytechnic", "cgpa", "gpa", "b.com", "m.com",
    "percentage", "m.p.c", "mpc", "s.s.c", "ssc", "hsc", "cbse", "icse", "school"
]

EXP_KEYWORDS = [
    "developed", "implemented", "built", "designed", "created", "led", "managed",
    "engineered", "architected", "maintained", "collaborated", "contributed",
    "software engineer", "developer", "intern", "analyst", "lead", "specialist",
    "responsibilities", "project", "web app", "application", "database", "api",
    "trainee", "solutions", "full stack", "frontend", "backend", "system"
]

CERT_KEYWORDS = [
    "certified", "certification", "certificate", "coursera", "udemy", "edx", "aws",
    "azure", "gcp", "google", "oracle", "cisco", "comptia", "microsoft", "meta",
    "scrum", "pmp", "kaggle", "nptel", "hackerrank", "freecodecamp", "deeplearning",
    "edu skill", "eduskills", "fundamentals", "training", "badge", "award"
]

def extract_education(text: str, parsed_sections: dict) -> list:
    items = parsed_sections.get("education", [])
    if items:
        res = [it for it in items if not is_contact_info(it)]
        if res:
            return res[:8]
    fallback = []
    for line in text.splitlines():
        trimmed = clean_bullet(line)
        if not trimmed or is_contact_info(trimmed) or len(trimmed) < 4:
            continue
        lower = trimmed.lower()
        if any(dk in lower for dk in DEGREE_KEYWORDS) or (re.search(r'(19|20)\d{2}', lower) and any(w in lower for w in ['grade', 'cgpa', 'passed', 'class', 'honors', 'board', 'percentage', '%'])):
            if trimmed not in fallback:
                fallback.append(trimmed)
    return fallback[:8]

def extract_experience(text: str, parsed_sections: dict) -> list:
    items = parsed_sections.get("experience", []) + parsed_sections.get("projects", [])
    if items:
        res = [it for it in items if not is_contact_info(it)]
        if res:
            return res[:10]
    fallback = []
    for line in text.splitlines():
        trimmed = clean_bullet(line)
        if not trimmed or is_contact_info(trimmed) or len(trimmed) < 15:
            continue
        lower = trimmed.lower()
        if any(ek in lower for ek in EXP_KEYWORDS) or re.search(r'(?:19|20)\d{2}\s*[\-–—]\s*(?:(?:19|20)\d{2}|present|current)', lower):
            if trimmed not in fallback:
                fallback.append(trimmed)
    return fallback[:10]

def extract_certifications(text: str, parsed_sections: dict) -> list:
    items = parsed_sections.get("certifications", [])
    if items:
        res = [it for it in items if not is_contact_info(it)]
        if res:
            return res[:8]
    fallback = []
    for line in text.splitlines():
        trimmed = clean_bullet(line)
        if not trimmed or is_contact_info(trimmed) or len(trimmed) < 6:
            continue
        lower = trimmed.lower()
        if any(ck in lower for ck in CERT_KEYWORDS):
            if trimmed not in fallback:
                fallback.append(trimmed)
    return fallback[:8]

def score_resume(skills, education, experience, certifications):
    score = 0
    score += min(len(skills), 10) * 8
    if education:
        score += 5
    if experience:
        score += 5
    if certifications:
        score += 5
    if score < 60 and skills:
        score = 60
    return min(score, 100), []

def match_job_description(resume_text: str, resume_skills: List[str], job_description: str) -> Optional[JobMatchAnalysis]:
    jd_clean = job_description.strip()
    if not jd_clean:
        return None

    jd_skills = extract_skills(jd_clean)
    resume_skills_lower = {s.lower() for s in resume_skills}

    matching_skills = [s for s in jd_skills if s.lower() in resume_skills_lower]
    missing_skills = [s for s in jd_skills if s.lower() not in resume_skills_lower]

    stop_words = {
        "the", "and", "a", "an", "in", "on", "at", "to", "for", "of", "with", "is", "are", "was",
        "were", "be", "been", "will", "would", "can", "could", "should", "as", "by", "from", "that",
        "this", "these", "those", "it", "its", "or", "not", "we", "you", "our", "your", "they", "their",
        "have", "has", "had", "do", "does", "did", "about", "into", "through", "during", "before", "after",
        "must", "required", "preferred", "plus", "experience", "candidate", "responsibilities", "qualifications"
    }

    jd_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', jd_clean.lower())) - stop_words
    resume_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', resume_text.lower())) - stop_words

    overlap_words = jd_words.intersection(resume_words)
    text_similarity = len(overlap_words) / len(jd_words) if jd_words else 0.5

    if jd_skills:
        skill_ratio = len(matching_skills) / len(jd_skills)
        raw_score = (skill_ratio * 75) + (min(text_similarity * 1.5, 1.0) * 25)
    else:
        raw_score = min(text_similarity * 1.8, 1.0) * 100

    match_score = max(min(int(round(raw_score)), 100), 10)

    if match_score >= 80:
        level = "Strong Match"
    elif match_score >= 60:
        level = "Good Match"
    elif match_score >= 40:
        level = "Moderate Match"
    else:
        level = "Needs Improvement"

    suggestions = []
    if missing_skills:
        preview = ", ".join(missing_skills[:6])
        suggestions.append(f"Highlight missing requirements: Add concrete experience or coursework in {preview} to pass ATS filters.")
    if match_score < 70:
        suggestions.append("Align your resume's terminology with the job description keywords to improve ATS parsing score.")
    if matching_skills:
        suggestions.append(f"Great alignment on {', '.join(matching_skills[:4])}! Emphasize measurable impact and metrics for these skills.")
    suggestions.append("Ensure role titles, tools, and technical competencies are clearly categorized in bullet points.")

    return JobMatchAnalysis(
        match_score=match_score,
        compatibility_level=level,
        matching_skills=matching_skills,
        missing_skills=missing_skills,
        job_skills=jd_skills,
        suggestions=suggestions
    )

def analyze_resume(text: str, job_description: Optional[str] = None) -> ResumeAnalysis:
    parsed_sections = parse_resume_sections(text)
    skills = extract_skills(text)
    education = extract_education(text, parsed_sections)
    experience = extract_experience(text, parsed_sections)
    certifications = extract_certifications(text, parsed_sections)
    recommendations = []
    
    if len(skills) > 0:
        recommendations.append(f"Based on your skills in {', '.join(skills[:3])}, consider roles in Software Development / Data Engineering")
        
    score, issues = score_resume(skills, education, experience, certifications)
    
    job_match = None
    if job_description and job_description.strip():
        job_match = match_job_description(text, skills, job_description)

    return ResumeAnalysis(
        skills=skills,
        education=education,
        experience=experience,
        certifications=certifications,
        recommendations=recommendations,
        score=score,
        issues=issues,
        job_match=job_match
    )

@app.post("/api/analyze", response_model=ResumeAnalysis)
async def analyze_resume_endpoint(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    contents = await file.read()
    text = extract_text_from_pdf(contents)
    analysis = analyze_resume(text, job_description=job_description)
    return analysis

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
