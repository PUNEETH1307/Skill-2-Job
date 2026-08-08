export type ResumeTemplateCategory = 'without-photo' | 'with-photo';

export interface ProjectItem {
  name: string;
  description: string;
  techStack: string;
  impact: string;
  link: string;
}

export interface ResumeProfile {
  fullName: string;
  headline: string;
  summary: string;
  email: string;
  phone: string;
  location: string;
  website: string;
  photoUrl: string;
  skills: string[];
  projects: ProjectItem[];
  experience: string[];
  education: string[];
}

export interface ResumeTemplate {
  id: string;
  name: string;
  category: ResumeTemplateCategory;
  accent: string;
  description: string;
  hasPhoto: boolean;
  tone: 'minimal' | 'balanced' | 'bold';
}

export const resumeTemplates: ResumeTemplate[] = [
  {
    id: 'clean-slate',
    name: 'Clean Slate',
    category: 'without-photo',
    accent: '#0f172a',
    description: 'Sharp typography, strong spacing, and a classic ATS-friendly layout.',
    hasPhoto: false,
    tone: 'minimal',
  },
  {
    id: 'editorial-edge',
    name: 'Editorial Edge',
    category: 'without-photo',
    accent: '#7c2d12',
    description: 'Magazine-style name block with elegant section rhythm.',
    hasPhoto: false,
    tone: 'bold',
  },
  {
    id: 'minimal-flow',
    name: 'Minimal Flow',
    category: 'without-photo',
    accent: '#155e75',
    description: 'A calm two-column layout with compact highlights.',
    hasPhoto: false,
    tone: 'balanced',
  },
  {
    id: 'professional-spotlight',
    name: 'Professional Spotlight',
    category: 'with-photo',
    accent: '#1d4ed8',
    description: 'Photo-led layout with a clean left rail for contact details.',
    hasPhoto: true,
    tone: 'balanced',
  },
  {
    id: 'executive-frame',
    name: 'Executive Frame',
    category: 'with-photo',
    accent: '#374151',
    description: 'Formal, boardroom-ready layout with a photo badge and section dividers.',
    hasPhoto: true,
    tone: 'minimal',
  },
  {
    id: 'modern-profile',
    name: 'Modern Profile',
    category: 'with-photo',
    accent: '#c2410c',
    description: 'Warm and energetic profile-first layout for portfolio-driven resumes.',
    hasPhoto: true,
    tone: 'bold',
  },
];

export const defaultResumeProfile: ResumeProfile = {
  fullName: 'Alex Morgan',
  headline: 'Software Developer',
  summary: '',
  email: '',
  phone: '',
  location: '',
  website: '',
  photoUrl: '',
  skills: ['React', 'TypeScript', 'Node.js'],
  projects: [],
  experience: [],
  education: [],
};

export function getMissingProfileFields(profile: ResumeProfile): string[] {
  const missing: string[] = [];

  if (!profile.fullName.trim()) missing.push('full name');
  if (!profile.headline.trim()) missing.push('headline');
  if (!profile.summary.trim()) missing.push('summary');
  if (!profile.email.trim()) missing.push('email');
  if (!profile.phone.trim()) missing.push('phone');
  if (!profile.location.trim()) missing.push('location');
  if (!profile.website.trim()) missing.push('website');
  if (profile.skills.length === 0) missing.push('skills');
  if (profile.projects.length === 0) missing.push('projects');
  if (profile.experience.length === 0) missing.push('experience');
  if (profile.education.length === 0) missing.push('education');

  return missing;
}

export function cloneProfile(profile: ResumeProfile): ResumeProfile {
  return {
    ...profile,
    skills: [...profile.skills],
    projects: profile.projects.map((project) => ({ ...project })),
    experience: [...profile.experience],
    education: [...profile.education],
  };
}