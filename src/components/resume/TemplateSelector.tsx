import type { CSSProperties } from 'react';
import { resumeTemplates, type ResumeTemplate } from './templateData';

type TemplateSelectorProps = {
  templates?: ResumeTemplate[];
  selectedTemplateId?: string;
  selectedTemplate?: string;
  onSelect?: (templateId: string) => void;
  onChoose?: (templateId: string) => void;
  [key: string]: any;
};

const styles: Record<string, CSSProperties> = {
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: '16px',
  },
  card: {
    borderRadius: '22px',
    border: '1px solid rgba(15, 23, 42, 0.08)',
    overflow: 'hidden',
    background: '#fff',
    cursor: 'pointer',
    boxShadow: '0 16px 40px rgba(15, 23, 42, 0.08)',
    transition: 'transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease',
  },
  selectedCard: {
    borderColor: 'rgba(29, 78, 216, 0.55)',
    transform: 'translateY(-3px)',
    boxShadow: '0 22px 55px rgba(29, 78, 216, 0.18)',
  },
  preview: {
    minHeight: '168px',
    padding: '16px',
    color: '#fff',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    gap: '12px',
  },
  badgeRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '8px',
    fontSize: '0.76rem',
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    opacity: 0.96,
  },
  title: {
    margin: 0,
    fontWeight: 800,
    fontSize: '1.05rem',
  },
  description: {
    margin: 0,
    fontSize: '0.9rem',
    lineHeight: 1.55,
    color: 'rgba(15, 23, 42, 0.74)',
  },
  meta: {
    padding: '14px 16px 16px',
  },
  mockLines: {
    display: 'grid',
    gap: '8px',
  },
  line: {
    height: '10px',
    borderRadius: '999px',
    background: 'rgba(255, 255, 255, 0.82)',
  },
};

function TemplateSelector(props: TemplateSelectorProps) {
  const templates = props.templates ?? resumeTemplates;
  const currentSelection = props.selectedTemplateId ?? props.selectedTemplate ?? '';
  const handleSelect = props.onSelect ?? props.onChoose ?? (() => undefined);

  return (
    <div style={styles.grid}>
      {templates.map((template) => {
        const selected = currentSelection === template.id;
        const cardStyle: CSSProperties = {
          ...styles.card,
          ...(selected ? styles.selectedCard : {}),
        };

        return (
          <button
            key={template.id}
            type="button"
            style={cardStyle}
            onClick={() => handleSelect(template.id)}
          >
            <div
              style={{
                ...styles.preview,
                background:
                  template.category === 'with-photo'
                    ? `linear-gradient(135deg, ${template.accent}, #111827)`
                    : `linear-gradient(135deg, ${template.accent}, #334155)`,
              }}
            >
              <div style={styles.badgeRow}>
                <span>{template.category === 'with-photo' ? 'Photo template' : 'No-photo template'}</span>
                <span>{selected ? 'Selected' : template.tone.toUpperCase()}</span>
              </div>

              <div style={{ display: 'grid', gap: '10px' }}>
                {template.hasPhoto ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div
                      style={{
                        width: '54px',
                        height: '54px',
                        borderRadius: '18px',
                        background: 'rgba(255,255,255,0.22)',
                        border: '1px solid rgba(255,255,255,0.3)',
                      }}
                    />
                    <div style={{ display: 'grid', gap: '7px', flex: 1 }}>
                      <div style={{ ...styles.line, width: '68%' }} />
                      <div style={{ ...styles.line, width: '42%', opacity: 0.78 }} />
                    </div>
                  </div>
                ) : (
                  <div style={{ display: 'grid', gap: '8px' }}>
                    <div style={{ ...styles.line, width: '76%' }} />
                    <div style={{ ...styles.line, width: '58%', opacity: 0.82 }} />
                  </div>
                )}

                <div style={{ display: 'grid', gap: '8px' }}>
                  <div style={{ ...styles.line, width: '100%', height: '8px' }} />
                  <div style={{ ...styles.line, width: '86%', height: '8px', opacity: 0.86 }} />
                  <div style={{ ...styles.line, width: '62%', height: '8px', opacity: 0.74 }} />
                </div>
              </div>
            </div>

            <div style={styles.meta}>
              <p style={styles.title}>{template.name}</p>
              <p style={styles.description}>{template.description}</p>
            </div>
          </button>
        );
      })}
    </div>
  );
}

export default TemplateSelector;