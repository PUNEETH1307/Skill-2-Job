import { useMemo, useState, type CSSProperties, type FormEvent } from 'react';
import TemplateSelector from '../components/resume/TemplateSelector';
import GenerationDialog from '../components/resume/GenerationDialog';
import ResumeFormDialog from '../components/resume/ResumeFormDialog';
import ProjectsSection from '../components/resume/sections/ProjectsSection';
import Template1 from '../components/resume/templates/Template1';
import {
  defaultResumeProfile,
  getMissingProfileFields,
  resumeTemplates,
  type ResumeProfile,
  type ResumeTemplate,
} from '../components/resume/templateData';

const pageStyles: Record<string, CSSProperties> = {
  page: {
    minHeight: '100vh',
    padding: '32px',
    background:
      'radial-gradient(circle at top left, rgba(255, 122, 89, 0.22), transparent 28%), radial-gradient(circle at top right, rgba(0, 163, 255, 0.18), transparent 24%), linear-gradient(180deg, #f7f2eb 0%, #f3efe8 100%)',
    color: '#1f2937',
    fontFamily: 'Georgia, Times New Roman, serif',
  },
  shell: {
    maxWidth: '1400px',
    margin: '0 auto',
  },
  hero: {
    display: 'grid',
    gridTemplateColumns: '1.25fr 0.95fr',
    gap: '24px',
    alignItems: 'stretch',
    marginBottom: '24px',
  },
  heroCard: {
    background: 'rgba(255, 255, 255, 0.82)',
    border: '1px solid rgba(31, 41, 55, 0.08)',
    borderRadius: '28px',
    boxShadow: '0 30px 80px rgba(31, 41, 55, 0.12)',
    backdropFilter: 'blur(12px)',
    overflow: 'hidden',
  },
  heroCopy: {
    padding: '32px',
  },
  eyebrow: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 12px',
    borderRadius: '999px',
    background: 'rgba(15, 23, 42, 0.08)',
    color: '#0f172a',
    fontSize: '12px',
    letterSpacing: '0.16em',
    textTransform: 'uppercase',
    marginBottom: '18px',
  },
  title: {
    fontSize: 'clamp(2.2rem, 4vw, 4.1rem)',
    lineHeight: 1.02,
    margin: 0,
    color: '#111827',
  },
  subtitle: {
    marginTop: '18px',
    marginBottom: '0',
    maxWidth: '62ch',
    color: '#374151',
    fontSize: '1rem',
    lineHeight: 1.7,
  },
  actionsRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '12px',
    marginTop: '22px',
  },
  primaryButton: {
    border: 'none',
    borderRadius: '14px',
    padding: '14px 18px',
    background: 'linear-gradient(135deg, #0f172a, #1d4ed8)',
    color: '#fff',
    fontWeight: 700,
    cursor: 'pointer',
    boxShadow: '0 18px 40px rgba(29, 78, 216, 0.24)',
  },
  secondaryButton: {
    border: '1px solid rgba(15, 23, 42, 0.14)',
    borderRadius: '14px',
    padding: '14px 18px',
    background: 'rgba(255, 255, 255, 0.82)',
    color: '#111827',
    fontWeight: 700,
    cursor: 'pointer',
  },
  infoStack: {
    display: 'grid',
    gap: '14px',
    padding: '24px',
    borderLeft: '1px solid rgba(31, 41, 55, 0.08)',
  },
  infoCard: {
    background: 'linear-gradient(180deg, rgba(255,255,255,0.94), rgba(255,255,255,0.8))',
    borderRadius: '22px',
    padding: '18px',
    border: '1px solid rgba(31, 41, 55, 0.08)',
  },
  section: {
    marginBottom: '24px',
  },
  sectionTitle: {
    fontSize: '1.1rem',
    fontWeight: 800,
    color: '#111827',
    marginBottom: '10px',
  },
  layout: {
    display: 'grid',
    gridTemplateColumns: '1fr 0.95fr',
    gap: '24px',
    alignItems: 'start',
  },
  panel: {
    background: 'rgba(255,255,255,0.88)',
    border: '1px solid rgba(31, 41, 55, 0.08)',
    borderRadius: '28px',
    padding: '24px',
    boxShadow: '0 20px 55px rgba(31, 41, 55, 0.1)',
  },
  warning: {
    marginBottom: '20px',
    padding: '16px 18px',
    borderRadius: '18px',
    background: 'linear-gradient(135deg, rgba(255, 244, 229, 1), rgba(255, 233, 213, 1))',
    border: '1px solid rgba(217, 119, 6, 0.18)',
    color: '#78350f',
  },
  warningTitle: {
    margin: 0,
    fontWeight: 800,
    marginBottom: '6px',
  },
  warningText: {
    margin: 0,
    lineHeight: 1.6,
  },
  previewFrame: {
    borderRadius: '28px',
    background: 'linear-gradient(180deg, rgba(15,23,42,0.96), rgba(30,41,59,0.96))',
    padding: '18px',
    color: '#e5e7eb',
    boxShadow: '0 26px 60px rgba(15, 23, 42, 0.28)',
    position: 'sticky',
    top: '20px',
  },
  previewLabel: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '14px',
    fontSize: '0.92rem',
    color: '#cbd5e1',
  },
  previewCard: {
    background: '#fff',
    color: '#111827',
    borderRadius: '24px',
    padding: '18px',
    minHeight: '640px',
  },
};

function ResumeBuilder() {
  const [profile, setProfile] = useState<ResumeProfile>(defaultResumeProfile);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('');
  const [showGenerateDialog, setShowGenerateDialog] = useState(false);
  const [showFormDialog, setShowFormDialog] = useState(false);
  const [generationState, setGenerationState] = useState<'idle' | 'ready' | 'generated'>('idle');
  const [skipMissingPrompt, setSkipMissingPrompt] = useState(false);
  const [statusMessage, setStatusMessage] = useState('Choose a template before generating your resume.');

  const selectedTemplate = useMemo<ResumeTemplate | undefined>(
    () => resumeTemplates.find((template) => template.id === selectedTemplateId),
    [selectedTemplateId],
  );

  const missingFields = useMemo(() => getMissingProfileFields(profile), [profile]);
  const hasMissingFields = missingFields.length > 0;
  const canGenerate = Boolean(selectedTemplate) && (!hasMissingFields || skipMissingPrompt);

  function handleOpenFillForm() {
    setShowFormDialog(true);
    setStatusMessage('Fill the missing fields in the form below. You can still skip any field you do not have.');
  }

  function handleTemplateChoose(templateId: string) {
    setSelectedTemplateId(templateId);
    setGenerationState('ready');
    setStatusMessage('Template selected. Review the profile and generate when you are ready.');
  }

  function handleGenerateClick() {
    if (!selectedTemplate) {
      setStatusMessage('Please choose one of the templates first.');
      return;
    }

    if (hasMissingFields && !skipMissingPrompt) {
      setShowFormDialog(true);
      setStatusMessage('No data found from profile for some fields. Fill them now or skip to continue.');
      return;
    }

    setShowGenerateDialog(true);
  }

  function handleFormSubmit(nextProfile: ResumeProfile) {
    setProfile(nextProfile);
    setSkipMissingPrompt(false);
    setShowFormDialog(false);
    setStatusMessage('Profile data updated. You can now generate with the selected template.');
  }

  function handleSkipMissing() {
    setSkipMissingPrompt(true);
    setStatusMessage('Missing fields will be skipped for now. You can generate with the available profile data.');
  }

  function handleGenerateResume(event?: FormEvent) {
    if (event) {
      event.preventDefault();
    }

    setGenerationState('generated');
    setShowGenerateDialog(false);
    setStatusMessage(`Generated a ${selectedTemplate?.name ?? 'selected'} resume draft.`);
  }

  return (
    <main style={pageStyles.page}>
      <div style={pageStyles.shell}>
        <section style={pageStyles.hero}>
          <div style={pageStyles.heroCard}>
            <div style={pageStyles.heroCopy}>
              <div style={pageStyles.eyebrow}>FlowCV-inspired resume studio</div>
              <h1 style={pageStyles.title}>Choose a template before you generate.</h1>
              <p style={pageStyles.subtitle}>
                Pick from a set of modern, recruiter-friendly layouts with and without a photo slot.
                If profile data is missing, you will see a warning and can fill it in form style or skip it for now.
              </p>
              <div style={pageStyles.actionsRow}>
                <button type="button" style={pageStyles.primaryButton} onClick={handleGenerateClick}>
                  Generate resume
                </button>
                <button type="button" style={pageStyles.secondaryButton} onClick={handleOpenFillForm}>
                  Fill missing profile data
                </button>
              </div>
            </div>
          </div>

          <aside style={pageStyles.heroCard}>
            <div style={pageStyles.infoStack}>
              <div style={pageStyles.infoCard}>
                <div style={pageStyles.sectionTitle}>Current status</div>
                <p style={{ margin: 0, lineHeight: 1.65 }}>{statusMessage}</p>
              </div>
              <div style={pageStyles.infoCard}>
                <div style={pageStyles.sectionTitle}>Template mix</div>
                <p style={{ margin: 0, lineHeight: 1.65 }}>
                  {resumeTemplates.filter((template) => template.category === 'without-photo').length} layouts without photo
                  and {resumeTemplates.filter((template) => template.category === 'with-photo').length} layouts with photo.
                </p>
              </div>
              <div style={pageStyles.infoCard}>
                <div style={pageStyles.sectionTitle}>Profile readiness</div>
                <p style={{ margin: 0, lineHeight: 1.65 }}>
                  {hasMissingFields ? `${missingFields.length} field${missingFields.length > 1 ? 's' : ''} still need attention.` : 'Everything is ready to generate.'}
                </p>
              </div>
            </div>
          </aside>
        </section>

        <section style={pageStyles.layout}>
          <div style={pageStyles.panel}>
            {hasMissingFields && !skipMissingPrompt ? (
              <div style={pageStyles.warning}>
                <p style={pageStyles.warningTitle}>No data found from profile for: {missingFields.join(', ')}</p>
                <p style={pageStyles.warningText}>
                  Fill the missing details in a form or skip them for now. If you choose fill, the next dialog will ask
                  for the missing information in a structured form.
                </p>
                <div style={pageStyles.actionsRow}>
                  <button type="button" style={pageStyles.primaryButton} onClick={handleOpenFillForm}>
                    Fill now
                  </button>
                  <button type="button" style={pageStyles.secondaryButton} onClick={handleSkipMissing}>
                    Skip for now
                  </button>
                </div>
              </div>
            ) : null}

            <div style={pageStyles.section}>
              <div style={pageStyles.sectionTitle}>Popular templates</div>
              <TemplateSelector
                templates={resumeTemplates}
                selectedTemplateId={selectedTemplateId}
                onSelect={handleTemplateChoose}
              />
            </div>

            <div style={pageStyles.section}>
              <div style={pageStyles.sectionTitle}>Projects section preview</div>
              <ProjectsSection
                projects={profile.projects}
                accentColor={selectedTemplate?.accent}
                onAddProject={handleOpenFillForm}
                onEditProject={handleOpenFillForm}
                showWarning={hasMissingFields && profile.projects.length === 0}
              />
            </div>

            <div style={pageStyles.actionsRow}>
              <button type="button" style={pageStyles.primaryButton} onClick={handleGenerateClick} disabled={!selectedTemplateId}>
                Generate with selected template
              </button>
              <button type="button" style={pageStyles.secondaryButton} onClick={handleOpenFillForm}>
                Review profile fields
              </button>
            </div>
          </div>

          <div style={pageStyles.previewFrame}>
            <div style={pageStyles.previewLabel}>
              <span>Resume preview</span>
              <span>{selectedTemplate ? selectedTemplate.name : 'No template selected'}</span>
            </div>
            <div style={pageStyles.previewCard}>
              <Template1 profile={profile} template={selectedTemplate ?? resumeTemplates[0]} />
            </div>
          </div>
        </section>
      </div>

      <ResumeFormDialog
        open={showFormDialog}
        profile={profile}
        missingFields={missingFields}
        onClose={() => setShowFormDialog(false)}
        onSubmit={handleFormSubmit}
        onSkip={handleSkipMissing}
      />

      <GenerationDialog
        open={showGenerateDialog}
        template={selectedTemplate}
        profile={profile}
        missingFields={missingFields}
        onClose={() => setShowGenerateDialog(false)}
        onGenerate={handleGenerateResume}
        generationState={generationState}
        canGenerate={canGenerate}
      />
    </main>
  );
}

export default ResumeBuilder;