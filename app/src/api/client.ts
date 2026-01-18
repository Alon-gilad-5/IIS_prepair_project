/** API client for PrepAIr backend. */

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BACKEND_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Users
  ensureUser: (userId?: string) =>
    apiRequest<{ user_id: string }>('/api/users/ensure', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    }),

  // CV
  ingestCV: (userId: string, cvText: string) =>
    apiRequest<{ cv_version_id: string }>('/api/cv/ingest', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, cv_text: cvText }),
    }),

  analyzeCV: (userId: string, cvVersionId: string, jobSpecId: string) =>
    apiRequest<{
      match_score: number;
      strengths: string[];
      gaps: string[];
      suggestions: string[];
      role_focus: any;
    }>('/api/cv/analyze', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, cv_version_id: cvVersionId, job_spec_id: jobSpecId }),
    }),

  saveCV: (userId: string, updatedCvText: string, parentCvVersionId?: string) =>
    apiRequest<{ new_cv_version_id: string }>('/api/cv/save', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, updated_cv_text: updatedCvText, parent_cv_version_id: parentCvVersionId }),
    }),

  // JD
  ingestJD: (userId: string, jdText: string) =>
    apiRequest<{ job_spec_id: string; jd_hash: string; jd_profile_json?: any }>('/api/jd/ingest', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, jd_text: jdText }),
    }),

  // Interview
  startInterview: (userId: string, jobSpecId: string, cvVersionId: string | null, mode: string, settings?: any) =>
    apiRequest<{
      session_id: string;
      plan_summary: any;
      first_question: any;
      total_questions: number;
    }>('/api/interview/start', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        job_spec_id: jobSpecId,
        cv_version_id: cvVersionId,
        mode,
        settings: settings || { num_open: 4, num_code: 2, duration_minutes: 12 },
      }),
    }),

  nextInterview: (sessionId: string, userTranscript: string, userCode?: string, isFollowup?: boolean) =>
    apiRequest<{
      interviewer_message: string;
      followup_question?: { text: string };
      next_question?: any;
      is_done: boolean;
      progress: { turn_index: number; total: number };
    }>('/api/interview/next', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        user_transcript: userTranscript,
        user_code: userCode,
        is_followup: isFollowup,
      }),
    }),

  endInterview: (sessionId: string) =>
    apiRequest<{ ok: boolean }>('/api/interview/end', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
    }),

  // Progress
  getProgressOverview: (userId: string, jobSpecId?: string) =>
    apiRequest<{
      latest_snapshot?: any;
      trend: any[];
      breakdown: any;
    }>(`/api/progress/overview?user_id=${userId}${jobSpecId ? `&job_spec_id=${jobSpecId}` : ''}`),
};
