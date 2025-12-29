def build_resume_text(name, degree, cgpa, skills, projects):
    return f"{name} | {degree} | {cgpa}"

def save_resume_to_file(name, resume_text):
    with open("resumes/test.txt", "w") as f:
        f.write(resume_text)
