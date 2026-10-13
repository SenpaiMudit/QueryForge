-- Sample University Database for QueryForge
CREATE TABLE IF NOT EXISTS departments (
    dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_name TEXT NOT NULL,
    building TEXT,
    budget REAL
);

INSERT INTO departments (dept_name, building, budget) VALUES
('Computer Science', 'Turing Hall', 1200000.0),
('Mathematics', 'Euler Hall', 850000.0),
('Physics', 'Newton Hall', 950000.0),
('Economics', 'Smith Hall', 700000.0),
('Biology', 'Darwin Hall', 1100000.0);

CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE,
    dept_id INTEGER,
    gpa REAL,
    enrollment_year INTEGER,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

INSERT INTO students (first_name, last_name, email, dept_id, gpa, enrollment_year) VALUES
('Alice', 'Johnson', 'alice@uni.edu', 1, 3.85, 2022),
('Bob', 'Smith', 'bob@uni.edu', 1, 3.42, 2023),
('Charlie', 'Brown', 'charlie@uni.edu', 2, 3.91, 2021),
('Diana', 'Prince', 'diana@uni.edu', 3, 3.65, 2022),
('Evan', 'Wright', 'evan@uni.edu', 4, 2.95, 2023),
('Fiona', 'Gallagher', 'fiona@uni.edu', 1, 3.78, 2021),
('George', 'Clark', 'george@uni.edu', 5, 3.20, 2022),
('Hannah', 'Abbott', 'hannah@uni.edu', 2, 3.55, 2023),
('Ian', 'Malcolm', 'ian@uni.edu', 5, 3.88, 2021),
('Julia', 'Roberts', 'julia@uni.edu', 4, 3.45, 2022);

CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT UNIQUE,
    title TEXT NOT NULL,
    credits INTEGER,
    dept_id INTEGER,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

INSERT INTO courses (course_code, title, credits, dept_id) VALUES
('CS101', 'Intro to Computer Science', 4, 1),
('CS201', 'Data Structures & Algorithms', 4, 1),
('CS305', 'Database Management Systems', 3, 1),
('MATH101', 'Calculus I', 4, 2),
('MATH201', 'Linear Algebra', 3, 2),
('PHYS101', 'Classical Mechanics', 4, 3),
('ECON101', 'Principles of Microeconomics', 3, 4),
('BIO101', 'General Biology', 4, 5);

CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    semester TEXT,
    grade TEXT,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

INSERT INTO enrollments (student_id, course_id, semester, grade) VALUES
(1, 1, 'Fall 2022', 'A'),
(1, 2, 'Spring 2023', 'A'),
(1, 3, 'Fall 2023', 'A-'),
(2, 1, 'Fall 2023', 'B+'),
(2, 2, 'Spring 2024', 'B'),
(3, 4, 'Fall 2021', 'A'),
(3, 5, 'Spring 2022', 'A'),
(4, 6, 'Fall 2022', 'A-'),
(5, 7, 'Fall 2023', 'C+'),
(6, 1, 'Fall 2021', 'A'),
(6, 3, 'Fall 2022', 'A'),
(7, 8, 'Fall 2022', 'B'),
(8, 4, 'Fall 2023', 'B+'),
(9, 8, 'Fall 2021', 'A'),
(10, 7, 'Fall 2022', 'B');
