import { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import api from '../../services/api';
import { AxiosError } from 'axios';

interface GapEntry {
  skill: string;
  deficit_score: number;
}

interface CourseItem {
  id: number;
  skill_name: string;
  course_name: string;
  provider: string;
  url: string;
}

interface SkillCourseGroup {
  skill: string;
  deficit_score: number;
  courses: CourseItem[];
  message?: string;
}

const PROVIDER_COLORS: Record<string, string> = {
  Coursera: '#0056d2',
  Udemy: '#a435f0',
  NPTEL: '#1a73e8',
  YouTube: '#ff0000',
};

function getImportanceLevel(deficit: number): { label: string; color: string } {
  if (deficit >= 0.8) return { label: 'Critical', color: '#dc2626' };
  if (deficit >= 0.5) return { label: 'High', color: '#ea580c' };
  if (deficit >= 0.3) return { label: 'Medium', color: '#ca8a04' };
  return { label: 'Low', color: '#16a34a' };
}

export default function SkillGap() {
  const { id } = useParams<{ id: string }>();
  const [gaps, setGaps] = useState<GapEntry[]>([]);
  const [skillCourses, setSkillCourses] = useState<SkillCourseGroup[]>([]);
  const [loadingGap, setLoadingGap] = useState(true);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [gapError, setGapError] = useState('');
  const [courseError, setCourseError] = useState('');
  const [fullCoverage, setFullCoverage] = useState(false);

  useEffect(() => {
    if (!id) return;

    const fetchGap = async () => {
      try {
        const res = await api.get(`/jobs/${id}/skill-gap`);
        const data = res.data;
        if (data.message === 'Full skill coverage') {
          setFullCoverage(true);
          setGaps([]);
        } else {
          setGaps(Array.isArray(data.gaps) ? data.gaps : []);
        }
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
        setSkillCourses(Array.isArray(data.skill_courses) ? data.skill_courses : []);
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
        <h2 className="section-title">Missing Skills</h2>

        {gapError && <div className="alert alert-error">{gapError}</div>}

        {!gapError && fullCoverage && (
          <div className="alert alert-success">
            🎉 Full skill coverage — you meet all skill requirements for this role!
          </div>
        )}

        {!gapError && gaps.length > 0 && (
          <div className="gap-list">
            {gaps.map((gap, idx) => {
              const importance = getImportanceLevel(gap.deficit_score);
              return (
                <div key={idx} className="gap-item">
                  <div className="gap-item-header">
                    <span className="gap-skill-name">{gap.skill}</span>
                    <span
                      className="gap-importance-badge"
                      style={{ backgroundColor: importance.color }}
                    >
                      {importance.label}
                    </span>
                  </div>
                  <div className="gap-bar-container">
                    <div
                      className="gap-bar"
                      style={{
                        width: `${Math.round(gap.deficit_score * 100)}%`,
                        backgroundColor: importance.color,
                      }}
                    />
                  </div>
                  <span className="gap-score">
                    {Math.round(gap.deficit_score * 100)}% deficit
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Course Recommendations Section */}
      <div className="page-section">
        <h2 className="section-title">Recommended Learning Path</h2>
        <p className="helper-text">
          Courses from Coursera, Udemy, NPTEL, and YouTube to fill your skill gaps.
        </p>

        {courseError && <div className="alert alert-error">{courseError}</div>}

        {!courseError && skillCourses.length === 0 && !fullCoverage && (
          <p className="empty-text">No courses available for the identified skill gaps.</p>
        )}

        {!courseError && skillCourses.length > 0 && (
          <div className="skill-courses-container">
            {skillCourses.map((group, gIdx) => {
              const importance = getImportanceLevel(group.deficit_score);
              return (
                <div key={gIdx} className="skill-course-group">
                  <div className="skill-course-group-header">
                    <h3 className="skill-course-skill-name">{group.skill}</h3>
                    <span
                      className="gap-importance-badge"
                      style={{ backgroundColor: importance.color }}
                    >
                      {importance.label} Priority
                    </span>
                  </div>

                  {group.courses.length > 0 ? (
                    <div className="course-cards-grid">
                      {group.courses.map((course, cIdx) => (
                        <div key={cIdx} className="course-card">
                          <div className="course-card-body">
                            <span
                              className="course-provider-badge"
                              style={{
                                backgroundColor: PROVIDER_COLORS[course.provider] || '#6b7280',
                              }}
                            >
                              {course.provider}
                            </span>
                            <h4 className="course-name">{course.course_name}</h4>
                          </div>
                          {course.url && (
                            <a
                              href={course.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="course-link-btn"
                            >
                              Start Learning →
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="empty-text">No courses available for this skill yet.</p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
