import type { CSSProperties, FormEvent } from 'react';
import { type ResumeProfile, type ResumeTemplate } from './templateData';

type GenerationDialogProps = {
  open?: boolean;
  template?: ResumeTemplate | null;
  profile?: ResumeProfile;
  missingFields?: string[];
  generationState?: 'idle' | 'ready' | 'generated';
  canGenerate?: boolean;
  onClose?: () => void;
  onGenerate?: (event?: FormEvent) => void;
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
    zIndex: 60,
  },
  dialog: {
    width: 'min(100%, 720px)',
    borderRadius: '28px',
    background: '#fff',
    boxShadow: '0 30px 80px rgba(15, 23, 42, 0.35)',
    overflow: 'hidden',
  },
  header: {
    padding: '24px 24px 18px',
    borderBottom: '1px solid rgba(15, 23, 42, 0.08)',
    background: 'linear-gradient(135deg, rgba(241, 245, 249, 1), rgba(255, 247, 237, 1))',
  },
  body: {
    padding: '24px',
    display: 'grid',
    gap: '18px',
  },
  title: {
    margin: 0,
    fontSize: '1.45rem',
    color: '#0f172a',
    fontWeight: 800,
  },
  subtitle: {
    margin: '8px 0 0',
    lineHeight: 1.6,
    color: '#475569',
  },
  pillRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '10px',
  },
  pill: {
    borderRadius: '999px',
    padding: '8px 12px',
    background: 'rgba(15, 23, 42, 0.06)',
    color: '#0f172a',
    fontSize: '0.88rem',
    fontWeight: 700,
  },
  warning: {
    borderRadius: '18px',
    padding: '14px 16px',
    background: 'rgba(254, 243, 199, 0.72)',
    color: '#92400e',
    lineHeight: 1.55,
  },
  footer: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '12px',
    padding: '0 24px 24px',
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

function GenerationDialog(props: GenerationDialogProps) {
  const open = props.open ?? false;
  const template = props.template ?? null;
  const profile = props.profile;
  const missingFields = props.missingFields ?? [];
  const canGenerate = props.canGenerate ?? true;

  if (!open) {
    return null;
  }

  return (
    <div style={styles.overlay}>
      <div style={styles.dialog}>
        <div style={styles.header}>
          <p style={styles.title}>Ready to generate</p>
          <p style={styles.subtitle}>
            Confirm the template and make sure the profile details below are the ones you want in the generated resume.
          </p>
        </div>

        <div style={styles.body}>
          <div style={styles.pillRow}>
            <span style={styles.pill}>{template?.name ?? 'Template not selected'}</span>
            <span style={styles.pill}>{profile?.fullName?.trim() || 'Unnamed profile'}</span>
            <span style={styles.pill}>{template?.category === 'with-photo' ? 'Photo layout' : 'No-photo layout'}</span>
          </div>

          {missingFields.length > 0 ? (
            <div style={styles.warning}>
              No data found from profile for: {missingFields.join(', ')}. You can still generate now, but those sections
              will stay blank until they are filled.
            </div>
          ) : null}
        </div>

        <div style={styles.footer}>
          <button type="button" style={{ ...styles.button, ...styles.secondary }} onClick={props.onClose}>
            Cancel
          </button>
          <button
            type="button"
            style={{ ...styles.button, ...styles.primary, opacity: canGenerate ? 1 : 0.5 }}
            onClick={props.onGenerate}
            disabled={!canGenerate}
          >
            Generate now
          </button>
        </div>
      </div>
    </div>
  );
}

export default GenerationDialog;