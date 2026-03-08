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
