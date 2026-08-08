import type { CSSProperties } from 'react';
import type { ProjectItem } from '../templateData';

type ProjectsSectionProps = {
  projects?: ProjectItem[];
  accentColor?: string;
  showWarning?: boolean;
  onAddProject?: () => void;
  onEditProject?: () => void;
  [key: string]: any;
};

const styles: Record<string, CSSProperties> = {
  wrapper: {
    borderRadius: '24px',
    padding: '18px',
    background: 'linear-gradient(180deg, rgba(248, 250, 252, 1), rgba(255, 255, 255, 1))',
    border: '1px solid rgba(15, 23, 42, 0.08)',
  },
  warning: {
    padding: '14px 16px',
    marginBottom: '16px',
    borderRadius: '16px',
    background: 'rgba(254, 243, 199, 0.72)',
    color: '#92400e',
    lineHeight: 1.6,
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '16px',
  },
  title: {
    margin: 0,
    fontSize: '1.08rem',
    fontWeight: 800,
    color: '#0f172a',
  },
  action: {
    border: 'none',
    borderRadius: '999px',
    padding: '10px 14px',
    background: 'rgba(15, 23, 42, 0.08)',
    color: '#111827',
    fontWeight: 700,
    cursor: 'pointer',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    gap: '14px',
  },
  card: {
    borderRadius: '18px',
    padding: '16px',
    background: '#fff',
    border: '1px solid rgba(15, 23, 42, 0.08)',
    boxShadow: '0 12px 28px rgba(15, 23, 42, 0.06)',
  },
  projectName: {
    margin: '0 0 8px',
    fontSize: '1rem',
    fontWeight: 800,
    color: '#0f172a',
  },
  projectDescription: {
    margin: 0,
    color: '#475569',
    lineHeight: 1.6,
  },
  meta: {
    marginTop: '12px',
    display: 'grid',
    gap: '8px',
    fontSize: '0.9rem',
    color: '#334155',
  },
};

function ProjectsSection(props: ProjectsSectionProps) {
  const projects = props.projects ?? [];
  const accentColor = props.accentColor ?? '#1d4ed8';

  return (
    <section style={styles.wrapper}>
      {props.showWarning ? (
        <div style={styles.warning}>
          No data found from profile for projects. Fill or skip this section before you generate the resume.
        </div>
      ) : null}

      <div style={styles.header}>
        <h3 style={styles.title}>Projects</h3>
        <button type="button" style={{ ...styles.action, color: accentColor }} onClick={props.onAddProject ?? props.onEditProject}>
          Add project
        </button>
      </div>

      {projects.length > 0 ? (
        <div style={styles.grid}>
          {projects.map((project, index) => (
            <article key={`${project.name}-${index}`} style={styles.card}>
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '14px',
                  background: `linear-gradient(135deg, ${accentColor}, rgba(15, 23, 42, 0.88))`,
                  marginBottom: '12px',
                }}
              />
              <h4 style={styles.projectName}>{project.name || 'Untitled project'}</h4>
              <p style={styles.projectDescription}>{project.description || 'Add a short project summary.'}</p>
              <div style={styles.meta}>
                <span>Tech: {project.techStack || 'Not added yet'}</span>
                <span>Impact: {project.impact || 'No impact statement yet'}</span>
                {project.link ? <span>Link: {project.link}</span> : null}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div style={styles.card}>
          <p style={{ margin: 0, color: '#475569', lineHeight: 1.6 }}>
            Add 1-3 strong project cards here. This section is designed to look close to a FlowCV-style project block,
            with a clean visual hierarchy and room for project impact.
          </p>
        </div>
      )}
    </section>
  );
}

export default ProjectsSection;