from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from werkzeug.security import generate_password_hash, check_password_hash
import qrcode
from io import BytesIO
from flask import send_file
app = Flask(__name__)
from google import genai
gemini_client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
)



# Secret key for session
app.secret_key = "portfolio-publisher-secret-key"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    conn = psycopg2.connect(
        os.environ.get("DATABASE_URL"),
        connect_timeout=10
    )
    return conn


def init_db():

    conn = get_db()
    cursor = conn.cursor()

    # =====================================================
    # USERS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            is_published INTEGER DEFAULT 0
        )
    """)


    # =====================================================
    # PROFILES
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,
            full_name TEXT,
            phone TEXT,
            location TEXT,
            about TEXT,
            profile_image TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


    # =====================================================
    # EXPERIENCE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experience (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            company TEXT,
            role TEXT,
            start_date TEXT,
            end_date TEXT,
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


    # =====================================================
    # SOCIAL LINKS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS social_links (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,
            linkedin TEXT,
            github TEXT,
            email TEXT,
            portfolio TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


    # =====================================================
    # EDUCATION
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS education (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            degree TEXT,
            institution TEXT,
            year TEXT,
            grade TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


    # =====================================================
    # SKILLS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            skill_name TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


    # =====================================================
    # CERTIFICATES
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            certificate_name TEXT,
            issuing_organization TEXT,
            issue_date TEXT,
            certificate_link TEXT,
            certificate_image TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


    # =====================================================
    # RESUMES
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            resume_file TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


    # =====================================================
    # PROJECTS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            project_name TEXT,
            description TEXT,
            technologies TEXT,
            github_link TEXT,
            live_link TEXT,
            project_image TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


    # =====================================================
    # PROJECT IMAGES
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_images (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL,
            image_name TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)


    # =====================================================
    # THEMES
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS themes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,
            theme_color TEXT DEFAULT '#8b5cf6',
            background_color TEXT DEFAULT '#080612',
            font_style TEXT DEFAULT 'Outfit',
            background_style TEXT DEFAULT 'purple',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


    # =====================================================
    # CHAT SESSIONS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT DEFAULT 'New Chat',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


    # =====================================================
    # CHAT MESSAGES
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
        )
    """)


    # =====================================================
    # SAVE CHANGES
    # =====================================================

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

        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Passwords do not match!"

        if not username or not email or not password:
            return "All fields are required!"

        hashed_password = generate_password_hash(password)

        conn = None

        try:

            conn = get_db()
            cursor = conn.cursor()

            # Check existing username
            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE LOWER(TRIM(username)) = LOWER(TRIM(%s))
                LIMIT 1
                """,
                (username,)
            )

            existing_user = cursor.fetchone()

            if existing_user:
                conn.close()
                return "Username already exists!"

            # Insert user
            cursor.execute(
                """
                INSERT INTO users
                (
                    username,
                    email,
                    password
                )
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (
                    username,
                    email,
                    hashed_password
                )
            )

            new_user = cursor.fetchone()

            conn.commit()

            print("REGISTER SUCCESS")
            print("NEW USER ID:", new_user[0])
            print("NEW USERNAME:", username)

            conn.close()

            return redirect(url_for("login"))

        except Exception as e:

            print("REGISTER ERROR:", repr(e))

            if conn:
                conn.rollback()
                conn.close()

            return "Registration failed. Check terminal for the database error."

    return render_template("register.html")
@app.route("/login", methods=["GET", "POST"])
def login():

    print("LOGIN ROUTE HIT")

    if request.method == "POST":

        print("LOGIN POST HIT")

        username = request.form["username"].strip()
        password = request.form["password"]

        print("LOGIN USERNAME:", repr(username))

        conn = None

        try:
            conn = get_db()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute(
                """
                SELECT id, username, password
                FROM users
                WHERE LOWER(TRIM(username)) = LOWER(TRIM(%s))
                LIMIT 1
                """,
                (username,)
            )

            user = cursor.fetchone()

            print("LOGIN DB RESULT:", user)

            if user is None:
                print("USER NOT FOUND")
                return "Invalid username or password"

            if not check_password_hash(user["password"], password):
                print("PASSWORD INVALID")
                return "Invalid username or password"

            # Login successful
            session.clear()

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            print("LOGIN SUCCESS")
            print("SESSION USER ID:", session["user_id"])
            print("SESSION USERNAME:", session["username"])

            return redirect(url_for("dashboard"))

        except Exception as e:

            print("LOGIN ERROR:", e)

            return "Login failed. Please try again."

        finally:

            if conn:
                conn.close()

    return render_template("login.html")
# =========================================================
# PROFILE
# =========================================================

@app.route("/profile", methods=["GET", "POST"])
def profile():

    # =====================================================
    # LOGIN CHECK
    # =====================================================

    if "user_id" not in session:
        return redirect(url_for("login"))


    # =====================================================
    # SAVE / UPDATE PROFILE
    # =====================================================

    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        about = request.form.get(
            "about",
            ""
        ).strip()


        # =================================================
        # PROFILE IMAGE
        # =================================================

        profile_image = request.files.get(
            "profile_image"
        )

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


        # =================================================
        # DATABASE CONNECTION
        # =================================================

        conn = get_db()

        cursor = conn.cursor()


        # =================================================
        # UPDATE WITH NEW IMAGE
        # =================================================

        if image_filename:

            cursor.execute(
                """
                INSERT INTO profiles
                (
                    user_id,
                    full_name,
                    phone,
                    location,
                    about,
                    profile_image
                )
                VALUES (%s, %s, %s, %s, %s, %s)

                ON CONFLICT (user_id)
                DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    phone = EXCLUDED.phone,
                    location = EXCLUDED.location,
                    about = EXCLUDED.about,
                    profile_image = EXCLUDED.profile_image
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


        # =================================================
        # UPDATE WITHOUT CHANGING OLD IMAGE
        # =================================================

        else:

            cursor.execute(
                """
                INSERT INTO profiles
                (
                    user_id,
                    full_name,
                    phone,
                    location,
                    about
                )
                VALUES (%s, %s, %s, %s, %s)

                ON CONFLICT (user_id)
                DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    phone = EXCLUDED.phone,
                    location = EXCLUDED.location,
                    about = EXCLUDED.about
                """,
                (
                    session["user_id"],
                    full_name,
                    phone,
                    location,
                    about
                )
            )


        # =================================================
        # SAVE CHANGES
        # =================================================

        conn.commit()

        conn.close()


        # =================================================
        # GO TO DASHBOARD
        # =================================================

        return redirect(
            url_for("dashboard")
        )


    # =====================================================
    # PROFILE PAGE
    # =====================================================

    return render_template(
        "profile.html"
    )
# =========================================================
# EXPERIENCE
# =========================================================

@app.route("/experience", methods=["GET", "POST"])
def experience():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )

    # =====================================================
    # ADD EXPERIENCE
    # =====================================================

    if request.method == "POST":

        company = request.form["company"].strip()
        role = request.form["role"].strip()
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        description = request.form["description"].strip()

        cursor.execute(
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
            VALUES (%s, %s, %s, %s, %s, %s)
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


    # =====================================================
    # GET EXPERIENCE
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM experience
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (session["user_id"],)
    )

    experiences = cursor.fetchall()

    conn.close()

    return render_template(
        "experience.html",
        experiences=experiences
    )


# =========================================================
# EDIT EXPERIENCE
# =========================================================

@app.route(
    "/edit-experience/<int:experience_id>",
    methods=["GET", "POST"]
)
def edit_experience(experience_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    # =====================================================
    # GET EXPERIENCE
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM experience
        WHERE id = %s
          AND user_id = %s
        """,
        (
            experience_id,
            session["user_id"]
        )
    )

    experience = cursor.fetchone()


    # =====================================================
    # NOT FOUND
    # =====================================================

    if not experience:

        conn.close()

        return "Experience not found!", 404


    # =====================================================
    # UPDATE EXPERIENCE
    # =====================================================

    if request.method == "POST":

        company = request.form["company"].strip()
        role = request.form["role"].strip()
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        description = request.form["description"].strip()

        cursor.execute(
            """
            UPDATE experience
            SET
                company = %s,
                role = %s,
                start_date = %s,
                end_date = %s,
                description = %s
            WHERE id = %s
              AND user_id = %s
            """,
            (
                company,
                role,
                start_date,
                end_date,
                description,
                experience_id,
                session["user_id"]
            )
        )

        conn.commit()

        conn.close()

        return redirect(
            url_for("experience")
        )


    # =====================================================
    # EDIT PAGE
    # =====================================================

    conn.close()

    return render_template(
        "edit_experience.html",
        experience=experience
    )


# =========================================================
# DELETE EXPERIENCE
# =========================================================

@app.route(
    "/delete-experience/<int:experience_id>",
    methods=["POST"]
)
def delete_experience(experience_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM experience
        WHERE id = %s
          AND user_id = %s
        """,
        (
            experience_id,
            session["user_id"]
        )
    )

    conn.commit()

    conn.close()

    return redirect(
        url_for("experience")
    )
## =========================================================
# EDUCATION
# =========================================================

@app.route("/education", methods=["GET", "POST"])
def education():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()


    # =====================================================
    # ADD EDUCATION
    # =====================================================

    if request.method == "POST":

        degree = request.form.get(
            "degree",
            ""
        ).strip()

        institution = request.form.get(
            "institution",
            ""
        ).strip()

        year = request.form.get(
            "year",
            ""
        ).strip()

        grade = request.form.get(
            "grade",
            ""
        ).strip()


        cursor.execute(
            """
            INSERT INTO education
            (
                user_id,
                degree,
                institution,
                year,
                grade
            )
            VALUES (%s, %s, %s, %s, %s)
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

        return redirect(
            url_for("education")
        )


    # =====================================================
    # GET EDUCATION
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM education
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (
            session["user_id"],
        )
    )

    educations = cursor.fetchall()

    conn.close()


    # =====================================================
    # DISPLAY EDUCATION
    # =====================================================

    return render_template(
        "education.html",
        educations=educations
    )
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

        project_name = request.form.get(
            "project_name", ""
        ).strip()

        description = request.form.get(
            "description", ""
        ).strip()

        technologies = request.form.get(
            "technologies", ""
        ).strip()

        github_link = request.form.get(
            "github_link", ""
        ).strip()

        live_link = request.form.get(
            "live_link", ""
        ).strip()


        # ---------------- MAIN PROJECT IMAGE ----------------

        project_image = request.files.get(
            "project_image"
        )

        image_filename = None

        if project_image and project_image.filename != "":

            image_filename = project_image.filename

            upload_folder = os.path.join(
                "static",
                "images",
                "projects"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            project_image.save(
                os.path.join(
                    upload_folder,
                    image_filename
                )
            )


        # ---------------- DATABASE ----------------

        conn = get_db()

        cursor = conn.cursor(
            cursor_factory=RealDictCursor
        )


        # ---------------- SAVE PROJECT ----------------

        cursor.execute(
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
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
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

        new_project = cursor.fetchone()

        project_id = new_project["id"]


        # ---------------- MULTIPLE SCREENSHOTS ----------------

        project_images = request.files.getlist(
            "project_images"
        )

        for image in project_images:

            if image and image.filename != "":

                gallery_filename = image.filename

                upload_folder = os.path.join(
                    "static",
                    "images",
                    "projects"
                )

                os.makedirs(
                    upload_folder,
                    exist_ok=True
                )

                image.save(
                    os.path.join(
                        upload_folder,
                        gallery_filename
                    )
                )

                cursor.execute(
                    """
                    INSERT INTO project_images
                    (
                        project_id,
                        image_name
                    )
                    VALUES (%s, %s)
                    """,
                    (
                        project_id,
                        gallery_filename
                    )
                )


        conn.commit()
        conn.close()

        return redirect(
            url_for("projects")
        )


    # ---------------- GET PROJECTS ----------------

    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    cursor.execute(
        """
        SELECT *
        FROM projects
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (
            session["user_id"],
        )
    )

    projects_list = cursor.fetchall()


    # ---------------- GET PROJECT SCREENSHOTS ----------------

    cursor.execute(
        """
        SELECT *
        FROM project_images
        WHERE project_id IN (
            SELECT id
            FROM projects
            WHERE user_id = %s
        )
        ORDER BY id DESC
        """,
        (
            session["user_id"],
        )
    )

    project_images = cursor.fetchall()

    conn.close()


    return render_template(
        "projects.html",
        projects=projects_list,
        project_images=project_images
    )


# =========================================================
# DELETE PROJECT
# =========================================================

@app.route(
    "/delete-project/<int:project_id>",
    methods=["POST", "GET"]
)
def delete_project(project_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    cursor = conn.cursor()


    # Delete screenshots belonging to this project
    cursor.execute(
        """
        DELETE FROM project_images
        WHERE project_id = %s
        AND project_id IN (
            SELECT id
            FROM projects
            WHERE id = %s
            AND user_id = %s
        )
        """,
        (
            project_id,
            project_id,
            session["user_id"]
        )
    )


    # Delete project
    cursor.execute(
        """
        DELETE FROM projects
        WHERE id = %s
        AND user_id = %s
        """,
        (
            project_id,
            session["user_id"]
        )
    )


    conn.commit()
    conn.close()

    return redirect(
        url_for("projects")
    )


# =========================================================
# EDIT PROJECT
# =========================================================

@app.route(
    "/edit-project/<int:project_id>",
    methods=["GET", "POST"]
)
def edit_project(project_id):

    if "user_id" not in session:
        return redirect(url_for("login"))


    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    # ---------------- GET PROJECT ----------------

    cursor.execute(
        """
        SELECT *
        FROM projects
        WHERE id = %s
        AND user_id = %s
        """,
        (
            project_id,
            session["user_id"]
        )
    )

    project = cursor.fetchone()


    if not project:

        conn.close()

        return "Project not found!", 404


    # ---------------- UPDATE PROJECT ----------------

    if request.method == "POST":

        project_name = request.form.get(
            "project_name", ""
        ).strip()

        description = request.form.get(
            "description", ""
        ).strip()

        technologies = request.form.get(
            "technologies", ""
        ).strip()

        github_link = request.form.get(
            "github_link", ""
        ).strip()

        live_link = request.form.get(
            "live_link", ""
        ).strip()


        project_image = request.files.get(
            "project_image"
        )


        # Keep old image
        image_filename = project["project_image"]


        # New image uploaded
        if project_image and project_image.filename != "":

            image_filename = project_image.filename

            upload_folder = os.path.join(
                "static",
                "images",
                "projects"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            project_image.save(
                os.path.join(
                    upload_folder,
                    image_filename
                )
            )


        cursor.execute(
            """
            UPDATE projects
            SET
                project_name = %s,
                description = %s,
                technologies = %s,
                github_link = %s,
                live_link = %s,
                project_image = %s
            WHERE id = %s
            AND user_id = %s
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

        return redirect(
            url_for("projects")
        )


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

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    # ---------------- GET PROJECT ----------------

    cursor.execute(
        """
        SELECT *
        FROM projects
        WHERE id = %s
        AND user_id = %s
        """,
        (
            project_id,
            session["user_id"]
        )
    )

    project = cursor.fetchone()


    if not project:

        conn.close()

        return "Project not found!", 404


    # ---------------- GET PROJECT SCREENSHOTS ----------------

    cursor.execute(
        """
        SELECT *
        FROM project_images
        WHERE project_id = %s
        ORDER BY id DESC
        """,
        (
            project_id,
        )
    )

    project_images = cursor.fetchall()


    conn.close()


    return render_template(
        "project_details.html",
        project=project,
        project_images=project_images
    )
@app.route("/portfolio")
def public_portfolio():

    if "user_id" not in session:
        return redirect(url_for("login"))


    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    profile = cursor.execute(
        """
        SELECT *
        FROM profiles
        WHERE user_id = %s
        """,
        (session["user_id"],)
    ).fetchone()

    education = cursor.execute(
        """
        SELECT *
        FROM education
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    skills = cursor.execute(
        """
        SELECT *
        FROM skills
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    projects = cursor.execute(
        """
        SELECT *
        FROM projects
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    certificates = cursor.execute(
        """
        SELECT *
        FROM certificates
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    theme = cursor.execute(
        """
        SELECT *
        FROM themes
        WHERE user_id = %s
        """,
        (session["user_id"],)
    ).fetchone()

    resume = cursor.execute(
        """
        SELECT *
        FROM resumes
        WHERE user_id = %s
        ORDER BY id DESC
        LIMIT 1
        """,
        (session["user_id"],)
    ).fetchone()

    social = cursor.execute(
        """
        SELECT *
        FROM social_links
        WHERE user_id = %s
        """,
        (session["user_id"],)
    ).fetchone()

    experiences = cursor.execute(
        """
        SELECT *
        FROM experience
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

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
# CERTIFICATES
# =========================================================

# =========================================================
# CERTIFICATES
# =========================================================

@app.route("/certificates", methods=["GET", "POST"])
def certificates():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )

    # =====================================================
    # ADD CERTIFICATE
    # =====================================================

    if request.method == "POST":

        certificate_name = request.form["certificate_name"].strip()
        issuing_organization = request.form["issuing_organization"].strip()
        issue_date = request.form["issue_date"]
        certificate_link = request.form["certificate_link"].strip()

        certificate_image = request.files.get(
            "certificate_image"
        )

        image_filename = None

        if certificate_image and certificate_image.filename:

            upload_folder = "static/images/certificates"

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            image_filename = certificate_image.filename

            certificate_image.save(
                os.path.join(
                    upload_folder,
                    image_filename
                )
            )

        cursor.execute(
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
            VALUES (%s, %s, %s, %s, %s, %s)
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

        return redirect(
            url_for("certificates")
        )


    # =====================================================
    # GET CERTIFICATES
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM certificates
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (session["user_id"],)
    )

    certificates_list = cursor.fetchall()

    conn.close()


    # =====================================================
    # SHOW CERTIFICATES
    # =====================================================

    return render_template(
        "certificates.html",
        certificates=certificates_list
    )
# =========================================================
# PUBLIC PORTFOLIO BY USERNAME
# =========================================================

# =========================================================
# PUBLIC PORTFOLIO BY USERNAME
# =========================================================

@app.route("/portfolio/<username>")
def public_portfolio_by_username(username):

    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )

    print("USERNAME FROM URL:", username)


    # =====================================================
    # FIND USER
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE LOWER(username) = LOWER(%s)
        """,
        (username,)
    )

    user = cursor.fetchone()

    print(
        "USER FOUND:",
        dict(user) if user else None
    )


    # =====================================================
    # USER NOT FOUND
    # =====================================================

    if not user:

        conn.close()

        return "Portfolio not found!", 404


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

    cursor.execute(
        """
        SELECT *
        FROM profiles
        WHERE user_id = %s
        """,
        (user_id,)
    )

    profile = cursor.fetchone()


    # =====================================================
    # EDUCATION
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM education
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (user_id,)
    )

    education = cursor.fetchall()


    # =====================================================
    # SKILLS
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM skills
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (user_id,)
    )

    skills = cursor.fetchall()


    # =====================================================
    # PROJECTS
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM projects
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (user_id,)
    )

    projects = cursor.fetchall()


    # =====================================================
    # PROJECT IMAGES
    # =====================================================

    cursor.execute(
        """
        SELECT pi.*
        FROM project_images pi
        INNER JOIN projects p
            ON pi.project_id = p.id
        WHERE p.user_id = %s
        ORDER BY pi.id DESC
        """,
        (user_id,)
    )

    project_images = cursor.fetchall()


    # =====================================================
    # CERTIFICATES
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM certificates
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (user_id,)
    )

    certificates = cursor.fetchall()


    # =====================================================
    # EXPERIENCE
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM experience
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (user_id,)
    )

    experiences = cursor.fetchall()


    # =====================================================
    # RESUME
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM resumes
        WHERE user_id = %s
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id,)
    )

    resume = cursor.fetchone()


    # =====================================================
    # SOCIAL LINKS
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM social_links
        WHERE user_id = %s
        """,
        (user_id,)
    )

    social = cursor.fetchone()


    # =====================================================
    # THEME
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM themes
        WHERE user_id = %s
        """,
        (user_id,)
    )

    theme = cursor.fetchone()


    # =====================================================
    # CLOSE DATABASE
    # =====================================================

    conn.close()


    # =====================================================
    # SHOW PUBLIC PORTFOLIO
    # =====================================================

    return render_template(
        "public_portfolio.html",

        user=user,

        profile=profile,

        education=education,

        skills=skills,

        projects=projects,

        project_images=project_images,

        certificates=certificates,

        experiences=experiences,

        resume=resume,

        social=social,

        theme=theme
    
    )
# =========================================================
# PUBLISH / UNPUBLISH PORTFOLIO
# =========================================================

@app.route("/publish-portfolio", methods=["GET", "POST"])
def publish_portfolio():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    # =====================================================
    # PUBLISH / UNPUBLISH
    # =====================================================

    if request.method == "POST":

        action = request.form["action"]

        if action == "publish":

            cursor.execute(
                """
                UPDATE users
                SET is_published = 1
                WHERE id = %s
                """,
                (session["user_id"],)
            )

        elif action == "unpublish":

            cursor.execute(
                """
                UPDATE users
                SET is_published = 0
                WHERE id = %s
                """,
                (session["user_id"],)
            )

        conn.commit()


    # =====================================================
    # GET USER STATUS
    # =====================================================

    cursor.execute(
        """
        SELECT username, is_published
        FROM users
        WHERE id = %s
        """,
        (session["user_id"],)
    )

    user = cursor.fetchone()

    conn.close()


    if not user:
        return "User not found!", 404


    # =====================================================
    # PUBLIC PORTFOLIO URL
    # =====================================================

    portfolio_url = url_for(
        "public_portfolio_by_username",
        username=user[0],
        _external=True
    )


    return render_template(
        "publish_portfolio.html",
        username=user[0],
        portfolio_url=portfolio_url,
        is_published=user[1]
    )
## =========================================================
# GENERATE PORTFOLIO QR CODE
# =========================================================

@app.route("/portfolio-qr/<username>")
def generate_portfolio_qr(username):

    conn = get_db()
    cursor = conn.cursor()

    # =====================================================
    # GET USER
    # =====================================================

    cursor.execute(
        """
        SELECT username, is_published
        FROM users
        WHERE LOWER(username) = LOWER(%s)
        """,
        (username,)
    )

    user = cursor.fetchone()

    conn.close()


    # =====================================================
    # USER CHECK
    # =====================================================

    if not user:
        return "User not found!", 404


    # =====================================================
    # PUBLISHED CHECK
    # =====================================================

    if user[1] != 1:
        return "Portfolio is not published yet!", 403


    # =====================================================
    # PORTFOLIO URL
    # =====================================================

    portfolio_url = url_for(
        "public_portfolio_by_username",
        username=user[0],
        _external=True
    )


    # =====================================================
    # GENERATE QR CODE
    # =====================================================

    qr = qrcode.make(portfolio_url)

    qr_image = BytesIO()

    qr.save(
        qr_image,
        format="PNG"
    )

    qr_image.seek(0)


    # =====================================================
    # SEND QR IMAGE
    # =====================================================

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

# =========================================================
# CHAT HISTORY
# =========================================================

@app.route("/chat-history", methods=["GET"])
def chat_history():

    if "user_id" not in session:
        return {"error": "Please login first."}, 401

    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )

    cursor.execute(
        """
        SELECT id, title, created_at, updated_at
        FROM chat_sessions
        WHERE user_id = %s
        ORDER BY updated_at DESC
        """,
        (
            session["user_id"],
        )
    )

    chats = cursor.fetchall()

    conn.close()

    return {
        "chats": [dict(chat) for chat in chats]
    }

# =========================================================
# GET ONE CHAT HISTORY
# =========================================================

@app.route("/chat-history/<int:chat_id>", methods=["GET"])
def get_chat_history(chat_id):

    if "user_id" not in session:
        return {"error": "Please login first."}, 401

    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )

    # Get chat
    cursor.execute(
        """
        SELECT id, title
        FROM chat_sessions
        WHERE id = %s
          AND user_id = %s
        """,
        (
            chat_id,
            session["user_id"]
        )
    )

    chat = cursor.fetchone()

    if not chat:

        conn.close()

        return {
            "error": "Chat not found."
        }, 404


    # Get messages
    cursor.execute(
        """
        SELECT role, message, created_at
        FROM chat_messages
        WHERE session_id = %s
        ORDER BY id ASC
        """,
        (
            chat_id,
        )
    )

    messages = cursor.fetchall()

    conn.close()

    return {
        "chat": dict(chat),
        "messages": [dict(message) for message in messages]
    }
# =========================================================
# AI PORTFOLIO CHATBOT PAGE
# =========================================================

@app.route("/chatbot")
def chatbot():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "chatbot.html"
    )
# =========================================================
# AI PORTFOLIO CHATBOT
# =========================================================

@app.route("/ai-chat", methods=["POST"])
def ai_chat():

    if "user_id" not in session:
        return {
            "reply": "Please login first.",
            "chat_id": None
        }, 401


    data = request.get_json() or {}

    user_message = data.get(
        "message",
        ""
    ).strip()

    chat_id = data.get("chat_id")


    if not user_message:
        return {
            "reply": "Please enter a message.",
            "chat_id": chat_id
        }, 400


    conn = None

    try:

        # =================================================
        # DATABASE
        # =================================================

        conn = get_db()

        cursor = conn.cursor(
            cursor_factory=RealDictCursor
        )


        # =================================================
        # CREATE / CHECK CHAT
        # =================================================

        if chat_id:

            cursor.execute(
                """
                SELECT id
                FROM chat_sessions
                WHERE id = %s
                  AND user_id = %s
                """,
                (
                    chat_id,
                    session["user_id"]
                )
            )

            chat = cursor.fetchone()

            if not chat:
                chat_id = None


        # =================================================
        # CREATE NEW CHAT
        # =================================================

        if not chat_id:

            cursor.execute(
                """
                INSERT INTO chat_sessions
                (
                    user_id,
                    title
                )
                VALUES (%s, %s)
                RETURNING id
                """,
                (
                    session["user_id"],
                    "New Chat"
                )
            )

            new_chat = cursor.fetchone()

            chat_id = new_chat["id"]

            conn.commit()


        # =================================================
        # SAVE USER MESSAGE
        # =================================================

        cursor.execute(
            """
            INSERT INTO chat_messages
            (
                session_id,
                role,
                message
            )
            VALUES (%s, %s, %s)
            """,
            (
                chat_id,
                "user",
                user_message
            )
        )

        conn.commit()


        # =================================================
        # GET PREVIOUS CHAT
        # =================================================

        cursor.execute(
            """
            SELECT role, message
            FROM chat_messages
            WHERE session_id = %s
            ORDER BY id ASC
            LIMIT 30
            """,
            (
                chat_id,
            )
        )

        previous_messages = cursor.fetchall()


        conversation = ""

        for msg in previous_messages:

            if msg["role"] == "user":

                conversation += (
                    f"User: {msg['message']}\n"
                )

            else:

                conversation += (
                    f"Assistant: {msg['message']}\n"
                )


        # =================================================
        # GET PORTFOLIO DATA
        # =================================================

        user_id = session["user_id"]


        # USER
        cursor.execute(
            """
            SELECT username, email
            FROM users
            WHERE id = %s
            """,
            (
                user_id,
            )
        )

        user = cursor.fetchone()


        # PROFILE
        cursor.execute(
            """
            SELECT *
            FROM profiles
            WHERE user_id = %s
            """,
            (
                user_id,
            )
        )

        profile = cursor.fetchone()


        # EDUCATION
        cursor.execute(
            """
            SELECT *
            FROM education
            WHERE user_id = %s
            """,
            (
                user_id,
            )
        )

        education = cursor.fetchall()


        # SKILLS
        cursor.execute(
            """
            SELECT *
            FROM skills
            WHERE user_id = %s
            """,
            (
                user_id,
            )
        )

        skills = cursor.fetchall()


        # PROJECTS
        cursor.execute(
            """
            SELECT *
            FROM projects
            WHERE user_id = %s
            """,
            (
                user_id,
            )
        )

        projects = cursor.fetchall()


        # CERTIFICATES
        cursor.execute(
            """
            SELECT *
            FROM certificates
            WHERE user_id = %s
            """,
            (
                user_id,
            )
        )

        certificates = cursor.fetchall()


        # EXPERIENCE
        cursor.execute(
            """
            SELECT *
            FROM experience
            WHERE user_id = %s
            """,
            (
                user_id,
            )
        )

        experiences = cursor.fetchall()


        # =================================================
        # GEMINI PROMPT
        # =================================================

        prompt = f"""
You are an AI Portfolio Assistant inside a Portfolio Publisher website.

You are helping the logged-in portfolio owner.

Answer the user's question clearly and naturally.

IMPORTANT:

- You can answer general questions also.
- Never treat a suggested career field or example as the user's actual interest unless the user explicitly says so.
- For personal portfolio information, use the portfolio data provided below.
- Do not invent personal information.
- NEVER guess or assume any personal information.
- Use only the portfolio data and information explicitly provided by the user.
- If the requested personal information is unavailable, say:
  "This information is not available in your portfolio."
- Be helpful and concise.
- You can help with resume, projects, skills, certificates,
  education, experience, portfolio improvement and
  AI/ML/Data Science topics.


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

        cursor.execute(
            """
            INSERT INTO chat_messages
            (
                session_id,
                role,
                message
            )
            VALUES (%s, %s, %s)
            """,
            (
                chat_id,
                "assistant",
                reply
            )
        )


        # =================================================
        # UPDATE CHAT TITLE
        # =================================================

        cursor.execute(
            """
            SELECT title
            FROM chat_sessions
            WHERE id = %s
            """,
            (
                chat_id,
            )
        )

        current_chat = cursor.fetchone()


        if (
            current_chat
            and current_chat["title"] == "New Chat"
        ):

            title = user_message[:40]

            cursor.execute(
                """
                UPDATE chat_sessions
                SET
                    title = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    title,
                    chat_id
                )
            )

        else:

            cursor.execute(
                """
                UPDATE chat_sessions
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    chat_id,
                )
            )


        conn.commit()


        # =================================================
        # SUCCESS
        # =================================================

        return {
            "reply": reply,
            "chat_id": chat_id
        }


    except Exception as e:

        print(
            "Gemini Error:",
            e
        )

        if conn:
            conn.rollback()

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

    # =====================================================
    # LOGIN CHECK
    # =====================================================

    if "user_id" not in session:
        return redirect(url_for("login"))


    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    # =====================================================
    # ADD SKILL
    # =====================================================

    if request.method == "POST":

        skill_name = request.form.get(
            "skill_name",
            ""
        ).strip()


        if skill_name:

            cursor.execute(
                """
                INSERT INTO skills
                (
                    user_id,
                    skill_name
                )
                VALUES (%s, %s)
                """,
                (
                    session["user_id"],
                    skill_name
                )
            )

            conn.commit()


        conn.close()

        return redirect(
            url_for("skills")
        )


    # =====================================================
    # GET SAVED SKILLS
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM skills
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (
            session["user_id"],
        )
    )

    skills_list = cursor.fetchall()

    conn.close()


    # =====================================================
    # DISPLAY SKILLS
    # =====================================================

    return render_template(
        "skills.html",
        skills=skills_list
    )
# =========================================================
# DELETE CERTIFICATE
# =========================================================

@app.route("/delete-certificate/<int:certificate_id>")
def delete_certificate(certificate_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM certificates
        WHERE id = %s AND user_id = %s
        """,
        (
            certificate_id,
            session["user_id"]
        )
    )

    conn.commit()
    conn.close()

    return redirect(url_for("certificates"))


# =========================================================
# DELETE SKILL
# =========================================================

@app.route("/delete-skill/<int:skill_id>")
def delete_skill(skill_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM skills
        WHERE id = %s AND user_id = %s
        """,
        (
            skill_id,
            session["user_id"]
        )
    )

    conn.commit()
    conn.close()

    return redirect(url_for("skills"))


# =========================================================
# EDIT CERTIFICATE
# =========================================================

@app.route(
    "/edit-certificate/<int:certificate_id>",
    methods=["GET", "POST"]
)
def edit_certificate(certificate_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    # =====================================================
    # GET CERTIFICATE
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM certificates
        WHERE id = %s AND user_id = %s
        """,
        (
            certificate_id,
            session["user_id"]
        )
    )

    certificate = cursor.fetchone()


    # =====================================================
    # CERTIFICATE NOT FOUND
    # =====================================================

    if not certificate:

        conn.close()

        return "Certificate not found!", 404


    # =====================================================
    # UPDATE CERTIFICATE
    # =====================================================

    if request.method == "POST":

        certificate_name = request.form[
            "certificate_name"
        ].strip()

        issuing_organization = request.form[
            "issuing_organization"
        ].strip()

        issue_date = request.form[
            "issue_date"
        ]

        certificate_link = request.form[
            "certificate_link"
        ].strip()


        cursor.execute(
            """
            UPDATE certificates
            SET
                certificate_name = %s,
                issuing_organization = %s,
                issue_date = %s,
                certificate_link = %s
            WHERE id = %s
              AND user_id = %s
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

        return redirect(
            url_for("certificates")
        )


    # =====================================================
    # EDIT PAGE
    # =====================================================

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

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    # =====================================================
    # UPLOAD RESUME
    # =====================================================

    if request.method == "POST":

        resume_file = request.files.get(
            "resume_file"
        )

        if resume_file and resume_file.filename:

            upload_folder = "static/images/resumes"

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            filename = resume_file.filename

            resume_file.save(
                os.path.join(
                    upload_folder,
                    filename
                )
            )


            # ---------------------------------------------
            # REMOVE OLD RESUME RECORD
            # ---------------------------------------------

            cursor.execute(
                """
                DELETE FROM resumes
                WHERE user_id = %s
                """,
                (
                    session["user_id"],
                )
            )


            # ---------------------------------------------
            # SAVE NEW RESUME
            # ---------------------------------------------

            cursor.execute(
                """
                INSERT INTO resumes
                (
                    user_id,
                    resume_file
                )
                VALUES (%s, %s)
                """,
                (
                    session["user_id"],
                    filename
                )
            )

            conn.commit()


        conn.close()

        return redirect(
            url_for("resume")
        )


    # =====================================================
    # GET CURRENT RESUME
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM resumes
        WHERE user_id = %s
        ORDER BY id DESC
        LIMIT 1
        """,
        (
            session["user_id"],
        )
    )

    resume_data = cursor.fetchone()

    conn.close()


    # =====================================================
    # SHOW RESUME
    # =====================================================

    return render_template(
        "resume.html",
        resume=resume_data
    )
# =========================================================
# SOCIAL LINKS
# =========================================================

@app.route("/social-links", methods=["GET", "POST"])
def social_links():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    # =====================================================
    # SAVE / UPDATE SOCIAL LINKS
    # =====================================================

    if request.method == "POST":

        linkedin = request.form.get(
            "linkedin",
            ""
        ).strip()

        github = request.form.get(
            "github",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        portfolio = request.form.get(
            "portfolio",
            ""
        ).strip()


        # =================================================
        # CHECK EXISTING
        # =================================================

        cursor.execute(
            """
            SELECT *
            FROM social_links
            WHERE user_id = %s
            """,
            (
                session["user_id"],
            )
        )

        existing = cursor.fetchone()


        # =================================================
        # UPDATE
        # =================================================

        if existing:

            cursor.execute(
                """
                UPDATE social_links
                SET
                    linkedin = %s,
                    github = %s,
                    email = %s,
                    portfolio = %s
                WHERE user_id = %s
                """,
                (
                    linkedin,
                    github,
                    email,
                    portfolio,
                    session["user_id"]
                )
            )


        # =================================================
        # INSERT
        # =================================================

        else:

            cursor.execute(
                """
                INSERT INTO social_links
                (
                    user_id,
                    linkedin,
                    github,
                    email,
                    portfolio
                )
                VALUES (%s, %s, %s, %s, %s)
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

        return redirect(
            url_for("social_links")
        )


    # =====================================================
    # GET SOCIAL LINKS
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM social_links
        WHERE user_id = %s
        """,
        (
            session["user_id"],
        )
    )

    social = cursor.fetchone()

    conn.close()


    # =====================================================
    # SHOW SOCIAL LINKS
    # =====================================================

    return render_template(
        "social_links.html",
        social=social
    )

# =========================================================
# THEME SETTINGS
# =========================================================

@app.route("/theme-settings", methods=["GET", "POST"])
def theme_settings():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    # =====================================================
    # SAVE / UPDATE THEME
    # =====================================================

    if request.method == "POST":

        theme_color = request.form.get(
            "theme_color",
            ""
        ).strip()

        background_color = request.form.get(
            "background_color",
            ""
        ).strip()

        font_style = request.form.get(
            "font_style",
            ""
        ).strip()

        background_style = request.form.get(
            "background_style",
            ""
        ).strip()


        # =================================================
        # CHECK EXISTING THEME
        # =================================================

        cursor.execute(
            """
            SELECT *
            FROM themes
            WHERE user_id = %s
            """,
            (
                session["user_id"],
            )
        )

        existing = cursor.fetchone()


        # =================================================
        # UPDATE EXISTING THEME
        # =================================================

        if existing:

            cursor.execute(
                """
                UPDATE themes
                SET
                    theme_color = %s,
                    background_color = %s,
                    font_style = %s,
                    background_style = %s
                WHERE user_id = %s
                """,
                (
                    theme_color,
                    background_color,
                    font_style,
                    background_style,
                    session["user_id"]
                )
            )


        # =================================================
        # INSERT NEW THEME
        # =================================================

        else:

            cursor.execute(
                """
                INSERT INTO themes
                (
                    user_id,
                    theme_color,
                    background_color,
                    font_style,
                    background_style
                )
                VALUES (%s, %s, %s, %s, %s)
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

        return redirect(
            url_for("theme_settings")
        )


    # =====================================================
    # GET CURRENT THEME
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM themes
        WHERE user_id = %s
        """,
        (
            session["user_id"],
        )
    )

    theme = cursor.fetchone()

    conn.close()


    # =====================================================
    # DISPLAY THEME SETTINGS
    # =====================================================

    return render_template(
        "theme_settings.html",
        theme=theme
    )
# =========================================================
# DELETE RESUME
# =========================================================

# =========================================================
# DELETE RESUME
# =========================================================

@app.route("/delete-resume")
def delete_resume():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM resumes
        WHERE user_id = %s
        """,
        (session["user_id"],)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("resume"))


# =========================================================
# EDIT SKILL
# =========================================================

@app.route(
    "/edit-skill/<int:skill_id>",
    methods=["GET", "POST"]
)
def edit_skill(skill_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    cursor = conn.cursor(
        cursor_factory=RealDictCursor
    )


    # =====================================================
    # GET SKILL
    # =====================================================

    cursor.execute(
        """
        SELECT *
        FROM skills
        WHERE id = %s
          AND user_id = %s
        """,
        (
            skill_id,
            session["user_id"]
        )
    )

    skill = cursor.fetchone()


    # =====================================================
    # SKILL NOT FOUND
    # =====================================================

    if not skill:

        conn.close()

        return "Skill not found!", 404


    # =====================================================
    # UPDATE SKILL
    # =====================================================

    if request.method == "POST":

        skill_name = request.form.get(
            "skill_name",
            ""
        ).strip()


        if skill_name:

            cursor.execute(
                """
                UPDATE skills
                SET skill_name = %s
                WHERE id = %s
                  AND user_id = %s
                """,
                (
                    skill_name,
                    skill_id,
                    session["user_id"]
                )
            )

            conn.commit()


        conn.close()

        return redirect(
            url_for("skills")
        )


    # =====================================================
    # SHOW EDIT PAGE
    # =====================================================

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