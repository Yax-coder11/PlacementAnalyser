CREATE TABLE users (
    email TEXT PRIMARY KEY,
    password TEXT
);


CREATE TABLE resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    name TEXT,
    phone TEXT,
    email TEXT,
    degree TEXT,
    cgpa TEXT,
    skills TEXT,
    projects TEXT,
    file_path TEXT
);
 