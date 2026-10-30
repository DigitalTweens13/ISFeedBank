/**
 * Контракты сообщений брокера.
 *
 * Источники:
 * - docs/packages/contracts/events/reviews.labeling.v1.json
 * - docs/packages/contracts/events/cases.events.v1.json
 *
 * Python-зеркало: docs/packages/contracts/pydantic/events.py.
 * Обновляется вручную в одном PR с JSON-схемами.
 */

// ─── reviews.labeling.v1 ──────────────────────────────────────────────

export type Source =
  | 'banki_ru'
  | 'sravni_ru'
  | 'app_store'
  | 'google_play'
  | 'file_import'
  | 'api_batch';

export interface ReviewsLabelingTaskV1 {
  /** UUID отзыва в БД */
  review_id: string;
  /** Обезличенный текст, 1..20000 символов */
  text: string;
  source: Source;
  /** 1..5 */
  rating: number;
  /** ISO 8601, таймзона обязательна */
  published_at: string;
  /** UUID пакета; отсутствует для отзывов из расписания */
  batch_id?: string;
}

// ─── cases.events.v1 ──────────────────────────────────────────────────

export type EventType = 'case_created' | 'case_escalated' | 'case_closed';

export type Severity = 'critical' | 'high' | 'medium' | 'low';

export interface CasesEventV1 {
  event_type: EventType;
  /** UUID обращения */
  case_id: string;
  /** UUID отзыва */
  review_id: string;
  /** ISO 8601, таймзона обязательна */
  occurred_at: string;
  severity?: Severity;
  direction?: string;
}