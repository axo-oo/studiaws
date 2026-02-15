# ---------------------------------------------------------
# # LIBRARIES
# - All the libraries I am using for my project
# - Sqlite3 -> uses SQL to creat database, weaves it into python
# - Codecs  -> handles all file reading/writing, helps with encoding
# - Typing -> Hints for what type the data is
# ---------------------------------------------------------
import sqlite3
import codecs
from typing import List, Tuple, Optional
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

# ---------------------------------------------------------
# Using SQL to create the database and necessary tables, as well as insert data
# ---------------------------------------------------------
class DefenceDatabase:
    def __init__(self, db="defence.db"):
        self.db = db 
        self.connection = sqlite3.connect(self.db) # connects the database with the code
        self.cursor = self.connection.cursor() # a cursor is the object which executes SQL commands

    def drop_all_tables(self):
        # Dropping all tables first to prevent the endless loop of cases appearing
        self.cursor.execute('''DROP TABLE IF EXISTS Defences;''')
        self.cursor.execute('''DROP TABLE IF EXISTS Law;''')
        self.cursor.execute('''DROP TABLE IF EXISTS Quiz;''')
        self.cursor.execute('''DROP TABLE IF EXISTS Quiz_Question;''')
        self.cursor.execute('''DROP TABLE IF EXISTS Quiz_Answer;''')
                
    def create_tables(self):
        # Defence Table, includes a unique id, the name of the defence, and if it has an essay question
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Defences (
                            defence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            defence_type TEXT NOT NULL,
                            essay_question BIT
                            )
        ''')
        
        # Case Law Table, includes a unique id, defence type, name of case, and the law!
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Law (
                            law_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            defence_id INTEGER,
                            case_name TEXT NOT NULL,
                            case_law TEXT NOT NULL,
                            FOREIGN KEY (defence_id) REFERENCES Defence(defence_id)
                            )                    
        ''')

        # Quiz table (one quiz can belong to a defence)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Quiz (
                quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
                defence_id INTEGER NOT NULL,
                quiz_title TEXT NOT NULL,
                quiz_link TEXT,
                FOREIGN KEY (defence_id) REFERENCES Defences(defence_id) ON DELETE CASCADE 
            );
        """)
        # DELETE CASCADE - delete the foreign key from child table if deleted in adult table

        # QuizQuestion table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Quiz_Question (
                question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                defence_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                FOREIGN KEY (quiz_id) REFERENCES Quiz(quiz_id) ON DELETE CASCADE,
                FOREIGN KEY (defence_id) REFERENCES Defences(defence_id) ON DELETE CASCADE
            );
        """)

        # QuizAnswer table (multiple-choice answers with correctness flag)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Quiz_Answer (
                answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                answer_text TEXT NOT NULL,
                is_correct INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (question_id) REFERENCES Quiz_Question(question_id) ON DELETE CASCADE
            );
        """)

        # UserData table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS User_Data (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            );
        """)

        # Score table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Score (
                score_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                quiz_id INTEGER NOT NULL,
                score_value INTEGER NOT NULL,
                date_taken TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES User_Data(user_id) ON DELETE CASCADE,
                FOREIGN KEY (quiz_id) REFERENCES Quiz(quiz_id) ON DELETE CASCADE
            );
        """)

        self.connection.commit()

    # -----------------------------------------------------------------------------------
    # This is used to add defences
    def add_defence(self, defence_type: str, has_essay: int = 0):
        self.cursor.execute("""
            INSERT INTO Defences (defence_type, essay_question) VALUES (?, ?);
        """, (defence_type.upper(), has_essay))
        self.connection.commit()

    # Adds cases to the law table
    def add_law_cases(self, cases_list: List[Tuple[int, str, str]]):
        # cases_list: (defence_id, case_name, case_law)
        self.cursor.executemany("""
            INSERT INTO Law (defence_id, case_name, case_law)
            VALUES (?, ?, ?);
        """, cases_list)
        self.connection.commit()

    def add_quiz(self, defence_id: int, quiz_title: str, quiz_link: Optional[str] = None) -> int:
        self.cursor.execute("""
            INSERT INTO Quiz (defence_id, quiz_title, quiz_link) VALUES (?, ?, ?);
        """, (defence_id, quiz_title, quiz_link))
        self.connection.commit()
    
    def add_question(self, quiz_id: int, defence_id: int, question_text: str) -> int:
        self.cursor.execute("""
            INSERT INTO Quiz_Question (quiz_id, defence_id, question_text) VALUES (?, ?, ?);
        """, (quiz_id, defence_id, question_text))
        self.connection.commit()
        return self.cursor.lastrowid

    def add_answers(self, answers: List[Tuple[int, str, int]]):
        # answers: (question_id, answer_text, is_correct[0/1])
        self.cursor.executemany("""
            INSERT INTO Quiz_Answer (question_id, answer_text, is_correct)
            VALUES (?, ?, ?);
        """, answers)
        self.connection.commit()

    def add_user(self, name: str, email: str) -> int:
        self.cursor.execute("SELECT user_id FROM User_Data WHERE email = ?", (email,))
        existing = self.cursor.fetchone()
        if existing:
            print(f"User with email {email} already exists (user_id={existing[0]}).")
            return existing[0]  # return the existing user_id instead of inserting
        else:
            self.cursor.execute("INSERT INTO User_Data (name, email) VALUES (?, ?)", (name, email))
            self.connection.commit()
            return self.cursor.lastrowid

    def add_score(self, user_id: int, quiz_id: int, score_value: int) -> int:
        self.cursor.execute("""
            INSERT INTO Score (user_id, quiz_id, score_value)
            VALUES (?, ?, ?);
        """, (user_id, quiz_id, score_value))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def close_db(self):
        self.connection.close()

# ---------------------------------------------------------
# The following code fetches the data from the database, it is all of the select queries
# ---------------------------------------------------------   
class DataFetcher(DefenceDatabase):  
    def fetch_all_law(self):
        self.cursor.execute("SELECT * FROM Law;")
        return self.cursor.fetchall()

    def fetch_all_defences(self):
        self.cursor.execute("SELECT defence_id, defence_type, essay_question FROM Defences;")
        return self.cursor.fetchall()

    def fetch_law_by_defence(self, defence_type_keyword: str):
        # Find law linked to a specific defence type (case_name + case_law)
        self.cursor.execute("""
            SELECT Law.case_name, Law.case_law
            FROM Law
            INNER JOIN Defences ON Law.defence_id = Defences.defence_id
            WHERE Defences.defence_type LIKE ?;
        """, (f"%{defence_type_keyword.upper()}%",))
        return self.cursor.fetchall()

    def fetch_case_law_text(self, case_name_keyword: str):
        # SELECT specific column(s)
        self.cursor.execute("""
            SELECT Law.case_law
            FROM Law
            WHERE Law.case_name LIKE ?;
        """, (f"%{case_name_keyword}%",))
        return self.cursor.fetchall()
    
    def fetch_quiz(self):
        self.cursor.execute("""SELECT quiz_id, quiz_title
                            FROM Quiz;
                            """)
        return self.cursor.fetchall()

    def fetch_quiz_with_questions_answers(self, quiz_id: int):
        # Returns [(question_text, [(answer_text, is_correct), ...]), ...]
        self.cursor.execute("""
            SELECT question_id, question_text
            FROM Quiz_Question
            WHERE quiz_id = ?;
        """, (quiz_id,))
        questions = self.cursor.fetchall()
        compiled = []
        for q_id, q_text in questions:
            self.cursor.execute("""
                SELECT answer_text, is_correct
                FROM Quiz_Answer
                WHERE question_id = ?;
            """, (q_id,))
            answers = self.cursor.fetchall()
            compiled.append((q_text, answers))
        return compiled

    def save_score(self, user_id, quiz_id, score_value):
        self.cursor.execute("""
            INSERT INTO Score (user_id, quiz_id, score_value)
            VALUES (?, ?, ?)
        """, (user_id, quiz_id, score_value))
        self.connection.commit()
        return self.cursor.lastrowid

    def fetch_scores_by_user(self, user_id):
        self.cursor.execute("""
            SELECT score_id, quiz_id, score_value, date_taken
            FROM Score
            WHERE user_id = ?
        """, (user_id,))
        return self.cursor.fetchall()

    def fetch_scores_by_quiz(self, quiz_id):
        self.cursor.execute("""
            SELECT score_id, user_id, score_value, date_taken
            FROM Score
            WHERE quiz_id = ?
        """, (quiz_id,))
        return self.cursor.fetchall()

# ---------------------------------------------------------
# The following code reads the HTML template and renders content
# ---------------------------------------------------------
class Website_Code:
    def __init__(self, website_file):
        self.website_file = website_file 

    def load_website(self):
        with codecs.open (self.website_file, "r", encoding="utf-8") as file: # file reading with codecs, website based library
            return file.read()
    
    # ----------- CASES RENDERING ----------- 
    def render_cases(self, cases):
        list_items = "".join(
            f"<li><strong>{case_name}</strong>: {case_law}</li>" # uses an f string to insert values into html, li creates list and strong makes it bold
            for _, _, case_name, case_law in cases #_ skips the primary/foreign keys 
        )
        return list_items

    # ----------- DEFENCES RENDERING ----------- 
    def render_defence_tabs(self, defences):
        # defences rows: (defence_id, defence_type, essay_question)
        tabs = []
        for _, defence_type, _ in defences:
            # make safe ID (lowercase, spaces → hyphens)
            safe_id = defence_type.lower().replace(" ", "-")
            tabs.append(
                f'<button class="btn"onclick="openTab(\'{safe_id}\')">{defence_type.title()}</button> ')
        return "".join(tabs)
    
    def render_defence_sections(self, db: "DefenceDatabase", defences):
        sections = []
        for _, defence_type, _ in defences:
            safe_id = defence_type.lower().replace(" ", "-")
            laws = DataFetcher.fetch_law_by_defence(db,defence_type)
            law_list = "".join(
                f"<li><strong>{cn}</strong>: {cl}</li>\n"
                for (cn, cl) in laws
            )
            # first section is active by default
            sections.append(f"""
        <section id="{safe_id}" class="tab-content defence-section">
            <h2>{defence_type.title()}</h2>
            <ul>{law_list}</ul>
        </section>
            """)
        return "".join(sections)
    
    # ----------- QUIZZES RENDERING ----------- 
    def render_quiz_section(self, quizzes):
        tabs = []
        for _, quiz_title in quizzes:
            # make safe ID (lowercase, spaces → hyphens)
            safe_id = quiz_title.lower().replace(" ", "-")
            tabs.append(
                f'<button class="btn"onclick="openTab(\'{safe_id}\')">{quiz_title.title()}</button> ')
        return "".join(tabs)

    def render_quiz_question(self, quiz_data):
        blocks = []
        for idx, (q_text, answers) in enumerate(quiz_data, start=1):
            answer_items = "".join(
                f'<li><label><input type="radio" name="q{idx}" value={a_text}> {a_text}</label></li>'
                for (a_text, _) in answers
            )
            blocks.append(f"""
                <div class="quiz-question">
                    <h4>Q{idx}. {q_text}</h4>
                    <ul class="answers">{answer_items}</ul>
                </div>
            """)
        return "".join(blocks)
    
    def render_quiz_results(self, score_value, total_questions):
        return f"""
            <div class="quiz-results">
                <h3>Your Score: {score_value}/{total_questions}</h3>
            </div>
        """

    # ---------- USER RENDERING -----------
    def render_user_accounts(self, users):
        rows = "".join(
            f"<tr><td>{user_id}</td><td>{name}</td><td>{email}</td></tr>"
            for (user_id, name, email) in users
        )
        return f"""
            <table class="user-table">
                <thead><tr><th>ID</th><th>Name</th><th>Email</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        """

    # ----------- SCORE RENDERING -----------
    def render_scores(self, scores):
        rows = "".join(
            f"<tr><td>{score_id}</td><td>{user_id}</td><td>{quiz_id}</td><td>{score_value}</td><td>{date_taken}</td></tr>"
            for (score_id, user_id, quiz_id, score_value, date_taken) in scores
        )
        return f"""
            <table class="score-table">
                <thead><tr><th>Score ID</th><th>User ID</th><th>Quiz ID</th><th>Score</th><th>Date Taken</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        """

    def calculate_score(user_answers, quiz_data):
        """
        user_answers: dict {question_index: chosen_answer_text}
        quiz_data: [(question_text, [(answer_text, is_correct), ...]), ...]
        """
        score = 0
        for idx, (q_text, answers) in enumerate(quiz_data, start=1):
            chosen = user_answers.get(idx)
            for a_text, is_correct in answers:
                if chosen == a_text and is_correct:
                    score += 1
        return score
    
# ---------------------------------------------------------
# Link database and website together
# ---------------------------------------------------------
class LoadWebsite:
    def __init__(self, db_name: str, web_file: str):
        self.db = DefenceDatabase(db_name)
        self.website_file = Website_Code(web_file)
        self.execute_queries = DataFetcher()

    def generate_html(self, output_file: str = "index.html"):
        template = self.website_file.load_website()
        defences = self.execute_queries.fetch_all_defences()
        quiz_amount = self.execute_queries.fetch_quiz()

        # Render site parts
        tabs_html = self.website_file.render_defence_tabs(defences)
        sections_html = self.website_file.render_defence_sections(self.db, defences)
        quiz_html = self.website_file.render_quiz_section(quiz_amount)
        quiz = [] 
        for quiz_id in quiz_html:
            quiz_data = self.execute_queries.fetch_quiz_with_questions_answers(quiz_id)
            quiz.append(quiz_data)
        quizz_html = self.website_file.render_quiz_section(quiz_data)

        final_html = (
            template.replace("{{tabs}}", tabs_html)
            .replace("{{defence_section}}", sections_html)
            .replace("{{quizzes-tabs}}", quiz_html)
            .replace("{{quiz-sections}}", quizz_html)
        )

        with codecs.open(output_file, "w", encoding="utf-8") as file:
            file.write(final_html)
        print(f"Website generated: {output_file}")
        
        self.db.close_db()



class WebsiteServer(BaseHTTPRequestHandler):
    pass