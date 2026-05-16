"""Seed script for course recommendations.

Populates the course_recommendation table with learning resources from
Coursera, Udemy, NPTEL, and YouTube for common tech skills.

Usage:
    python seed_courses.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import CourseRecommendation


COURSES = [
    # Python
    {"skill_name": "Python", "course_name": "Python for Everybody Specialization", "provider": "Coursera", "url": "https://www.coursera.org/specializations/python"},
    {"skill_name": "Python", "course_name": "Complete Python Bootcamp", "provider": "Udemy", "url": "https://www.udemy.com/course/complete-python-bootcamp/"},
    {"skill_name": "Python", "course_name": "Programming in Python", "provider": "NPTEL", "url": "https://nptel.ac.in/courses/106106182"},
    {"skill_name": "Python", "course_name": "Python Full Course for Beginners", "provider": "YouTube", "url": "https://www.youtube.com/watch?v=_uQrJ0TkZlc"},

    # JavaScript
    {"skill_name": "JavaScript", "course_name": "JavaScript for Beginners Specialization", "provider": "Coursera", "url": "https://www.coursera.org/specializations/javascript-beginner"},
    {"skill_name": "JavaScript", "course_name": "The Complete JavaScript Course", "provider": "Udemy", "url": "https://www.udemy.com/course/the-complete-javascript-course/"},
    {"skill_name": "JavaScript", "course_name": "JavaScript Crash Course", "provider": "YouTube", "url": "https://www.youtube.com/watch?v=hdI2bqOjy3c"},

    # React
    {"skill_name": "React", "course_name": "React Basics by Meta", "provider": "Coursera", "url": "https://www.coursera.org/learn/react-basics"},
    {"skill_name": "React", "course_name": "React - The Complete Guide", "provider": "Udemy", "url": "https://www.udemy.com/course/react-the-complete-guide-incl-redux/"},
    {"skill_name": "React", "course_name": "React JS Full Course", "provider": "YouTube", "url": "https://www.youtube.com/watch?v=bMknfKXIFA8"},

    # Java
    {"skill_name": "Java", "course_name": "Java Programming and Software Engineering", "provider": "Coursera", "url": "https://www.coursera.org/specializations/java-programming"},
    {"skill_name": "Java", "course_name": "Java Programming Masterclass", "provider": "Udemy", "url": "https://www.udemy.com/course/java-the-complete-java-developer-course/"},
    {"skill_name": "Java", "course_name": "Programming in Java", "provider": "NPTEL", "url": "https://nptel.ac.in/courses/106105191"},

    # SQL
    {"skill_name": "SQL", "course_name": "SQL for Data Science", "provider": "Coursera", "url": "https://www.coursera.org/learn/sql-for-data-science"},
    {"skill_name": "SQL", "course_name": "The Complete SQL Bootcamp", "provider": "Udemy", "url": "https://www.udemy.com/course/the-complete-sql-bootcamp/"},
    {"skill_name": "SQL", "course_name": "Database Management Systems", "provider": "NPTEL", "url": "https://nptel.ac.in/courses/106105175"},

    # Machine Learning
    {"skill_name": "Machine Learning", "course_name": "Machine Learning by Andrew Ng", "provider": "Coursera", "url": "https://www.coursera.org/learn/machine-learning"},
    {"skill_name": "Machine Learning", "course_name": "Machine Learning A-Z", "provider": "Udemy", "url": "https://www.udemy.com/course/machinelearning/"},
    {"skill_name": "Machine Learning", "course_name": "Machine Learning for Engineering", "provider": "NPTEL", "url": "https://nptel.ac.in/courses/106106139"},
    {"skill_name": "Machine Learning", "course_name": "Machine Learning Full Course", "provider": "YouTube", "url": "https://www.youtube.com/watch?v=GwIo3gDZCVQ"},

    # Docker
    {"skill_name": "Docker", "course_name": "Docker for Developers", "provider": "Coursera", "url": "https://www.coursera.org/learn/docker-container"},
    {"skill_name": "Docker", "course_name": "Docker Mastery", "provider": "Udemy", "url": "https://www.udemy.com/course/docker-mastery/"},
    {"skill_name": "Docker", "course_name": "Docker Tutorial for Beginners", "provider": "YouTube", "url": "https://www.youtube.com/watch?v=fqMOX6JJhGo"},

    # AWS
    {"skill_name": "AWS", "course_name": "AWS Cloud Practitioner Essentials", "provider": "Coursera", "url": "https://www.coursera.org/learn/aws-cloud-practitioner-essentials"},
    {"skill_name": "AWS", "course_name": "Ultimate AWS Certified Cloud Practitioner", "provider": "Udemy", "url": "https://www.udemy.com/course/aws-certified-cloud-practitioner-new/"},
    {"skill_name": "AWS", "course_name": "AWS Full Course", "provider": "YouTube", "url": "https://www.youtube.com/watch?v=k1RI5locZE4"},

    # Node.js
    {"skill_name": "Node.js", "course_name": "Server-side Development with NodeJS", "provider": "Coursera", "url": "https://www.coursera.org/learn/server-side-nodejs"},
    {"skill_name": "Node.js", "course_name": "The Complete Node.js Developer Course", "provider": "Udemy", "url": "https://www.udemy.com/course/the-complete-nodejs-developer-course-2/"},
    {"skill_name": "Node.js", "course_name": "Node.js Full Course", "provider": "YouTube", "url": "https://www.youtube.com/watch?v=Oe421EPjeBE"},

    # Flask
    {"skill_name": "Flask", "course_name": "Python Flask Web Development", "provider": "Udemy", "url": "https://www.udemy.com/course/python-and-flask-bootcamp/"},
    {"skill_name": "Flask", "course_name": "Flask Tutorial for Beginners", "provider": "YouTube", "url": "https://www.youtube.com/watch?v=Z1RJmh_OqeA"},

    # Django
    {"skill_name": "Django", "course_name": "Django for Everybody", "provider": "Coursera", "url": "https://www.coursera.org/specializations/django"},
    {"skill_name": "Django", "course_name": "Python Django Full Course", "provider": "Udemy", "url": "https://www.udemy.com/course/python-and-django-full-stack-web-developer-bootcamp/"},

    # Git
    {"skill_name": "Git", "course_name": "Version Control with Git", "provider": "Coursera", "url": "https://www.coursera.org/learn/version-control-with-git"},
    {"skill_name": "Git", "course_name": "Git & GitHub Crash Course", "provider": "YouTube", "url": "https://www.youtube.com/watch?v=RGOj5yH7evk"},

    # TypeScript
    {"skill_name": "TypeScript", "course_name": "Understanding TypeScript", "provider": "Udemy", "url": "https://www.udemy.com/course/understanding-typescript/"},
    {"skill_name": "TypeScript", "course_name": "TypeScript Full Course", "provider": "YouTube", "url": "https://www.youtube.com/watch?v=BwuLxPH8IDs"},

    # MongoDB
    {"skill_name": "MongoDB", "course_name": "MongoDB for Developers", "provider": "Coursera", "url": "https://www.coursera.org/learn/introduction-mongodb"},
    {"skill_name": "MongoDB", "course_name": "MongoDB - The Complete Developer's Guide", "provider": "Udemy", "url": "https://www.udemy.com/course/mongodb-the-complete-developers-guide/"},

    # Kubernetes
    {"skill_name": "Kubernetes", "course_name": "Getting Started with Google Kubernetes Engine", "provider": "Coursera", "url": "https://www.coursera.org/learn/google-kubernetes-engine"},
    {"skill_name": "Kubernetes", "course_name": "Kubernetes for Absolute Beginners", "provider": "Udemy", "url": "https://www.udemy.com/course/learn-kubernetes/"},
    {"skill_name": "Kubernetes", "course_name": "Kubernetes Tutorial for Beginners", "provider": "YouTube", "url": "https://www.youtube.com/watch?v=X48VuDVv0do"},

    # TensorFlow
    {"skill_name": "TensorFlow", "course_name": "DeepLearning.AI TensorFlow Developer", "provider": "Coursera", "url": "https://www.coursera.org/professional-certificates/tensorflow-in-practice"},
    {"skill_name": "TensorFlow", "course_name": "TensorFlow Developer Certificate", "provider": "Udemy", "url": "https://www.udemy.com/course/tensorflow-developer-certificate-machine-learning-zero-to-mastery/"},
    {"skill_name": "TensorFlow", "course_name": "Deep Learning with Python and TensorFlow", "provider": "NPTEL", "url": "https://nptel.ac.in/courses/106106184"},

    # Angular
    {"skill_name": "Angular", "course_name": "Angular - The Complete Guide", "provider": "Udemy", "url": "https://www.udemy.com/course/the-complete-guide-to-angular-2/"},
    {"skill_name": "Angular", "course_name": "Angular Full Course", "provider": "YouTube", "url": "https://www.youtube.com/watch?v=3qBXWUpoPHo"},

    # PostgreSQL
    {"skill_name": "PostgreSQL", "course_name": "PostgreSQL for Everybody", "provider": "Coursera", "url": "https://www.coursera.org/specializations/postgresql-for-everybody"},
    {"skill_name": "PostgreSQL", "course_name": "The Complete PostgreSQL Bootcamp", "provider": "Udemy", "url": "https://www.udemy.com/course/the-complete-python-postgresql-developer-course/"},
]


def seed_courses():
    """Insert course recommendations (idempotent)."""
    count_new = 0
    count_existing = 0

    for entry in COURSES:
        existing = CourseRecommendation.query.filter_by(
            skill_name=entry["skill_name"],
            course_name=entry["course_name"],
        ).first()

        if existing:
            existing.provider = entry["provider"]
            existing.url = entry["url"]
            count_existing += 1
        else:
            course = CourseRecommendation(
                skill_name=entry["skill_name"],
                course_name=entry["course_name"],
                provider=entry["provider"],
                url=entry["url"],
            )
            db.session.add(course)
            count_new += 1

    db.session.commit()
    print(f"  Courses: {count_new} new, {count_existing} updated ({len(COURSES)} total)")


def main():
    app = create_app("development")
    with app.app_context():
        print("Seeding course recommendations...")
        seed_courses()
        print("Done.")


if __name__ == "__main__":
    main()
