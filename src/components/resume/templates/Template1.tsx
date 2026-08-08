import type { CSSProperties } from 'react';
import type { ResumeProfile, ResumeTemplate } from '../templateData';

type TemplatePreviewProps = {
  profile?: ResumeProfile;
  template?: ResumeTemplate;
  compact?: boolean;
  [key: string]: any;
};

const styles: Record<string, CSSProperties> = {
  shell: {
    display: 'grid',
    gap: '20px',
    color: '#111827',
    fontFamily: 'Georgia, Times New Roman, serif',
  },
  withPhoto: {
    gridTemplateColumns: '0.82fr 1.18fr',
    alignItems: 'start',
  },
  withoutPhoto: {
    gridTemplateColumns: '1fr',
  },
  leftRail: {
    borderRadius: '22px',
    padding: '18px',
    color: '#fff',
    background: 'linear-gradient(180deg, #0f172a, #1e293b)',
    minHeight: '100%',
  },
  profilePhoto: {
    width: '112px',
    height: '112px',
    borderRadius: '28px',
    background: 'linear-gradient(135deg, rgba(255,255,255,0.4), rgba(255,255,255,0.1))',
    border: '1px solid rgba(255,255,255,0.22)',
    marginBottom: '16px',
  },
  name: {
    margin: 0,
    fontSize: '2rem',
    lineHeight: 1.04,
    fontWeight: 800,
    color: '#0f172a',
  },
  heroName: {
    margin: 0,
    fontSize: '2.5rem',
    lineHeight: 1.02,
    fontWeight: 900,
    color: '#0f172a',
  },
  section: {
    display: 'grid',
    gap: '10px',
  },
  sectionTitle: {
    fontSize: '0.9rem',
    fontWeight: 800,
    letterSpacing: '0.12em',
    textTransform: 'uppercase',
    color: '#64748b',
  },
  chipRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
  },
  chip: {
    borderRadius: '999px',
    padding: '8px 12px',
    background: 'rgba(15, 23, 42, 0.06)',
    fontSize: '0.9rem',
    fontWeight: 700,
  },
  projectCard: {
    borderRadius: '18px',
    padding: '16px',
    border: '1px solid rgba(15, 23, 42, 0.08)',
    background: '#fff',
    boxShadow: '0 14px 30px rgba(15, 23, 42, 0.06)',
  },
};

function Template1(props: TemplatePreviewProps) {
  const profile = props.profile;
  const template = props.template;
  const compact = props.compact ?? false;
  const hasPhoto = Boolean(template?.hasPhoto);

  return (
    <div
      style={{
        ...styles.shell,
        ...(hasPhoto ? styles.withPhoto : styles.withoutPhoto),
        gap: compact ? '14px' : '20px',
      }}
    >
      {hasPhoto ? (
        <aside style={styles.leftRail}>
          <div
            style={{
              ...styles.profilePhoto,
              backgroundImage: profile?.photoUrl ? `url(${profile.photoUrl})` : styles.profilePhoto.background,
              backgroundSize: profile?.photoUrl ? 'cover' : 'auto',
              backgroundPosition: 'center',
            }}
          />
          <p style={{ margin: '0 0 10px', fontSize: '1.7rem', fontWeight: 900, lineHeight: 1.05 }}>
            {profile?.fullName || 'Your name'}
          </p>
          <p style={{ margin: '0 0 18px', opacity: 0.88, lineHeight: 1.55 }}>{profile?.headline || 'Headline goes here'}</p>
          <div style={{ display: 'grid', gap: '8px', fontSize: '0.93rem', lineHeight: 1.55 }}>
            <span>{profile?.email || 'email@example.com'}</span>
            <span>{profile?.phone || '+91 00000 00000'}</span>
            <span>{profile?.location || 'Location'}</span>
            <span>{profile?.website || 'portfolio.example.com'}</span>
          </div>
        </aside>
      ) : null}

      <section style={{ display: 'grid', gap: compact ? '14px' : '20px' }}>
        <div style={styles.section}>
          <div style={styles.sectionTitle}>Profile</div>
          <h2 style={hasPhoto ? styles.name : styles.heroName}>{profile?.fullName || 'Your name'}</h2>
          <p style={{ margin: 0, color: '#475569', lineHeight: 1.7 }}>{profile?.summary || 'Write a concise summary of your background and goals.'}</p>
        </div>

        <div style={styles.section}>
          <div style={styles.sectionTitle}>Skills</div>
          <div style={styles.chipRow}>
            {(profile?.skills?.length ? profile.skills : ['TypeScript', 'React', 'Problem solving']).map((skill) => (
              <span key={skill} style={styles.chip}>
                {skill}
              </span>
            ))}
          </div>
        </div>

        <div style={styles.section}>
          <div style={styles.sectionTitle}>Projects</div>
          <div style={{ display: 'grid', gap: '12px' }}>
            {(profile?.projects?.length ? profile.projects : [{ name: 'Project title', description: 'A short project description.', techStack: 'React, Node.js', impact: 'Improved workflow efficiency by 25%', link: '' }]).map((project, index) => (
              <article key={`${project.name}-${index}`} style={styles.projectCard}>
                <p style={{ margin: '0 0 6px', fontWeight: 800 }}>{project.name}</p>
                <p style={{ margin: '0 0 8px', color: '#475569', lineHeight: 1.6 }}>{project.description}</p>
                <p style={{ margin: 0, color: '#0f172a', fontWeight: 700, lineHeight: 1.55 }}>{project.techStack}</p>
                <p style={{ margin: '4px 0 0', color: '#475569', lineHeight: 1.55 }}>{project.impact}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

export default Template1;