"""Print an actual matcher result using clearly labeled synthetic demo inputs."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from resume_match import read_resume, score
from workflow import evidence_profile

resume = read_resume('demo_resume.txt', (HERE / 'demo_resume.txt').read_bytes())
vacancy = {
    'title': 'Python Developer',
    'description': 'Python developer using SQL, Streamlit, Git and Docker.',
    'location': 'India',
    'source': 'Synthetic demonstration; not an actual vacancy',
}
result = {
    'notice': 'Fictional demo data. The score is text similarity, not measured accuracy or verified eligibility. No application is created or sent.',
    'profile_evidence': evidence_profile(resume),
    'demo_job': vacancy,
    'matching_output': score(resume, vacancy),
}
print(json.dumps(result, indent=2, ensure_ascii=False))
