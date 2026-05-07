import { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import api from '../../services/api';
import { AxiosError } from 'axios';

interface GapEntry {
  skill: string;
  deficit_score: number;
}

interface CourseEntry {
  skill_name: string;
  course_name: string;
  provider: string;
  url: string;
}

export default function SkillGap() {
  const { id } = useParams<{ id: string }>();
  const [gaps, setGaps] = useState<GapEntry[]>([]);
  const [coveragePercentage, setCoveragePercentage] = useState<number | null>(null);
  const [courses, setCourses] = useState<CourseEntry[]>([]);
  const [loadingGap, setLoadingGap] = useState(true);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [gapError, setGapError] = useState('');
  const [courseError, setCourseError] = useState('');

  useEffect(() => {
    if (!id) return;

    const fetchGap = async () => {
      try {
        const res = await api.get(`/jobs/${id}/skill-gap`);
        const data = res.data;
        setGaps(Array.isArray(data.gaps) ? data.gaps : []);
        setCoveragePercentage(data.coverage_percentage ?? null);
      } catch (err) {
        if (err instanceof AxiosError && err.response) {
          setGapError(err.response.data?.error?.message ?? 'Failed to load skill gap.');
        } else {
          setGapError('Unable to connect to the server.');
        }
      } finally {
        setLoadingGap(false);
      }
    };

    const fetchCourses = async () => {
      try {
        const res = await api.get(`/jobs/${id}/courses`);
        const data = res.data;
        setCourses(Array.isArray(data) ? data : data.courses ?? []);
      } catch (err) {
        if (err instanceof AxiosError && err.response) {
          setCourseError(err.response.data?.error?.message ?? 'Failed to load courses.');
        } else {
          setCourseError('Unable to connect to the server.');
        }
      } finally {
        setLoadingCourses(false);
      }
    };

    fetchGap();
    fetchCourses();
  }, [id]);

  const loading = loadingGap || loadingCourses;

  if (loading) {
    return (
      <div className="page-container">
        <p className="loading-text"><span className="spinner" /> Loading skill gap analysis...</p>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Skill Gap Analysis</h1>
        <Link to="/student/jobs" className="back-link">Back to Recommendations</Link>
      </div>

      {/* Skill Gap Section */}
      <div className="page-section">
        <h2 className="section-title">Missing / Weak Skills</h2>

        {gapError && <div className="alert alert-error">{gapError}</div>}

        {!gapError && gaps.length === 0 && (
          <div className="alert alert-success">
            Full skill coverage — you meet all skill requirements for this role!
          </div>
        )}

        {!gapError && coveragePercentage != null && (
          <p className="coverage-text">
            Skill coverage: <strong>{Math.round(coveragePercentage)}%</strong>
          </p>
        )}

        {!gapError && gaps.length > 0 && (
          <div className="gap-list">
            {gaps.map((gap, idx) => (
              <div key={idx} className="gap-item">
                <span className="gap-skill-name">{gap.skill}</span>
                <div className="gap-bar-container">
                  <div
                    className="gap-bar"
                    style={{ width: `${Math.round(gap.deficit_score * 100)}%` }}
                  />
                </div>
                <span className="gap-score">
                  {Math.round(gap.deficit_score * 100)}% deficit
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Course Recommendations Section */}
      <div className="page-section">
        <h2 className="section-title">Course Recommendations</h2>

        {courseError && <div className="alert alert-error">{courseError}</div>}

        {!courseError && courses.length === 0 && (
          <p className="empty-text">No courses available for the identified skill gaps.</p>
        )}

        {!courseError && courses.length > 0 && (
          <div className="course-list">
            {courses.map((course, idx) => (
              <div key={idx} className="course-card">
                <div>
                  <h4 className="course-name">{course.course_name}</h4>
                  <p className="course-provider">
                    {course.provider} &middot; Skill: {course.skill_name}
                  </p>
                </div>
                {course.url && (
                  <a
                    href={course.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="course-link"
                  >
                    View Course &rarr;
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
