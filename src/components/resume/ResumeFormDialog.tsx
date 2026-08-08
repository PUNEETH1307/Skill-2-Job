import { useEffect, useMemo, useState, type CSSProperties, type FormEvent } from 'react';
import { cloneProfile, defaultResumeProfile, type ResumeProfile } from './templateData';

type ResumeFormDialogProps = {
  open?: boolean;
  profile?: ResumeProfile;
  missingFields?: string[];
  onClose?: () => void;
  onSubmit?: (profile: ResumeProfile) => void;
  onSkip?: () => void;
  [key: string]: any;
};

const styles: Record<string, CSSProperties> = {
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(15, 23, 42, 0.62)',
    display: 'grid',
    placeItems: 'center',
    padding: '20px',
    zIndex: 70,
  },
  dialog: {
    width: 'min(100%, 820px)',
    maxHeight: '90vh',
    overflow: 'auto',
    borderRadius: '28px',
    background: '#fff',
    boxShadow: '0 30px 90px rgba(15, 23, 42, 0.35)',
  },
  header: {
    padding: '24px',
    borderBottom: '1px solid rgba(15, 23, 42, 0.08)',
    background: 'linear-gradient(135deg, rgba(239, 246, 255, 1), rgba(255, 247, 237, 1))',
  },
  title: {
    margin: 0,
    color: '#0f172a',
    fontWeight: 800,
    fontSize: '1.4rem',
  },
  subtitle: {
    margin: '10px 0 0',
    lineHeight: 1.6,
    color: '#475569',
  },
  body: {
    padding: '24px',
    display: 'grid',
    gap: '18px',
  },
  warning: {
    padding: '14px 16px',
    borderRadius: '18px',
    background: 'rgba(254, 243, 199, 0.7)',
    color: '#92400e',
    lineHeight: 1.55,
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: '14px',
  },
  field: {
    display: 'grid',
    gap: '8px',
  },
  label: {
    fontSize: '0.88rem',
    fontWeight: 700,
    color: '#334155',
  },
  input: {
    width: '100%',
    borderRadius: '14px',
    border: '1px solid rgba(15, 23, 42, 0.12)',
    padding: '13px 14px',
    fontSize: '0.98rem',
    color: '#0f172a',
    background: '#fff',
  },
  textarea: {
    minHeight: '110px',
    resize: 'vertical',
  },
  footer: {
    padding: '0 24px 24px',
    display: 'flex',
    flexWrap: 'wrap',
    gap: '12px',
    justifyContent: 'flex-end',
  },
  button: {
    borderRadius: '14px',
    border: 'none',
    padding: '13px 18px',
    fontWeight: 800,
    cursor: 'pointer',
  },
  primary: {
    background: 'linear-gradient(135deg, #0f172a, #2563eb)',
    color: '#fff',
  },
  secondary: {
    background: 'rgba(15, 23, 42, 0.06)',
    color: '#111827',
  },
};

function ResumeFormDialog(props: ResumeFormDialogProps) {
  const open = props.open ?? false;
  const fields = props.missingFields ?? [];
  const initialProfile = useMemo(() => cloneProfile(props.profile ?? defaultResumeProfile), [props.profile]);
  const [draft, setDraft] = useState<ResumeProfile>(initialProfile);

  useEffect(() => {
    setDraft(initialProfile);
  }, [initialProfile]);

  if (!open) {
    return null;
  }

  function updateField(key: keyof ResumeProfile, value: string) {
    setDraft((current) => ({
      ...current,
      [key]: value,
    }));
  }

  function updateSkills(value: string) {
    setDraft((current) => ({
      ...current,
      skills: value
        .split(',')
        .map((skill) => skill.trim())
        .filter(Boolean),
    }));
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    props.onSubmit?.(draft);
  }

  return (
    <div style={styles.overlay}>
      <div style={styles.dialog}>
        <div style={styles.header}>
          <p style={styles.title}>Fill profile details</p>
          <p style={styles.subtitle}>
            No data found from profile for {fields.length > 0 ? fields.join(', ') : 'the selected fields'}. Fill the form or skip.
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={styles.body}>
            <div style={styles.warning}>
              The next generated resume will use the data entered here. Any empty field can still be skipped if you do not have it yet.
            </div>

            <div style={styles.grid}>
              <label style={styles.field}>
                <span style={styles.label}>Full name</span>
                <input style={styles.input} value={draft.fullName} onChange={(event) => updateField('fullName', event.target.value)} />
              </label>
              <label style={styles.field}>
                <span style={styles.label}>Headline</span>
                <input style={styles.input} value={draft.headline} onChange={(event) => updateField('headline', event.target.value)} />
              </label>
              <label style={{ ...styles.field, gridColumn: '1 / -1' }}>
                <span style={styles.label}>Summary</span>
                <textarea
                  style={{ ...styles.input, ...styles.textarea }}
                  value={draft.summary}
                  onChange={(event) => updateField('summary', event.target.value)}
                />
              </label>
              <label style={styles.field}>
                <span style={styles.label}>Email</span>
                <input style={styles.input} value={draft.email} onChange={(event) => updateField('email', event.target.value)} />
              </label>
              <label style={styles.field}>
                <span style={styles.label}>Phone</span>
                <input style={styles.input} value={draft.phone} onChange={(event) => updateField('phone', event.target.value)} />
              </label>
              <label style={styles.field}>
                <span style={styles.label}>Location</span>
                <input style={styles.input} value={draft.location} onChange={(event) => updateField('location', event.target.value)} />
              </label>
              <label style={styles.field}>
                <span style={styles.label}>Website</span>
                <input style={styles.input} value={draft.website} onChange={(event) => updateField('website', event.target.value)} />
              </label>
              <label style={{ ...styles.field, gridColumn: '1 / -1' }}>
                <span style={styles.label}>Photo URL, if you want a photo template</span>
                <input style={styles.input} value={draft.photoUrl} onChange={(event) => updateField('photoUrl', event.target.value)} />
              </label>
              <label style={{ ...styles.field, gridColumn: '1 / -1' }}>
                <span style={styles.label}>Skills, comma separated</span>
                <input
                  style={styles.input}
                  value={draft.skills.join(', ')}
                  onChange={(event) => updateSkills(event.target.value)}
                />
              </label>
            </div>

            <div style={styles.grid}>
              <label style={{ ...styles.field, gridColumn: '1 / -1' }}>
                <span style={styles.label}>Projects</span>
                <textarea
                  style={{ ...styles.input, ...styles.textarea }}
                  value={draft.projects.map((project) => `${project.name} | ${project.description} | ${project.techStack} | ${project.impact}`).join('\n')}
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      projects: event.target.value
                        .split('\n')
                        .map((line) => line.trim())
                        .filter(Boolean)
                        .map((line) => {
                          const [name = '', description = '', techStack = '', impact = ''] = line.split('|').map((part) => part.trim());
                          return { name, description, techStack, impact, link: '' };
                        }),
                    }))
                  }
                />
              </label>
            </div>
          </div>

          <div style={styles.footer}>
            <button type="button" style={{ ...styles.button, ...styles.secondary }} onClick={props.onSkip}>
              Skip for now
            </button>
            <button type="button" style={{ ...styles.button, ...styles.secondary }} onClick={props.onClose}>
              Cancel
            </button>
            <button type="submit" style={{ ...styles.button, ...styles.primary }}>
              Save details
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ResumeFormDialog;