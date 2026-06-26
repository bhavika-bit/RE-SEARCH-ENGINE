import { Atom, Dna, BrainCircuit, Leaf, FlaskConical, Database, Cpu, Globe, Sparkles } from 'lucide-react';
import { LucideIcon } from 'lucide-react';

export interface TopicTheme {
  name: string;
  accentColor: string;
  accentColorDark: string;
  gradientFrom: string;
  gradientTo: string;
  icon: LucideIcon;
}

const PALETTES: TopicTheme[] = [
  {
    name: 'Quantum Physics',
    accentColor: '#8B5CF6',
    accentColorDark: '#7C3AED',
    gradientFrom: '#8B5CF6',
    gradientTo: '#6366F1',
    icon: Atom,
  },
  {
    name: 'Biology & Medical',
    accentColor: '#10B981',
    accentColorDark: '#059669',
    gradientFrom: '#10B981',
    gradientTo: '#14B8A6',
    icon: Dna,
  },
  {
    name: 'AI & Machine Learning',
    accentColor: '#06B6D4',
    accentColorDark: '#0891B2',
    gradientFrom: '#06B6D4',
    gradientTo: '#3B82F6',
    icon: BrainCircuit,
  },
  {
    name: 'Climate & Earth',
    accentColor: '#84CC16',
    accentColorDark: '#65A30D',
    gradientFrom: '#84CC16',
    gradientTo: '#22C55E',
    icon: Leaf,
  },
  {
    name: 'Chemistry',
    accentColor: '#F472B6',
    accentColorDark: '#DB2777',
    gradientFrom: '#F472B6',
    gradientTo: '#EC4899',
    icon: FlaskConical,
  },
  {
    name: 'Data Science',
    accentColor: '#FB923C',
    accentColorDark: '#EA580C',
    gradientFrom: '#FB923C',
    gradientTo: '#F97316',
    icon: Database,
  },
  {
    name: 'Systems Engineering',
    accentColor: '#64748B',
    accentColorDark: '#475569',
    gradientFrom: '#64748B',
    gradientTo: '#94A3B8',
    icon: Cpu,
  },
  {
    name: 'Social Sciences',
    accentColor: '#A78BFA',
    accentColorDark: '#8B5CF6',
    gradientFrom: '#A78BFA',
    gradientTo: '#C4B5FD',
    icon: Globe,
  },
];

const DEFAULT_THEME: TopicTheme = {
  name: 'Research',
  accentColor: '#F59E0B',
  accentColorDark: '#D97706',
  gradientFrom: '#F59E0B',
  gradientTo: '#EAB308',
  icon: Sparkles,
};

function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash);
}

export function getTopicTheme(topicString: string): TopicTheme {
  if (!topicString || topicString.trim() === '') {
    return DEFAULT_THEME;
  }

  const lowerTopic = topicString.toLowerCase();

  if (lowerTopic.includes('quantum') || lowerTopic.includes('physics') || lowerTopic.includes('particle')) {
    return PALETTES[0];
  }

  if (lowerTopic.includes('bio') || lowerTopic.includes('medical') || lowerTopic.includes('genetic') || lowerTopic.includes('health')) {
    return PALETTES[1];
  }

  if (lowerTopic.includes('neural') || lowerTopic.includes('ml') || lowerTopic.includes('ai') || lowerTopic.includes('machine learning') || lowerTopic.includes('deep learning') || lowerTopic.includes('nlp')) {
    return PALETTES[2];
  }

  if (lowerTopic.includes('climate') || lowerTopic.includes('environment') || lowerTopic.includes('earth') || lowerTopic.includes('sustainability') || lowerTopic.includes('ecolog')) {
    return PALETTES[3];
  }

  if (lowerTopic.includes('chem') || lowerTopic.includes('molecular') || lowerTopic.includes('compound')) {
    return PALETTES[4];
  }

  if (lowerTopic.includes('data') || lowerTopic.includes('analytics') || lowerTopic.includes('statistics') || lowerTopic.includes('visualization')) {
    return PALETTES[5];
  }

  if (lowerTopic.includes('system') || lowerTopic.includes('engineering') || lowerTopic.includes('robot') || lowerTopic.includes('hardware')) {
    return PALETTES[6];
  }

  if (lowerTopic.includes('social') || lowerTopic.includes('psychology') || lowerTopic.includes('economics') || lowerTopic.includes('political')) {
    return PALETTES[7];
  }

  const hash = hashString(topicString);
  return PALETTES[hash % PALETTES.length];
}
