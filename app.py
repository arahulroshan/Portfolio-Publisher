from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
import qrcode
from io import BytesIO
from flask import send_file
app = Flask(__name__)
import os
from google import genai
gemini_client = genai.Client()


# Secret key for session
app.secret_key = "portfolio-publisher-secret-key"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():

    conn = sqlite3.connect("portfolio.db")

    conn.row_factory = sqlite3.Row

    return conn



# =========================================================
# CREATE DATABASE
# =========================================================

def init_db():

    conn = get_db()

    try:
        conn.execute(
            "ALTER TABLE themes ADD COLUMN font_style TEXT DEFAULT 'Outfit'"
        )
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute(
            "ALTER TABLE themes ADD COLUMN background_style TEXT DEFAULT 'purple'"
        )
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute(
            "ALTER TABLE profiles ADD COLUMN profile_image TEXT"
    )
    except sqlite3.OperationalError:
        pass

    # ---------------- USERS TABLE ----------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE NOT NULL,

            email TEXT NOT NULL,

            password TEXT NOT NULL

        )
    """)
    # Add publish status to existing users table

    try:
        conn.execute(
            "ALTER TABLE users ADD COLUMN is_published INTEGER DEFAULT 0"
    )
    except sqlite3.OperationalError:
        pass


    # ---------------- PROFILES TABLE ----------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER UNIQUE NOT NULL,

            full_name TEXT,

            phone TEXT,

            location TEXT,

            about TEXT,

            profile_image TEXT,

            FOREIGN KEY (user_id) REFERENCES users(id)

        )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS experience (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        company TEXT,

        role TEXT,

        start_date TEXT,

        end_date TEXT,

        description TEXT,

        FOREIGN KEY (user_id) REFERENCES users(id)

    )
""")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS social_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            linkedin TEXT,
            github TEXT,
            email TEXT,
            portfolio TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # ---------------- EDUCATION TABLE ----------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS education (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            degree TEXT,

            institution TEXT,

            year TEXT,

            grade TEXT,

            FOREIGN KEY (user_id) REFERENCES users(id)

        )
    """)


    # ---------------- SKILLS TABLE ----------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS skills (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            skill_name TEXT NOT NULL,

            FOREIGN KEY (user_id) REFERENCES users(id)

        )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS certificates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        certificate_name TEXT NOT NULL,
        issuing_organization TEXT,
        issue_date TEXT,
        certificate_link TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            resume_file TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    try:
        conn.execute("""
        
            ALTER TABLE certificates
            ADD COLUMN certificate_image TEXT
        """)
    except sqlite3.OperationalError:
        pass


    # ---------------- PROJECTS TABLE ----------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            project_name TEXT NOT NULL,

            description TEXT,

            technologies TEXT,

            github_link TEXT,

            live_link TEXT,

            project_image TEXT,

            FOREIGN KEY (user_id) REFERENCES users(id)

        )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS project_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        image_name TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )
""")
        # ---------------- SOCIAL LINKS TABLE ----------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS social_links (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER UNIQUE NOT NULL,

            linkedin TEXT,

            github TEXT,

            email TEXT,

            portfolio TEXT,

            FOREIGN KEY (user_id) REFERENCES users(id)

        )
    """)
    # ---------------- THEMES TABLE ----------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS themes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER UNIQUE NOT NULL,

            theme_color TEXT DEFAULT '#8b5cf6',

            background_color TEXT DEFAULT '#080612',

            font_style TEXT DEFAULT 'Outfit',

            background_style TEXT DEFAULT 'purple',

           FOREIGN KEY (user_id) REFERENCES users(id)

      )
    """)


    conn.commit()

    conn.close()


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]

        email = request.form["email"]

        password = request.form["password"]

        confirm_password = request.form["confirm_password"]


        # Check password

        if password != confirm_password:

            return "Passwords do not match!"


        # Hash password

        hashed_password = generate_password_hash(password)


        try:

            conn = get_db()


            conn.execute(
                """
                INSERT INTO users
                (
                    username,
                    email,
                    password
                )
                VALUES (?, ?, ?)
                """,
                (
                    username,
                    email,
                    hashed_password
                )
            )


            conn.commit()

            conn.close()


            return redirect(url_for("login"))


        except sqlite3.IntegrityError:

            return "Username already exists!"


    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]


        conn = get_db()


        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()


        conn.close()


        # Check login

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            session["username"] = user["username"]


            return redirect(url_for("dashboard"))


        return "Invalid username or password!"


    return render_template("login.html")


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile", methods=["GET", "POST"])
def profile():

    # Login check
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        full_name = request.form["full_name"]
        phone = request.form["phone"]
        location = request.form["location"]
        about = request.form["about"]

        # Profile image
        profile_image = request.files.get("profile_image")

        image_filename = None

        if profile_image and profile_image.filename:

            image_filename = profile_image.filename

            upload_folder = os.path.join(
                "static",
                "images",
                "profiles"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            profile_image.save(
                os.path.join(
                    upload_folder,
                    image_filename
                )
            )

        conn = get_db()

        # Keep old image if no new image is uploaded
        if image_filename:

            conn.execute(
                """
                INSERT OR REPLACE INTO profiles
                (
                    user_id,
                    full_name,
                    phone,
                    location,
                    about,
                    profile_image
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session["user_id"],
                    full_name,
                    phone,
                    location,
                    about,
                    image_filename
                )
            )

        else:

            conn.execute(
                """
                INSERT OR REPLACE INTO profiles
                (
                    user_id,
                    full_name,
                    phone,
                    location,
                    about
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session["user_id"],
                    full_name,
                    phone,
                    location,
                    about
                )
            )

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("profile.html")
@app.route("/experience", methods=["GET", "POST"])
def experience():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    if request.method == "POST":

        company = request.form["company"]
        role = request.form["role"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        description = request.form["description"]

        conn.execute(
            """
            INSERT INTO experience
            (
                user_id,
                company,
                role,
                start_date,
                end_date,
                description
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                company,
                role,
                start_date,
                end_date,
                description
            )
        )

        conn.commit()

    experiences = conn.execute(
        """
        SELECT *
        FROM experience
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "experience.html",
        experiences=experiences
    )
# =========================================================
# EDUCATION
# =========================================================

@app.route("/education", methods=["GET", "POST"])
def education():

    # Login check

    if "user_id" not in session:

        return redirect(url_for("login"))


    if request.method == "POST":

        degree = request.form["degree"]

        institution = request.form["institution"]

        year = request.form["year"]

        grade = request.form["grade"]


        conn = get_db()


        conn.execute(
            """
            INSERT INTO education
            (
                user_id,
                degree,
                institution,
                year,
                grade
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                degree,
                institution,
                year,
                grade
            )
        )


        conn.commit()

        conn.close()


        return redirect(url_for("dashboard"))


    return render_template("education.html")


# =========================================================
# PROJECTS
# =========================================================

@app.route("/projects", methods=["GET", "POST"])
def projects():

    # Login check
    if "user_id" not in session:
        return redirect(url_for("login"))

    # ---------------- ADD PROJECT ----------------

    if request.method == "POST":

        project_name = request.form["project_name"]
        description = request.form["description"]
        technologies = request.form["technologies"]
        github_link = request.form["github_link"]
        live_link = request.form["live_link"]

        # ---------------- MAIN PROJECT IMAGE ----------------

        project_image = request.files.get("project_image")

        image_filename = None

        if project_image and project_image.filename != "":

            image_filename = project_image.filename

            project_image.save(
                "static/images/projects/" + image_filename
            )

        # ---------------- SAVE PROJECT ----------------

        conn = get_db()

        cursor = conn.execute(
            """
            INSERT INTO projects
            (
                user_id,
                project_name,
                description,
                technologies,
                github_link,
                live_link,
                project_image
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                project_name,
                description,
                technologies,
                github_link,
                live_link,
                image_filename
            )
        )

        # Get newly created project ID
        project_id = cursor.lastrowid

        # ---------------- MULTIPLE SCREENSHOTS ----------------

        project_images = request.files.getlist("project_images")

        for image in project_images:

            if image and image.filename != "":

                image_filename = image.filename

                image.save(
                    "static/images/projects/" + image_filename
                )

                conn.execute(
                    """
                    INSERT INTO project_images
                    (
                        project_id,
                        image_name
                    )
                    VALUES (?, ?)
                    """,
                    (
                        project_id,
                        image_filename
                    )
                )

        conn.commit()
        conn.close()

        return redirect(url_for("projects"))

    # ---------------- GET PROJECTS ----------------

    conn = get_db()

    projects = conn.execute(
        """
        SELECT *
        FROM projects
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    # ---------------- GET PROJECT SCREENSHOTS ----------------

    project_images = conn.execute(
        """
        SELECT *
        FROM project_images
        WHERE project_id IN (
            SELECT id
            FROM projects
            WHERE user_id = ?
        )
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "projects.html",
        projects=projects,
        project_images=project_images
    )
# =========================================================
# DELETE PROJECT
# =========================================================

@app.route("/delete-project/<int:project_id>")
def delete_project(project_id):

    # Login check

    if "user_id" not in session:

        return redirect(url_for("login"))


    conn = get_db()


    conn.execute(
        """
        DELETE FROM projects
        WHERE id = ? AND user_id = ?
        """,
        (
            project_id,
            session["user_id"]
        )
    )


    conn.commit()

    conn.close()


    return redirect(url_for("projects"))


# =========================================================
# EDIT PROJECT
# =========================================================

@app.route("/edit-project/<int:project_id>", methods=["GET", "POST"])
def edit_project(project_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    project = conn.execute(
        """
        SELECT *
        FROM projects
        WHERE id = ? AND user_id = ?
        """,
        (project_id, session["user_id"])
    ).fetchone()

    if not project:
        conn.close()
        return "Project not found!"

    if request.method == "POST":

        project_name = request.form["project_name"]
        description = request.form["description"]
        technologies = request.form["technologies"]
        github_link = request.form["github_link"]
        live_link = request.form["live_link"]

        project_image = request.files.get("project_image")

        image_filename = project["project_image"]

        if project_image and project_image.filename != "":
            image_filename = project_image.filename

            project_image.save(
                "static/images/projects/" + image_filename
            )

        conn.execute(
            """
            UPDATE projects
            SET
                project_name = ?,
                description = ?,
                technologies = ?,
                github_link = ?,
                live_link = ?,
                project_image = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                project_name,
                description,
                technologies,
                github_link,
                live_link,
                image_filename,
                project_id,
                session["user_id"]
            )
        )

        conn.commit()
        conn.close()

        return redirect(url_for("projects"))

    conn.close()

    return render_template(
        "edit_project.html",
        project=project
    )
# =========================================================
# PROJECT DETAILS
# =========================================================

@app.route("/project/<int:project_id>")
def project_details(project_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    project = conn.execute(
        """
        SELECT *
        FROM projects
        WHERE id = ? AND user_id = ?
        """,
        (project_id, session["user_id"])
    ).fetchone()

    conn.close()

    if not project:
        return "Project not found!"

    return render_template(
        "project_details.html",
        project=project
    )
    

@app.route("/portfolio")
def public_portfolio():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    profile = conn.execute(
        """
        SELECT *
        FROM profiles
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    education = conn.execute(
        """
        SELECT *
        FROM education
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    skills = conn.execute(
        """
        SELECT *
        FROM skills
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    projects = conn.execute(
        """
        SELECT *
        FROM projects
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    certificates = conn.execute(
        """
        SELECT *
        FROM certificates
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()
    theme = conn.execute(
        """
        SELECT *
        FROM themes
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchone()
    resume = conn.execute(
        """
        SELECT *
        FROM resumes
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (session["user_id"],)
    ).fetchone()


    social = conn.execute(
        """
        SELECT *
        FROM social_links
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return render_template(
        "public_portfolio.html",
        profile=profile,
        education=education,
        skills=skills,
        projects=projects,
        certificates=certificates,
        resume=resume,
        social=social,
        theme=theme,
        experiences=experiences
    )
# =========================================================
# PUBLIC PORTFOLIO BY USERNAME
# =========================================================


@app.route("/portfolio/<username>")
def public_portfolio_by_username(username):

    conn = get_db()

    print("USERNAME FROM URL:", username)

    # Find user
    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE LOWER(username) = LOWER(?)
        """,
        (username,)
    ).fetchone()

    print("USER FOUND:", dict(user) if user else None)

    # User not found
    if not user:

        conn.close()

        return "Portfolio not found!"


    # =====================================================
    # CHECK PUBLISH STATUS
    # =====================================================

    if user["is_published"] != 1:

        conn.close()

        return """
        <!DOCTYPE html>

        <html>

        <head>

            <title>Portfolio Not Published</title>

        </head>

        <body
            style="
                background:#050509;
                color:white;
                text-align:center;
                font-family:Arial;
                padding-top:120px;
            "
        >

            <h1>
                🔒 This Portfolio is Not Published
            </h1>

            <p style="color:#aaa;">
                The portfolio owner has not published
                this portfolio yet.
            </p>

        </body>

        </html>
        """


    # =====================================================
    # USER ID
    # =====================================================

    user_id = user["id"]


    # =====================================================
    # PROFILE
    # =====================================================

    profile = conn.execute(
        """
        SELECT *
        FROM profiles
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()


    # =====================================================
    # EDUCATION
    # =====================================================

    education = conn.execute(
        """
        SELECT *
        FROM education
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()


    # =====================================================
    # SKILLS
    # =====================================================

    skills = conn.execute(
        """
        SELECT *
        FROM skills
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()


    # =====================================================
    # PROJECTS
    # =====================================================

    projects = conn.execute(
        """
        SELECT *
        FROM projects
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()


    # =====================================================
    # CERTIFICATES
    # =====================================================

    certificates = conn.execute(
        """
        SELECT *
        FROM certificates
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()


    # =====================================================
    # RESUME
    # =====================================================

    resume = conn.execute(
        """
        SELECT *
        FROM resumes
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id,)
    ).fetchone()


    # =====================================================
    # SOCIAL LINKS
    # =====================================================

    social = conn.execute(
        """
        SELECT *
        FROM social_links
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()


    # =====================================================
    # THEME
    # =====================================================

    theme = conn.execute(
        """
        SELECT *
        FROM themes
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()


    # =====================================================
    # EXPERIENCE
    # =====================================================

    experiences = conn.execute(
        """
        SELECT *
        FROM experience
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()


    print(
        "EXPERIENCES:",
        [dict(exp) for exp in experiences]
    )


    # Close database
    conn.close()


    # =====================================================
    # SHOW PUBLIC PORTFOLIO
    # =====================================================

    return render_template(
        "public_portfolio.html",

        profile=profile,

        education=education,

        skills=skills,

        projects=projects,

        certificates=certificates,

        resume=resume,

        social=social,

        theme=theme,

        experiences=experiences
    )
# =========================================================
# PUBLISH / UNPUBLISH PORTFOLIO
# =========================================================

@app.route("/publish-portfolio", methods=["GET", "POST"])
def publish_portfolio():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    if request.method == "POST":

        action = request.form["action"]

        if action == "publish":

            conn.execute(
                """
                UPDATE users
                SET is_published = 1
                WHERE id = ?
                """,
                (session["user_id"],)
            )

        elif action == "unpublish":

            conn.execute(
                """
                UPDATE users
                SET is_published = 0
                WHERE id = ?
                """,
                (session["user_id"],)
            )

        conn.commit()

    user = conn.execute(
        """
        SELECT username, is_published
        FROM users
        WHERE id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    conn.close()

    if not user:
        return "User not found!"

    portfolio_url = url_for(
        "public_portfolio_by_username",
        username=user["username"],
        _external=True
    )

    return render_template(
        "publish_portfolio.html",
        username=user["username"],
        portfolio_url=portfolio_url,
        is_published=user["is_published"]
    )
# =========================================================
# GENERATE PORTFOLIO QR CODE
# =========================================================

@app.route("/portfolio-qr/<username>")
def generate_portfolio_qr(username):

    conn = get_db()

    user = conn.execute(
        """
        SELECT username, is_published
        FROM users
        WHERE LOWER(username) = LOWER(?)
        """,
        (username,)
    ).fetchone()

    conn.close()

    if not user:
        return "User not found!", 404

    if user["is_published"] != 1:
        return "Portfolio is not published yet!", 403

    portfolio_url = url_for(
        "public_portfolio_by_username",
        username=user["username"],
        _external=True
    )

    qr = qrcode.make(portfolio_url)

    qr_image = BytesIO()
    qr.save(qr_image, format="PNG")
    qr_image.seek(0)

    return send_file(
        qr_image,
        mimetype="image/png",
        download_name="portfolio_qr.png"
    )
# =========================================================
# AI PORTFOLIO CHATBOT - GEMINI AI + CHAT HISTORY
# =========================================================


# =========================================================
# CHAT HISTORY
# =========================================================

@app.route("/chat-history", methods=["GET"])
def chat_history():

    if "user_id" not in session:
        return {"error": "Please login first."}, 401

    conn = get_db()

    chats = conn.execute(
        """
        SELECT id, title, created_at, updated_at
        FROM chat_sessions
        WHERE user_id = ?
        ORDER BY updated_at DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return {
        "chats": [dict(chat) for chat in chats]
    }


@app.route("/chat-history/<int:chat_id>", methods=["GET"])
def get_chat_history(chat_id):

    if "user_id" not in session:
        return {"error": "Please login first."}, 401

    conn = get_db()

    chat = conn.execute(
        """
        SELECT id, title
        FROM chat_sessions
        WHERE id = ?
        AND user_id = ?
        """,
        (chat_id, session["user_id"])
    ).fetchone()

    if not chat:
        conn.close()
        return {"error": "Chat not found."}, 404

    messages = conn.execute(
        """
        SELECT role, message, created_at
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY id ASC
        """,
        (chat_id,)
    ).fetchall()

    conn.close()

    return {
        "chat": dict(chat),
        "messages": [dict(message) for message in messages]
    }
# =========================================================
# AI PORTFOLIO CHATBOT
# =========================================================

@app.route("/chatbot")
def chatbot():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("chatbot.html")


@app.route("/ai-chat", methods=["POST"])
def ai_chat():

    if "user_id" not in session:
        return {
            "reply": "Please login first.",
            "chat_id": None
        }, 401

    data = request.get_json()

    user_message = data.get("message", "").strip()
    chat_id = data.get("chat_id")

    if not user_message:
        return {
            "reply": "Please enter a message.",
            "chat_id": chat_id
        }, 400

    conn = None

    try:

        conn = get_db()

        # =================================================
        # CREATE CHAT TABLES
        # =================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT DEFAULT 'New Chat',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()

        # =================================================
        # CREATE / CHECK CHAT
        # =================================================

        if chat_id:

            chat = conn.execute(
                """
                SELECT id
                FROM chat_sessions
                WHERE id = ?
                AND user_id = ?
                """,
                (chat_id, session["user_id"])
            ).fetchone()

            if not chat:
                chat_id = None

        if not chat_id:

            cursor = conn.execute(
                """
                INSERT INTO chat_sessions
                (user_id, title)
                VALUES (?, ?)
                """,
                (session["user_id"], "New Chat")
            )

            chat_id = cursor.lastrowid

            conn.commit()

        # =================================================
        # SAVE USER MESSAGE
        # =================================================

        conn.execute(
            """
            INSERT INTO chat_messages
            (session_id, role, message)
            VALUES (?, ?, ?)
            """,
            (chat_id, "user", user_message)
        )

        conn.commit()

        # =================================================
        # GET PREVIOUS CHAT
        # =================================================

        previous_messages = conn.execute(
            """
            SELECT role, message
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id ASC
            LIMIT 30
            """,
            (chat_id,)
        ).fetchall()

        conversation = ""

        for msg in previous_messages:

            if msg["role"] == "user":
                conversation += f"User: {msg['message']}\n"

            else:
                conversation += f"Assistant: {msg['message']}\n"

        # =================================================
        # GET PORTFOLIO DATA
        # =================================================

        user_id = session["user_id"]

        user = conn.execute(
            """
            SELECT username, email
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        profile = conn.execute(
            """
            SELECT *
            FROM profiles
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

        education = conn.execute(
            """
            SELECT *
            FROM education
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchall()

        skills = conn.execute(
            """
            SELECT *
            FROM skills
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchall()

        projects = conn.execute(
            """
            SELECT *
            FROM projects
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchall()

        certificates = conn.execute(
            """
            SELECT *
            FROM certificates
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchall()

        experiences = conn.execute(
            """
            SELECT *
            FROM experience
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchall()

        # =================================================
        # GEMINI PROMPT
        # =================================================

        prompt = f"""
You are an AI Portfolio Assistant inside a Portfolio Publisher website.

You are helping the logged-in portfolio owner.

Answer the user's question clearly and naturally.

IMPORTANT:
-You can answer general questions also, but never treat a suggested career field or example as the user's actual interest unless the user explicitly says so.
- For personal portfolio information, use the portfolio data provided below.
- Do not invent personal information.
- NEVER guess or assume any personal information.
- Use only the portfolio data and information explicitly provided by the user.
- If the requested personal information is unavailable, say "This information is not available in your portfolio."
- If a personal detail is not available, say that it is not available.
- Be helpful and concise.
- You can help with resume, projects, skills, certificates,
  education, experience, portfolio improvement and AI/ML/Data Science topics.

PORTFOLIO DATA:

Username:
{user["username"] if user else "Not available"}

Email:
{user["email"] if user else "Not available"}

Profile:
{dict(profile) if profile else "Not available"}

Education:
{[dict(x) for x in education]}

Skills:
{[dict(x) for x in skills]}

Projects:
{[dict(x) for x in projects]}

Certificates:
{[dict(x) for x in certificates]}

Experience:
{[dict(x) for x in experiences]}

PREVIOUS CONVERSATION:

{conversation}

CURRENT USER MESSAGE:

{user_message}

Give the best possible answer.
"""

        # =================================================
        # GEMINI AI
        # =================================================

        response = gemini_client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt
        )

        reply = response.text

        # =================================================
        # SAVE AI RESPONSE
        # =================================================

        conn.execute(
            """
            INSERT INTO chat_messages
            (session_id, role, message)
            VALUES (?, ?, ?)
            """,
            (chat_id, "assistant", reply)
        )

        # =================================================
        # UPDATE CHAT TITLE
        # =================================================

        current_chat = conn.execute(
            """
            SELECT title
            FROM chat_sessions
            WHERE id = ?
            """,
            (chat_id,)
        ).fetchone()

        if current_chat and current_chat["title"] == "New Chat":

            title = user_message[:40]

            conn.execute(
                """
                UPDATE chat_sessions
                SET title = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (title, chat_id)
            )

        else:

            conn.execute(
                """
                UPDATE chat_sessions
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (chat_id,)
            )

        conn.commit()

        return {
            "reply": reply,
            "chat_id": chat_id
        }

    except Exception as e:

        print("Gemini Error:", e)

        return {
            "reply": "Sorry, something went wrong while connecting to the AI. Please try again.",
            "chat_id": chat_id
        }, 500

    finally:

        if conn:
            conn.close()

    

# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    # Login check

    if "user_id" not in session:

        return redirect(url_for("login"))


    return render_template(
        "dashboard.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()


    return redirect(url_for("login"))


# =========================================================
# SKILLS
# =========================================================
@app.route("/skills", methods=["GET", "POST"])
def skills():

    # Login check

    if "user_id" not in session:

        return redirect(url_for("login"))


    if request.method == "POST":

        skill_name = request.form["skill_name"]

        conn = get_db()

        conn.execute(
            """
            INSERT INTO skills
            (
                user_id,
                skill_name
            )
            VALUES (?, ?)
            """,
            (
                session["user_id"],
                skill_name
            )
        )

        conn.commit()

        conn.close()

        return redirect(url_for("dashboard"))


    # Get saved skills

    conn = get_db()

    skills = conn.execute(
        """
        SELECT *
        FROM skills
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "skills.html",
        skills=skills
    )
@app.route("/certificates", methods=["GET", "POST"])
def certificates():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        certificate_name = request.form["certificate_name"]
        issuing_organization = request.form["issuing_organization"]
        issue_date = request.form["issue_date"]
        certificate_link = request.form["certificate_link"]

        certificate_image = request.files.get("certificate_image")

        image_filename = None

        if certificate_image and certificate_image.filename:

            image_filename = certificate_image.filename

            upload_folder = "static/images/certificates"

            os.makedirs(upload_folder, exist_ok=True)

            certificate_image.save(
                os.path.join(upload_folder, image_filename)
            )

        conn = get_db()

        conn.execute(
            """
            INSERT INTO certificates
            (
                user_id,
                certificate_name,
                issuing_organization,
                issue_date,
                certificate_link,
                certificate_image
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                certificate_name,
                issuing_organization,
                issue_date,
                certificate_link,
                image_filename
            )
        )

        conn.commit()
        conn.close()

        return redirect(url_for("certificates"))

    conn = get_db()

    certificates = conn.execute(
        """
        SELECT *
        FROM certificates
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "certificates.html",
        certificates=certificates
    )
@app.route("/delete-certificate/<int:certificate_id>")
def delete_certificate(certificate_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    conn.execute(
        """
        DELETE FROM certificates
        WHERE id = ? AND user_id = ?
        """,
        (certificate_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("certificates"))
@app.route("/delete-skill/<int:skill_id>")
def delete_skill(skill_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    conn.execute(
        """
        DELETE FROM skills
        WHERE id = ? AND user_id = ?
        """,
        (skill_id, session["user_id"])
    )

    conn.commit()
    conn.close()
# =========================================================
# EDIT CERTIFICATE
# =========================================================

@app.route("/edit-certificate/<int:certificate_id>", methods=["GET", "POST"])
def edit_certificate(certificate_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    certificate = conn.execute(
        """
        SELECT *
        FROM certificates
        WHERE id = ? AND user_id = ?
        """,
        (
            certificate_id,
            session["user_id"]
        )
    ).fetchone()

    if not certificate:
        conn.close()
        return "Certificate not found!"

    if request.method == "POST":

        certificate_name = request.form["certificate_name"]
        issuing_organization = request.form["issuing_organization"]
        issue_date = request.form["issue_date"]
        certificate_link = request.form["certificate_link"]

        conn.execute(
            """
            UPDATE certificates
            SET
                certificate_name = ?,
                issuing_organization = ?,
                issue_date = ?,
                certificate_link = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                certificate_name,
                issuing_organization,
                issue_date,
                certificate_link,
                certificate_id,
                session["user_id"]
            )
        )

        conn.commit()
        conn.close()

        return redirect(url_for("certificates"))

    conn.close()

    return render_template(
        "edit_certificate.html",
        certificate=certificate
    )
# =========================================================
# RESUME
# =========================================================

@app.route("/resume", methods=["GET", "POST"])
def resume():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    if request.method == "POST":

        resume_file = request.files.get("resume_file")

        if resume_file and resume_file.filename:

            upload_folder = "static/images/resumes"

            os.makedirs(upload_folder, exist_ok=True)

            filename = resume_file.filename

            resume_file.save(
                os.path.join(upload_folder, filename)
            )

            # Remove old resume record
            conn.execute(
                """
                DELETE FROM resumes
                WHERE user_id = ?
                """,
                (session["user_id"],)
            )

            # Save new resume
            conn.execute(
                """
                INSERT INTO resumes
                (user_id, resume_file)
                VALUES (?, ?)
                """,
                (
                    session["user_id"],
                    filename
                )
            )

            conn.commit()

        conn.close()

        return redirect(url_for("resume"))

    resume = conn.execute(
        """
        SELECT *
        FROM resumes
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return render_template(
        "resume.html",
        resume=resume
    )

# =========================================================
# SOCIAL LINKS
# =========================================================

@app.route("/social-links", methods=["GET", "POST"])
def social_links():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    if request.method == "POST":

        linkedin = request.form["linkedin"]
        github = request.form["github"]
        email = request.form["email"]
        portfolio = request.form["portfolio"]

        existing = conn.execute(
            """
            SELECT *
            FROM social_links
            WHERE user_id = ?
            """,
            (session["user_id"],)
        ).fetchone()

        if existing:

            conn.execute(
                """
                UPDATE social_links
                SET linkedin = ?,
                    github = ?,
                    email = ?,
                    portfolio = ?
                WHERE user_id = ?
                """,
                (
                    linkedin,
                    github,
                    email,
                    portfolio,
                    session["user_id"]
                )
            )

        else:

            conn.execute(
                """
                INSERT INTO social_links
                (
                    user_id,
                    linkedin,
                    github,
                    email,
                    portfolio
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session["user_id"],
                    linkedin,
                    github,
                    email,
                    portfolio
                )
            )

        conn.commit()

        conn.close()

        return redirect(url_for("social_links"))

    social = conn.execute(
        """
        SELECT *
        FROM social_links
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return render_template(
        "social_links.html",
        social=social
    )
@app.route("/theme-settings", methods=["GET", "POST"])
def theme_settings():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    if request.method == "POST":

        theme_color = request.form["theme_color"]
        background_color = request.form["background_color"]
        font_style = request.form["font_style"]
        background_style = request.form["background_style"]
        existing = conn.execute(
            """
            SELECT *
            FROM themes
            WHERE user_id = ?
            """,
            (session["user_id"],)
        ).fetchone()

        if existing:

            conn.execute(
                """
                UPDATE themes
SET theme_color = ?,
    background_color = ?,
    font_style = ?,
    background_style = ?
WHERE user_id = ?
                """,
                (
    theme_color,
    background_color,
    font_style,
    background_style,
    session["user_id"]
)
            )

        else:

            conn.execute(
                """
                INSERT INTO themes
(
    user_id,
    theme_color,
    background_color,
    font_style,
    background_style
)
VALUES (?, ?, ?, ?, ?)
                """,
                (
    session["user_id"],
    theme_color,
    background_color,
    font_style,
    background_style
)
            )

        conn.commit()
        conn.close()

        return redirect(url_for("theme_settings"))

    theme = conn.execute(
        """
        SELECT *
        FROM themes
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return render_template(
        "theme_settings.html",
        theme=theme
    )
# =========================================================
# DELETE RESUME
# =========================================================

@app.route("/delete-resume")
def delete_resume():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    conn.execute(
        """
        DELETE FROM resumes
        WHERE user_id = ?
        """,
        (session["user_id"],)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("resume"))
    return redirect(url_for("skills"))
@app.route("/edit-skill/<int:skill_id>", methods=["GET", "POST"])
def edit_skill(skill_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    skill = conn.execute(
        """
        SELECT *
        FROM skills
        WHERE id = ? AND user_id = ?
        """,
        (skill_id, session["user_id"])
    ).fetchone()

    if not skill:
        conn.close()
        return "Skill not found!"

    if request.method == "POST":

        skill_name = request.form["skill_name"]

        conn.execute(
            """
            UPDATE skills
            SET skill_name = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                skill_name,
                skill_id,
                session["user_id"]
            )
        )

        conn.commit()
        conn.close()

        return redirect(url_for("skills"))

    conn.close()

    return render_template(
        "edit_skill.html",
        skill=skill
    )

# =========================================================
# RUN APPLICATION
# =========================================================

# Initialize database when the application starts
init_db()


if __name__ == "__main__":
    app.run(debug=True)