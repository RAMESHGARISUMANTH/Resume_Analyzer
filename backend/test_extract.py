import re

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
        "work & experience"
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
        "achievements & certifications", "certifications and courses", "courses"
    ],
    "skills": [
        "skills", "technical skills", "key skills", "core competencies",
        "technologies", "tools & technologies", "technical proficiencies",
        "areas of expertise", "competencies", "programming skills"
    ],
    "summary": [
        "summary", "professional summary", "career objective", "objective",
        "about me", "profile", "overview", "executive summary"
    ],
    "awards": [
        "awards", "honors", "achievements", "accomplishments", "extracurricular"
    ]
}

def clean_header_line(line: str) -> str:
    cleaned = re.sub(r'^[•\*\-\–\—\d\.\s#_\|\:\>]+', '', line)
    cleaned = re.sub(r'[\:\-\–\—#_\|\*\s]+$', '', cleaned)
    return cleaned.strip().lower()

def identify_header(line: str) -> str:
    trimmed = line.strip()
    if not trimmed or len(trimmed) > 45:
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
    return ""

def is_contact_info(line: str) -> bool:
    lower = line.lower()
    # Email, social links
    if '@' in lower or 'linkedin.com' in lower or 'github.com' in lower or 'github.io' in lower or 'twitter.com' in lower:
        return True
    if re.search(r'https?://', lower):
        return True
    
    # Check phone number without falsely catching year ranges like 2020 - 2024
    # Clean out year ranges first before checking digits
    line_without_years = re.sub(r'(?:19|20)\d{2}\s*[\-–—]\s*(?:(?:19|20)\d{2}|present|current)', '', lower)
    phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', line_without_years)
    if phone_match and any(kw in lower for kw in ['phone', 'tel', 'cell', 'mobile', '+']) or (phone_match and len(re.sub(r'\D', '', phone_match.group(0))) >= 10):
        # Only treat entire line as contact info if the line is mostly the contact info
        if len(line.strip()) < 50:
            return True
            
    return False

def clean_bullet(line: str) -> str:
    return re.sub(r'^[•\*\-\–\—►▪\>\d+\.]\s*', '', line).strip()

def parse_resume_sections(text: str) -> dict:
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
    "college", "institute", "school of", "polytechnic", "cgpa", "gpa", "b.com", "m.com"
]

EXP_KEYWORDS = [
    "developed", "implemented", "built", "designed", "created", "led", "managed",
    "engineered", "architected", "maintained", "collaborated", "contributed",
    "software engineer", "developer", "intern", "analyst", "lead", "specialist",
    "responsibilities", "project", "web app", "application", "database", "api"
]

CERT_KEYWORDS = [
    "certified", "certification", "certificate", "coursera", "udemy", "edx", "aws",
    "azure", "gcp", "google", "oracle", "cisco", "comptia", "microsoft", "meta",
    "scrum", "pmp", "kaggle", "nptel", "hackerrank", "freecodecamp", "deeplearning"
]

def extract_education_robust(text: str, parsed_sections: dict) -> list:
    items = parsed_sections.get("education", [])
    if items:
        # Keep non-contact, meaningful items
        result = [it for it in items if not is_contact_info(it)]
        if result:
            return result[:8]
    
    # Fallback: scan whole text for lines matching degrees or institutions
    fallback = []
    for line in text.splitlines():
        trimmed = clean_bullet(line)
        if not trimmed or is_contact_info(trimmed) or len(trimmed) < 4:
            continue
        lower = trimmed.lower()
        if any(dk in lower for dk in DEGREE_KEYWORDS) or (re.search(r'(19|20)\d{2}', lower) and any(w in lower for w in ['grade', 'cgpa', 'passed', 'class', 'honors', 'board'])):
            if trimmed not in fallback:
                fallback.append(trimmed)
    return fallback[:8]

def extract_experience_robust(text: str, parsed_sections: dict) -> list:
    items = parsed_sections.get("experience", []) + parsed_sections.get("projects", [])
    if items:
        result = [it for it in items if not is_contact_info(it)]
        if result:
            return result[:10]
            
    # Fallback: scan whole text for lines with action verbs
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

def extract_certifications_robust(text: str, parsed_sections: dict) -> list:
    items = parsed_sections.get("certifications", [])
    if items:
        result = [it for it in items if not is_contact_info(it)]
        if result:
            return result[:8]
            
    # Fallback: scan whole text
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

# Test with sample_1
sample_1 = """
RAMESH S
Full Stack Developer
contact@gmail.com | +91 9876543210 | linkedin.com/in/ramesh

EDUCATION:
Bachelor of Technology in Computer Science & Engineering
ABC Institute of Technology, 2020 - 2024
CGPA: 8.5/10

TECHNICAL SKILLS:
Python, JavaScript, React, FastAPI, Docker, SQL

WORK EXPERIENCE:
Software Engineer Intern - Tech Solutions (Jan 2024 - Present)
• Developed responsive full-stack web applications using React and FastAPI
• Implemented REST APIs and optimized database queries in PostgreSQL
• Integrated Docker containers for CI/CD deployment pipelines

PROJECTS:
Resume Analyzer AI
• Built an automated resume screening tool using PyPDF2 and Machine Learning
• Analyzed candidate skills and matched against job requirements with 95% accuracy

CERTIFICATIONS:
• AWS Certified Cloud Practitioner - Amazon Web Services (2023)
• Meta Front-End Developer Professional Certificate - Coursera
"""

parsed = parse_resume_sections(sample_1)
edu = extract_education_robust(sample_1, parsed)
exp = extract_experience_robust(sample_1, parsed)
cert = extract_certifications_robust(sample_1, parsed)

print("EDUCATION (", len(edu), "):", edu)
print("EXPERIENCE (", len(exp), "):", exp)
print("CERTIFICATIONS (", len(cert), "):", cert)
