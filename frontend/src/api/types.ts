/** 与后端 Pydantic 模型一一对应的类型定义。 */

export interface TopicInfo {
  topic: string;
  label: string;
  count: number;
}

export interface Meta {
  question_count: number;
  default_exam_size: number;
  points_per_question: number;
  topics: TopicInfo[];
}

export interface ExamQuestion {
  id: string;
  topic: string;
  topic_label: string;
  difficulty: "easy" | "medium" | "hard" | string;
  question: string;
  options: Record<string, string>;
  /** 已作答时后端返回，用于刷新页面后续答 */
  selected?: string | null;
  is_correct?: boolean | null;
}

export interface Exam {
  id: string;
  created_at: string;
  status: "in_progress" | "finished" | string;
  size: number;
  topics: string[];
  points_per_question: number;
  questions: ExamQuestion[];
  answered_count: number;
  correct_count: number;
  score: number;
}

export interface AnswerFeedback {
  question_id: string;
  selected: string;
  is_correct: boolean;
  correct_answer: string;
  explanation: string;
  why_wrong: string | null;
  knowledge: string[];
  doc: string;
  topic: string;
  topic_label: string;
  question: string;
  options: Record<string, string>;
  answered_count: number;
  total: number;
  correct_count: number;
  score: number;
}

export interface ExamResult {
  id: string;
  created_at: string;
  finished_at: string | null;
  status: string;
  size: number;
  score: number;
  correct_count: number;
  wrong_count: number;
  duration_seconds: number;
  by_topic: { topic: string; label: string; total: number; correct: number }[];
}

export interface ExamHistoryItem {
  id: string;
  created_at: string;
  finished_at: string | null;
  status: string;
  size: number;
  score: number;
  correct_count: number;
  duration_seconds: number;
  topics: string[];
}

export interface AnswerDetail {
  question: ExamQuestion;
  selected: string | null;
  is_correct: boolean | null;
  correct_answer: string;
  explanation: string;
  why_wrong: string | null;
  knowledge: string[];
  doc: string;
}

export interface ExamDetail {
  exam: ExamResult;
  answers: AnswerDetail[];
}

export interface WrongQuestion {
  question_id: string;
  topic: string;
  topic_label: string;
  wrong_count: number;
  last_selected: string | null;
  first_wrong_at: string;
  last_wrong_at: string;
  mastered: boolean;
  note: string;
  question: ExamQuestion;
  correct_answer: string;
  explanation: string;
  why_wrong: string | null;
  knowledge: string[];
  doc: string;
}

export interface TopicStat {
  topic: string;
  label: string;
  attempts: number;
  correct: number;
  accuracy: number;
  bank_count: number;
  wrong_open: number;
}

export interface Stats {
  exam_count: number;
  finished_exam_count: number;
  answered_questions: number;
  avg_score: number;
  best_score: number;
  total_minutes: number;
  bank_size: number;
  wrong_open_count: number;
  wrong_mastered_count: number;
  by_topic: TopicStat[];
  recent_exams: ExamHistoryItem[];
}

export interface CreateExamPayload {
  size?: number;
  topics?: string[];
  difficulty?: "easy" | "medium" | "hard" | "any";
  only_wrong?: boolean;
}
