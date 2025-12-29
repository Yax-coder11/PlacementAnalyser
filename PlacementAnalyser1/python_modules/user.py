class User:
    def __init__(self, username):
        self.username = username
        self.resumes = []

    def add_resume(self, resume):
        self.resumes.append(resume)

    def total_resumes(self):
        return len(self.resumes)
