/**
 * REST-контракт Backend API.
 *
 * Источник: docs/packages/contracts/openapi/api.v1.yaml (OpenAPI 3.1.0).
 * Python-зеркало: docs/packages/contracts/pydantic/api.py.
 *
 * ВАЖНО: этот файл поддерживается вручную, поля и типы должны совпадать
 * с pydantic/api.py. При изменении api.v1.yaml обновляйте оба файла
 * в одном PR; в CI-проверке (scripts/check_contract_sync.py — план)
 * расхождение будет ошибкой.
 */

// ─── enums ────────────────────────────────────────────────────────────

export type Role = 'cx_analyst' | 'product_owner' | 'head_of_direction' | 'admin';

export type Platform = 'ios' | 'android';

export type Provider = 'apns' | 'rustore' | 'fcm' | 'hms';

export type BatchState = 'received' | 'queued' | 'labeling' | 'done' | 'failed';

export type CaseStatus =
  | 'new'
  | 'in_progress'
  | 'on_review'
  | 'rejected'
  | 'closed'
  | 'escalated';

export type StrategyModule = 'ingestion' | 'analytics' | 'responses' | 'auth';

// ─── session ──────────────────────────────────────────────────────────

export interface SessionDto {
  employee_id: string;
  full_name?: string;
  roles: Role[];
}

export interface DeviceRegistration {
  token: string;
  platform: Platform;
  provider?: Provider;
}

// ─── feedback ─────────────────────────────────────────────────────────

export interface RawReview {
  external_id?: string;
  source?: string;
  /** minLength: 5, maxLength: 20000 */
  text: string;
  /** 1..5 */
  rating: number;
  /** ISO 8601, таймзона обязательна */
  published_at: string;
  /** Принимается и отбрасывается на сервере (152-ФЗ). */
  author?: string;
}

export interface ReviewBatch {
  batch_id?: string;
  /** minItems: 1, maxItems: 1000 */
  reviews: RawReview[];
}

export interface BatchReport {
  batch_id: string;
  accepted: number;
  rejected: number;
  warnings?: string[];
  markup_queued?: boolean;
}

export interface BatchStatusDto {
  batch_id: string;
  state: BatchState;
  /** 0..100 */
  progress?: number;
}

// ─── analytics ────────────────────────────────────────────────────────

export interface Period {
  /** YYYY-MM-DD */
  from: string;
  /** YYYY-MM-DD */
  to: string;
}

export interface Sentiment {
  positive?: number;
  neutral?: number;
  negative?: number;
}

export interface TopicDynamics {
  date?: string;
  value?: number;
}

export interface Topic {
  topic_id?: string;
  topic_name?: string;
  total?: number;
  dynamics?: TopicDynamics[];
}

export interface DashboardDto {
  period: Period;
  cached: boolean;
  sentiment: Sentiment;
  topics: Topic[];
}

export interface ByDirectionItem {
  direction?: string;
  closed?: number;
}

export interface ReportDto {
  period: Period;
  closed_cases: number;
  avg_reaction_hours: number;
  by_direction?: ByDirectionItem[];
}

// ─── cases ────────────────────────────────────────────────────────────

export interface CaseDto {
  case_id: string;
  review_id?: string;
  topic_id?: string;
  direction?: string;
  owner_id: string;
  status: CaseStatus;
  created_at: string;
  due_at: string;
  escalated?: boolean;
  version: number;
}

export interface StatusChangeRecord {
  at: string;
  from_status: CaseStatus;
  to_status: CaseStatus;
  author_id: string;
  reason?: string;
}

export interface CaseDetailsDto extends CaseDto {
  review_text?: string;
  history?: StatusChangeRecord[];
}

export interface StatusChange {
  to_status: CaseStatus;
  expected_version: number;
  /** Обязательно при to_status=rejected. */
  reason?: string;
}

// ─── dictionaries ─────────────────────────────────────────────────────

export interface DictionaryEntryDto {
  id: string;
  name: string;
  meta?: Record<string, unknown>;
}

// ─── admin ────────────────────────────────────────────────────────────

export interface StrategySwitch {
  module: StrategyModule;
  kind: string;
  name: string;
}