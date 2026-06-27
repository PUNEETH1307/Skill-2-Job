"""
Master seed script for Skill2Job.
Populates: taxonomy, courses, companies, job roles, profiles,
           interviews, placements, notifications, shortlists.
Run:  python seed_all.py
Safe to re-run (idempotent).
"""
import json, sys, os
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import (
    User, SkillTaxonomy, CourseRecommendation,
    Company, JobRole, StudentProfile, Project,
    Shortlist, Interview, PlacementRecord, Notification,
)

# ── 1. SKILL TAXONOMY ───────────────────────────────────────────────────────
SKILLS = [
    # Programming Languages
    ("Python",       "Programming Languages", ["py","python3","Python3"]),
    ("JavaScript",   "Programming Languages", ["JS","js","javascript","ECMAScript"]),
    ("Java",         "Programming Languages", ["java","Java SE"]),
    ("C++",          "Programming Languages", ["cpp","c plus plus","cplusplus"]),
    ("C",            "Programming Languages", ["c language","clang"]),
    ("C#",           "Programming Languages", ["CSharp","c sharp","csharp"]),
    ("TypeScript",   "Programming Languages", ["TS","ts","typescript"]),
    ("Go",           "Programming Languages", ["golang","Golang"]),
    ("Ruby",         "Programming Languages", ["rb","ruby"]),
    ("PHP",          "Programming Languages", ["php"]),
    ("Kotlin",       "Programming Languages", ["kotlin"]),
    ("R",            "Programming Languages", ["R language","rlang"]),
    # Web & Frameworks
    ("React",        "Web & Frameworks", ["ReactJS","reactjs","react.js"]),
    ("Angular",      "Web & Frameworks", ["AngularJS","angularjs","angular"]),
    ("Vue.js",       "Web & Frameworks", ["VueJS","vuejs","vue"]),
    ("Django",       "Web & Frameworks", ["django","DRF"]),
    ("Flask",        "Web & Frameworks", ["flask"]),
    ("Spring Boot",  "Web & Frameworks", ["spring","springboot","Spring"]),
    ("Express.js",   "Web & Frameworks", ["express","expressjs"]),
    ("FastAPI",      "Web & Frameworks", ["fastapi"]),
    ("Node.js",      "Web & Frameworks", ["nodejs","node","NodeJS"]),
    ("Next.js",      "Web & Frameworks", ["nextjs","NextJS"]),
    ("Bootstrap",    "Web & Frameworks", ["bootstrap"]),
    ("TailwindCSS",  "Web & Frameworks", ["tailwind","tailwindcss"]),
    # Data & ML
    ("Machine Learning",   "Data & ML", ["ML","ml","machine-learning"]),
    ("Deep Learning",      "Data & ML", ["DL","dl","deep-learning"]),
    ("Data Science",       "Data & ML", ["DS","ds","data analytics"]),
    ("TensorFlow",         "Data & ML", ["tensorflow","tf"]),
    ("PyTorch",            "Data & ML", ["pytorch","torch"]),
    ("Pandas",             "Data & ML", ["pandas","pd"]),
    ("NumPy",              "Data & ML", ["numpy","np"]),
    ("Scikit-learn",       "Data & ML", ["sklearn","scikit learn"]),
    ("NLP",                "Data & ML", ["Natural Language Processing","text mining"]),
    ("Computer Vision",    "Data & ML", ["CV","cv","image processing"]),
    # Databases
    ("MySQL",      "Databases", ["mysql","sql"]),
    ("PostgreSQL", "Databases", ["Postgres","postgres","psql"]),
    ("MongoDB",    "Databases", ["Mongo","mongo","mongodb"]),
    ("Redis",      "Databases", ["redis"]),
    ("SQLite",     "Databases", ["sqlite","sqlite3"]),
    ("Oracle",     "Databases", ["oracle db","oracledb"]),
    # DevOps & Cloud
    ("Docker",      "DevOps & Cloud", ["docker"]),
    ("Kubernetes",  "DevOps & Cloud", ["K8s","k8s","kubernetes"]),
    ("AWS",         "DevOps & Cloud", ["Amazon Web Services","aws"]),
    ("Azure",       "DevOps & Cloud", ["Microsoft Azure","azure"]),
    ("GCP",         "DevOps & Cloud", ["Google Cloud","gcp"]),
    ("Git",         "DevOps & Cloud", ["git","github","GitHub"]),
    ("Linux",       "DevOps & Cloud", ["linux","ubuntu","bash"]),
    ("CI/CD",       "DevOps & Cloud", ["cicd","jenkins","github actions"]),
    # Soft Skills
    ("Communication",   "Soft Skills", ["communication skills"]),
    ("Leadership",      "Soft Skills", ["leadership skills"]),
    ("Teamwork",        "Soft Skills", ["team work","collaboration"]),
    ("Problem Solving", "Soft Skills", ["problem-solving","analytical thinking"]),
]

# ── 2. COURSES ───────────────────────────────────────────────────────────────
COURSES = [
    ("Python","Python for Everybody","Coursera","https://www.coursera.org/specializations/python"),
    ("Python","Complete Python Bootcamp","Udemy","https://www.udemy.com/course/complete-python-bootcamp/"),
    ("Python","Programming in Python","NPTEL","https://nptel.ac.in/courses/106106182"),
    ("Python","Python Full Course","YouTube","https://www.youtube.com/watch?v=_uQrJ0TkZlc"),
    ("JavaScript","The Complete JavaScript Course","Udemy","https://www.udemy.com/course/the-complete-javascript-course/"),
    ("JavaScript","JavaScript Crash Course","YouTube","https://www.youtube.com/watch?v=hdI2bqOjy3c"),
    ("React","React Basics by Meta","Coursera","https://www.coursera.org/learn/react-basics"),
    ("React","React - The Complete Guide","Udemy","https://www.udemy.com/course/react-the-complete-guide-incl-redux/"),
    ("React","React JS Full Course","YouTube","https://www.youtube.com/watch?v=bMknfKXIFA8"),
    ("Machine Learning","ML by Andrew Ng","Coursera","https://www.coursera.org/learn/machine-learning"),
    ("Machine Learning","Machine Learning A-Z","Udemy","https://www.udemy.com/course/machinelearning/"),
    ("Machine Learning","ML for Engineering","NPTEL","https://nptel.ac.in/courses/106106139"),
    ("Machine Learning","ML Full Course","YouTube","https://www.youtube.com/watch?v=GwIo3gDZCVQ"),
    ("Deep Learning","Deep Learning Specialization","Coursera","https://www.coursera.org/specializations/deep-learning"),
    ("Deep Learning","PyTorch for Deep Learning","Udemy","https://www.udemy.com/course/pytorch-for-deep-learning/"),
    ("Deep Learning","Deep Learning Full Course","YouTube","https://www.youtube.com/watch?v=aircAruvnKk"),
    ("Data Science","IBM Data Science Certificate","Coursera","https://www.coursera.org/professional-certificates/ibm-data-science"),
    ("Data Science","Data Science A-Z","Udemy","https://www.udemy.com/course/datascience/"),
    ("Data Science","Data Science Full Course","YouTube","https://www.youtube.com/watch?v=ua-CiDNNj30"),
    ("MySQL","MySQL for Beginners","Udemy","https://www.udemy.com/course/mysql-for-beginners/"),
    ("MySQL","Database Management Systems","NPTEL","https://nptel.ac.in/courses/106105175"),
    ("MySQL","MySQL Full Course","YouTube","https://www.youtube.com/watch?v=7S_tz1z_5bA"),
    ("Docker","Docker for Developers","Coursera","https://www.coursera.org/learn/docker-container"),
    ("Docker","Docker Mastery","Udemy","https://www.udemy.com/course/docker-mastery/"),
    ("Docker","Docker Tutorial","YouTube","https://www.youtube.com/watch?v=fqMOX6JJhGo"),
    ("AWS","AWS Cloud Practitioner Essentials","Coursera","https://www.coursera.org/learn/aws-cloud-practitioner-essentials"),
    ("AWS","Ultimate AWS Cloud Practitioner","Udemy","https://www.udemy.com/course/aws-certified-cloud-practitioner-new/"),
    ("AWS","AWS Full Course","YouTube","https://www.youtube.com/watch?v=k1RI5locZE4"),
    ("Kubernetes","Kubernetes for Beginners","Udemy","https://www.udemy.com/course/learn-kubernetes/"),
    ("Kubernetes","Kubernetes Tutorial","YouTube","https://www.youtube.com/watch?v=X48VuDVv0do"),
    ("Git","Version Control with Git","Coursera","https://www.coursera.org/learn/version-control-with-git"),
    ("Git","Git & GitHub Crash Course","YouTube","https://www.youtube.com/watch?v=RGOj5yH7evk"),
    ("Django","Django for Everybody","Coursera","https://www.coursera.org/specializations/django"),
    ("Django","Python Django Full Course","Udemy","https://www.udemy.com/course/python-and-django-full-stack-web-developer-bootcamp/"),
    ("Flask","Python Flask Bootcamp","Udemy","https://www.udemy.com/course/python-and-flask-bootcamp/"),
    ("Flask","Flask Tutorial","YouTube","https://www.youtube.com/watch?v=Z1RJmh_OqeA"),
    ("Node.js","Complete Node.js Developer Course","Udemy","https://www.udemy.com/course/the-complete-nodejs-developer-course-2/"),
    ("Node.js","Node.js Full Course","YouTube","https://www.youtube.com/watch?v=Oe421EPjeBE"),
    ("TypeScript","Understanding TypeScript","Udemy","https://www.udemy.com/course/understanding-typescript/"),
    ("TypeScript","TypeScript Full Course","YouTube","https://www.youtube.com/watch?v=BwuLxPH8IDs"),
    ("TensorFlow","TensorFlow Developer Certificate","Coursera","https://www.coursera.org/professional-certificates/tensorflow-in-practice"),
    ("TensorFlow","TensorFlow & Keras Bootcamp","Udemy","https://www.udemy.com/course/tensorflow-developer-certificate-machine-learning-zero-to-mastery/"),
    ("Linux","Linux Command Line Bootcamp","Udemy","https://www.udemy.com/course/the-linux-command-line-bootcamp/"),
    ("Linux","Linux Tutorial","YouTube","https://www.youtube.com/watch?v=sWbUDq4S6Y8"),
    ("CI/CD","Jenkins Complete Guide","Udemy","https://www.udemy.com/course/jenkins-from-zero-to-hero/"),
    ("CI/CD","GitHub Actions Full Course","YouTube","https://www.youtube.com/watch?v=R8_veQiYBjI"),
    ("MongoDB","MongoDB Complete Guide","Udemy","https://www.udemy.com/course/mongodb-the-complete-developers-guide/"),
    ("MongoDB","MongoDB Full Course","YouTube","https://www.youtube.com/watch?v=J6mDkcqU_ZE"),
    ("NLP","NLP with Python","Coursera","https://www.coursera.org/learn/python-text-mining"),
    ("NLP","NLP Zero to Hero","YouTube","https://www.youtube.com/watch?v=X2vAabgKiuM"),
    ("Computer Vision","Computer Vision Basics","Coursera","https://www.coursera.org/learn/computer-vision-basics"),
    ("Computer Vision","OpenCV Full Course","YouTube","https://www.youtube.com/watch?v=oXlwWbU8l2o"),
]

# ── 3. COMPANIES ─────────────────────────────────────────────────────────────
COMPANIES = [
    ("TechCorp Solutions",   "Information Technology",  "Bangalore", "hr@techcorp.com",        "+91-80-12345678"),
    ("DataMinds Analytics",  "Data & Analytics",        "Hyderabad", "careers@dataminds.in",   "+91-40-87654321"),
    ("CloudNova Systems",    "Cloud Computing",         "Pune",      "jobs@cloudnova.io",       "+91-20-11223344"),
    ("FinTech Innovations",  "Banking & Finance",       "Mumbai",    "hr@fintechin.com",        "+91-22-99887766"),
    ("CyberShield Security", "Cybersecurity",           "Chennai",   "recruit@cybershield.in",  "+91-44-55667788"),
    ("EduTech Learning",     "Education Technology",    "Delhi",     "hr@edutech.in",           "+91-11-44332211"),
]

# ── 4. JOB ROLES ─────────────────────────────────────────────────────────────
# (company_idx, title, description, required_skills, cgpa_threshold)
JOB_ROLES = [
    (0, "Full Stack Developer",
     "Build scalable web apps using React and Node.js with MySQL backend.",
     ["JavaScript", "React", "Node.js", "MySQL", "Git"], 7.0),

    (0, "Backend Engineer (Python)",
     "Develop REST APIs using Django/Flask with PostgreSQL.",
     ["Python", "Django", "Flask", "PostgreSQL", "Docker", "Git"], 7.5),

    (1, "Data Scientist",
     "Build ML models for business insights using Python and cloud tools.",
     ["Python", "Machine Learning", "Deep Learning", "TensorFlow", "Pandas", "NumPy"], 7.5),

    (1, "Data Analyst",
     "Analyse business data using SQL and visualization tools.",
     ["Python", "MySQL", "Pandas", "Data Science"], 6.5),

    (2, "Cloud Engineer (AWS)",
     "Design and deploy AWS infrastructure with Docker and Kubernetes.",
     ["AWS", "Docker", "Kubernetes", "Linux", "CI/CD"], 7.0),

    (2, "DevOps Engineer",
     "Implement CI/CD pipelines and manage cloud infrastructure.",
     ["Docker", "Kubernetes", "AWS", "Linux", "CI/CD", "Git"], 7.0),

    (3, "Software Developer (Java)",
     "Enterprise application development with Spring Boot and MySQL.",
     ["Java", "Spring Boot", "MySQL", "Git"], 7.0),

    (4, "Cybersecurity Analyst",
     "Monitor and protect systems from security threats.",
     ["Linux", "Python", "Git"], 7.0),

    (5, "Frontend Developer",
     "Create responsive UI using React and TypeScript.",
     ["React", "TypeScript", "JavaScript", "Git", "Bootstrap", "TailwindCSS"], 6.5),
]


def banner(title):
    print(f"\n{'='*52}")
    print(f"  {title}")
    print('='*52)


# ── SEED FUNCTIONS ────────────────────────────────────────────────────────────

def seed_taxonomy():
    banner("1. SKILL TAXONOMY")
    added = 0
    for canonical, category, synonyms in SKILLS:
        row = SkillTaxonomy.query.filter_by(canonical_name=canonical).first()
        if row:
            row.category = category
            row.synonyms_json = json.dumps(synonyms)
        else:
            db.session.add(SkillTaxonomy(
                canonical_name=canonical,
                category=category,
                synonyms_json=json.dumps(synonyms),
                is_deprecated=False,
            ))
            added += 1
    db.session.commit()
    print(f"  ✅ {added} new | {SkillTaxonomy.query.count()} total skills in taxonomy")


def seed_courses():
    banner("2. COURSE RECOMMENDATIONS")
    added = 0
    for skill_name, course_name, provider, url in COURSES:
        exists = CourseRecommendation.query.filter_by(
            skill_name=skill_name, course_name=course_name).first()
        if not exists:
            db.session.add(CourseRecommendation(
                skill_name=skill_name, course_name=course_name,
                provider=provider, url=url,
            ))
            added += 1
    db.session.commit()
    print(f"  ✅ {added} new | {CourseRecommendation.query.count()} total courses")


def seed_companies():
    banner("3. COMPANIES")
    objs = []
    added = 0
    for name, industry, location, email, phone in COMPANIES:
        row = Company.query.filter_by(name=name).first()
        if row:
            objs.append(row)
        else:
            c = Company(name=name, industry=industry, location=location,
                        contact_email=email, contact_phone=phone)
            db.session.add(c)
            db.session.flush()
            objs.append(c)
            added += 1
    db.session.commit()
    print(f"  ✅ {added} new | {Company.query.count()} total companies")
    return objs


def seed_job_roles(companies):
    banner("4. JOB ROLES")
    from app.services.skill_analyzer import SkillAnalyzer
    analyzer = SkillAnalyzer()
    added = 0
    for comp_idx, title, desc, skills, cgpa in JOB_ROLES:
        company = companies[comp_idx]
        exists = JobRole.query.filter_by(company_id=company.id, title=title).first()
        if exists:
            # Regenerate vector in case taxonomy was just seeded
            try:
                vec = analyzer.generate_job_requirement_vector(skills)
                taxonomy = SkillTaxonomy.query.filter_by(
                    is_deprecated=False).order_by(SkillTaxonomy.id).all()
                skill_index = {s.canonical_name.lower(): i for i, s in enumerate(taxonomy)}
                exists.job_vector_json = json.dumps({
                    "vector": vec.tolist(), "skill_index": skill_index, "version": "1.0"})
                exists.required_skills_json = json.dumps(skills)
                db.session.commit()
            except Exception:
                pass
            continue
        try:
            vec = analyzer.generate_job_requirement_vector(skills)
            taxonomy = SkillTaxonomy.query.filter_by(
                is_deprecated=False).order_by(SkillTaxonomy.id).all()
            skill_index = {s.canonical_name.lower(): i for i, s in enumerate(taxonomy)}
            vec_json = json.dumps({"vector": vec.tolist(), "skill_index": skill_index, "version": "1.0"})
        except Exception:
            vec_json = None
        db.session.add(JobRole(
            company_id=company.id, title=title, description=desc,
            required_skills_json=json.dumps(skills),
            job_vector_json=vec_json,
            cgpa_threshold=cgpa, is_active=True,
        ))
        added += 1
    db.session.commit()
    print(f"  ✅ {added} new | {JobRole.query.count()} total job roles")


def seed_student_profiles():
    banner("5. STUDENT PROFILES & SKILL VECTORS")
    from app.services.skill_analyzer import SkillAnalyzer
    analyzer = SkillAnalyzer()
    added = 0
    for user in User.query.filter_by(role="student").all():
        profile = StudentProfile.query.filter_by(user_id=user.id).first()
        if not profile:
            profile = StudentProfile(
                user_id=user.id,
                institution="ATMECE",
                degree="B.E",
                branch="Computer Science",
                cgpa=8.0,
                graduation_year=2026,
                skills_json=json.dumps(
                    ["Python", "React", "MySQL", "Machine Learning", "Git", "Docker"]),
                dream_job="Software Developer",
                expected_lpa=8.0,
            )
            db.session.add(profile)
            db.session.flush()
            db.session.add(Project(
                profile_id=profile.id,
                title="Skill2Job Platform",
                description="AI-based placement coordination system using Flask and React",
                technologies="Python, React, MySQL, Machine Learning",
            ))
            db.session.commit()
            added += 1
            print(f"  Created profile for {user.name}")
        # Always rebuild skill vector now that taxonomy is seeded
        try:
            analyzer.analyze_and_store(profile)
        except Exception as e:
            print(f"  Warning: vector rebuild failed for {user.name}: {e}")
    db.session.commit()
    print(f"  ✅ {added} new | {StudentProfile.query.count()} total profiles with skill vectors")


def seed_interviews():
    banner("6. INTERVIEWS")
    if Interview.query.count() > 0:
        print(f"  ✅ {Interview.query.count()} interviews already exist — skipping")
        return
    profiles = StudentProfile.query.all()
    jobs = JobRole.query.filter_by(is_active=True).all()
    admin = User.query.filter(User.role.in_(["admin", "placement_officer"])).first()
    if not profiles or not jobs:
        print("  ⚠️  No profiles or jobs found — skipping")
        return
    p0 = profiles[0]
    p1 = profiles[1] if len(profiles) > 1 else profiles[0]
    j0, j1, j2 = jobs[0], (jobs[1] if len(jobs) > 1 else jobs[0]), (jobs[2] if len(jobs) > 2 else jobs[0])
    aid = admin.id if admin else None
    interviews = [
        Interview(profile_id=p0.id, job_role_id=j0.id, company_id=j0.company_id,
                  scheduled_by=aid,
                  interview_date=date.today() + timedelta(days=7),
                  interview_time="10:00 AM", mode="in-person",
                  venue_or_link="TechCorp Office, Koramangala, Bangalore",
                  status="scheduled"),
        Interview(profile_id=p0.id, job_role_id=j2.id, company_id=j2.company_id,
                  scheduled_by=aid,
                  interview_date=date.today() + timedelta(days=14),
                  interview_time="2:00 PM", mode="online",
                  venue_or_link="https://meet.google.com/abc-defg-hij",
                  status="scheduled"),
        Interview(profile_id=p1.id, job_role_id=j1.id, company_id=j1.company_id,
                  scheduled_by=aid,
                  interview_date=date.today() - timedelta(days=3),
                  interview_time="11:00 AM", mode="in-person",
                  venue_or_link="DataMinds Office, Hyderabad",
                  status="completed", result="selected",
                  feedback="Strong ML knowledge and good communication skills"),
    ]
    for i in interviews:
        db.session.add(i)
    db.session.commit()
    print(f"  ✅ {Interview.query.count()} interviews created")


def seed_placements():
    banner("7. PLACEMENT RECORDS")
    if PlacementRecord.query.count() > 0:
        print(f"  ✅ {PlacementRecord.query.count()} placements already exist — skipping")
        return
    profiles = StudentProfile.query.all()
    jobs = JobRole.query.filter_by(is_active=True).all()
    companies = Company.query.all()
    if not profiles or not jobs or not companies:
        print("  ⚠️  Missing data — skipping")
        return
    records = [
        PlacementRecord(
            profile_id=profiles[0].id, job_role_id=jobs[0].id,
            company_id=companies[0].id,
            placement_date=date.today() - timedelta(days=30),
            department="Computer Science", package_lpa=12.5,
            notes="Joined as Full Stack Developer"),
    ]
    if len(profiles) > 1 and len(jobs) > 2:
        records.append(PlacementRecord(
            profile_id=profiles[1].id, job_role_id=jobs[2].id,
            company_id=companies[1].id,
            placement_date=date.today() - timedelta(days=15),
            department="Computer Science", package_lpa=15.0,
            notes="Joined as Data Scientist"))
    for r in records:
        exists = PlacementRecord.query.filter_by(
            profile_id=r.profile_id, job_role_id=r.job_role_id).first()
        if not exists:
            db.session.add(r)
    db.session.commit()
    print(f"  ✅ {PlacementRecord.query.count()} placement records created")


def seed_notifications():
    banner("8. NOTIFICATIONS")
    if Notification.query.count() > 0:
        print(f"  ✅ {Notification.query.count()} notifications already exist — skipping")
        return
    sender = User.query.filter(User.role.in_(["admin", "placement_officer"])).first()
    sid = sender.id if sender else None
    student_count = User.query.filter_by(role="student").count()
    items = [
        Notification(sent_by=sid,
            title="🚀 Placement Drive — TechCorp Solutions",
            message="TechCorp Solutions is visiting campus on July 15th for Full Stack and Backend roles. CGPA cutoff: 7.0. Register on the portal by July 10th. Eligible branches: CSE, ISE, ECE.",
            target_audience="all_students", recipient_count=student_count, is_email=False),
        Notification(sent_by=sid,
            title="📋 Interview Shortlist Released — DataMinds Analytics",
            message="Students shortlisted for DataMinds Analytics Data Scientist role have been notified. Check your dashboard for the interview schedule. Date: July 20th at 10:00 AM.",
            target_audience="shortlisted", recipient_count=2, is_email=False),
        Notification(sent_by=sid,
            title="📚 50+ New Courses Added — ML, AI & Cloud",
            message="We have added over 50 course recommendations across Machine Learning, Deep Learning, TensorFlow, AWS, Docker and more. Visit Skill Analysis → Skill Gap to see recommended courses for your target role.",
            target_audience="all_students", recipient_count=student_count, is_email=False),
        Notification(sent_by=sid,
            title="🎉 Placement Statistics — June 2026",
            message="We are proud to announce that 87% of eligible CSE students have been placed this season. Average package: ₹12.5 LPA. Highest package: ₹24 LPA. Top recruiters: TechCorp, DataMinds, CloudNova.",
            target_audience="all_students", recipient_count=student_count, is_email=False),
    ]
    for n in items:
        db.session.add(n)
    db.session.commit()
    print(f"  ✅ {Notification.query.count()} notifications created")


def seed_shortlists():
    banner("9. SHORTLISTS")
    if Shortlist.query.count() > 0:
        print(f"  ✅ {Shortlist.query.count()} shortlists already exist — skipping")
        return
    from app.services.job_matching import JobMatchingEngine
    engine = JobMatchingEngine()
    total = 0
    for job in JobRole.query.filter_by(is_active=True).all()[:4]:
        try:
            candidates = engine.shortlist_candidates(job.id)
            for c in candidates[:5]:
                exists = Shortlist.query.filter_by(
                    profile_id=c["profile_id"], job_role_id=job.id).first()
                if not exists:
                    db.session.add(Shortlist(
                        profile_id=c["profile_id"],
                        job_role_id=job.id,
                        compatibility_score=c["compatibility_score"],
                        status="Shortlisted",
                    ))
                    total += 1
        except Exception as e:
            print(f"  Warning: shortlist failed for job {job.id}: {e}")
    db.session.commit()
    print(f"  ✅ {Shortlist.query.count()} shortlist records created")


def main():
    print("\n" + "="*52)
    print("  SKILL2JOB — MASTER SEED SCRIPT")
    print("="*52)
    app = create_app("development")
    with app.app_context():
        print("\nEnsuring all tables exist...")
        db.create_all()

        seed_taxonomy()
        seed_courses()
        companies = seed_companies()
        seed_job_roles(companies)
        seed_student_profiles()
        seed_interviews()
        seed_placements()
        seed_notifications()
        seed_shortlists()

        banner("FINAL SUMMARY")
        print(f"  Skills in taxonomy  : {SkillTaxonomy.query.count()}")
        print(f"  Courses             : {CourseRecommendation.query.count()}")
        print(f"  Companies           : {Company.query.count()}")
        print(f"  Job Roles           : {JobRole.query.count()}")
        print(f"  Student Profiles    : {StudentProfile.query.count()}")
        print(f"  Shortlists          : {Shortlist.query.count()}")
        print(f"  Interviews          : {Interview.query.count()}")
        print(f"  Placements          : {PlacementRecord.query.count()}")
        print(f"  Notifications       : {Notification.query.count()}")
        print()
        print("  Accounts:")
        print("  Admin    : sysadmin@skillbridge.com / SysAdmin1234")
        print("  Admin    : admin@skillbridge.com / Admin1234")
        print("  Student  : teststudent@test.com / Test@1234")
        print("="*52 + "\n")


if __name__ == "__main__":
    main()
