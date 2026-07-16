// Shared TypeScript interfaces for CodeSwitch frontend

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  bio: string | null;
  avatar: string | null;
  date_joined: string;
  is_staff?: boolean;
}

export interface ConversionRecord {
  id: number;
  source_language: string;
  target_language: string;
  input_code: string;
  output_code: string;
  timestamp: string;
}

export interface CodeFile {
  id: number;
  filename: string;
  language: string;
  code_content: string;
  created_at: string;
  updated_at: string;
}

export interface LearningModule {
  id: number;
  title: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  language: string;
  lesson_count: number;
  lessons?: Lesson[];
}

export interface Lesson {
  id: number;
  title: string;
  content: string;
  example_code: string;
  order: number;
}

export interface UserProgress {
  id: number;
  lesson_id: number;
  module_title: string;
  lesson_title: string;
  completed: boolean;
  completion_date: string | null;
}

export interface Quiz {
  id: number;
  title: string;
  passing_score: number;
  attempt: { score: number; passed: boolean } | null;
  questions: QuizQuestion[];
}

export interface QuizQuestion {
  id: number;
  question_text: string;
  order: number;
  options: QuizOption[];
}

export interface QuizOption {
  id: number;
  option_text: string;
  explanation: string;
}

export interface SharedSnippet {
  source_language: string;
  target_language: string;
  input_code: string;
  output_code: string;
  engine: string;
  created_at: string;
}

export interface PublicProfile {
  username: string;
  date_joined: string;
  conversion_count: number;
  lessons_completed: number;
  modules_completed: number;
  languages_used: string[];
  first_name?: string;
  last_name?: string;
  bio?: string | null;
  avatar?: string | null;
  email?: string;
}

export interface RunResult {
  stdout: string;
  stderr: string;
  code: number;
}

export interface VerificationResult {
  verified: boolean;
  status: 'match' | 'mismatch' | 'source_error' | 'target_error';
  summary: string;
  source: RunResult;
  target: RunResult;
  comparison: {
    stdout_match: boolean;
    exit_code_match: boolean;
  };
}

export type VisualizationStepKind =
  | 'function'
  | 'loop'
  | 'condition'
  | 'assignment'
  | 'array'
  | 'return'
  | 'output'
  | 'call'
  | 'statement';

export interface VisualizationVariable {
  name: string;
  value: string;
}

export type VisualizationPrimitive = string | number | boolean | null;

export interface VisualizationRef {
  $ref: string;
}

export type VisualizationValue = VisualizationPrimitive | VisualizationRef;

export interface VisualizationFrame {
  id: string;
  name: string;
  variables: Record<string, VisualizationValue>;
}

export interface VisualizationHeapObject {
  type: 'list' | 'tuple' | 'dict' | 'set' | 'object';
  items: unknown;
  repr?: string;
}

export interface VisualizationTraceError {
  message: string;
  line?: number;
}

export interface VisualizationTraceStep {
  id: string;
  line: number;
  event: 'call' | 'line' | 'return' | 'exception';
  frames: VisualizationFrame[];
  heap: Record<string, VisualizationHeapObject>;
  stdout: string;
  return_value?: VisualizationValue;
  error?: VisualizationTraceError;
}

export interface VisualizationStep {
  id: string;
  line: number;
  kind: VisualizationStepKind;
  title: string;
  description: string;
  code: string;
  visual: {
    focus: VisualizationStepKind;
    variables: VisualizationVariable[];
    stack?: Array<{
      name: string;
      variables: VisualizationVariable[];
    }>;
    output?: string[];
    return_value?: string;
    pulse?: 'loop' | 'branch' | 'output' | 'collection';
    iteration_label?: string;
  };
}

export interface VisualizationTimeline {
  language: string;
  mode?: 'execution_trace' | 'concept_trace';
  summary: string;
  concepts: string[];
  recommendations: string[];
  trace?: VisualizationTraceStep[];
  error?: VisualizationTraceError;
  steps: VisualizationStep[];
}

export interface AdminStats {
  total_users: number;
  total_conversions: number;
  total_files: number;
  total_modules: number;
  new_users_this_week: number;
  conversions_this_week: number;
}

export interface AdminUser {
  id: number;
  username: string;
  email: string;
  is_staff: boolean;
  is_active: boolean;
  date_joined: string;
  conversion_count: number;
}

export interface AdminConversion {
  id: number;
  user: string;
  source_language: string;
  target_language: string;
  timestamp: string;
}

export interface AdminLesson extends Lesson {
  has_quiz?: boolean;
}

export type Language = 'python' | 'c' | 'java' | 'javascript' | 'cpp' | 'other';
export type Difficulty = 'beginner' | 'intermediate' | 'advanced';
export type TabName = 'Overview' | 'Users' | 'Conversions' | 'Modules';
