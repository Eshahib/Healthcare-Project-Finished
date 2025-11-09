/**
 * API Client for connecting to the backend
 */

const API_BASE_URL = 'http://localhost:8000/api';

// Token storage
export function getToken(): string | null {
  return localStorage.getItem('auth_token')
}

export function setToken(token: string): void {
  localStorage.setItem('auth_token', token)
}

export function removeToken(): void {
  localStorage.removeItem('auth_token')
}

export interface UserResponse {
  id: number
  username: string
  email: string | null
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

/**
 * Register a new user
 */
export async function register(
  username: string,
  email: string | undefined,
  password: string
): Promise<UserResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      username,
      email: email || null,
      password,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Registration failed' }))
    throw new Error(error.detail || `HTTP error! status: ${response.status}`)
  }

  return response.json()
}

/**
 * Login and get access token
 */
export async function login(username: string, password: string): Promise<string> {
  const formData = new URLSearchParams()
  formData.append('username', username)
  formData.append('password', password)

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Login failed' }))
    throw new Error(error.detail || `HTTP error! status: ${response.status}`)
  }

  const data: TokenResponse = await response.json()
  setToken(data.access_token)
  return data.access_token
}

/**
 * Get current user information
 */
export async function getCurrentUser(): Promise<UserResponse> {
  const token = getToken()
  if (!token) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    if (response.status === 401) {
      removeToken()
    }
    const error = await response.json().catch(() => ({ detail: 'Failed to get user' }))
    throw new Error(error.detail || `HTTP error! status: ${response.status}`)
  }

  return response.json()
}

export interface SymptomEntryRequest {
  symptoms: string[];
  comments?: string;
  user_id?: number;
  user_email? : string;
}

export interface SymptomEntryResponse {
  id: number;
  user_id: number | null;
  symptoms: string[];
  comments: string | null;
  created_at: string;
}

export interface DiagnosisResponse {
  id: number;
  symptom_entry_id: number;
  diagnosis_text: string;
  confidence_score: string | null;
  possible_conditions: string[] | null;
  recommendations: string | null;
  created_at: string;
}

export interface SymptomEntryWithDiagnosis extends SymptomEntryResponse {
  diagnosis: DiagnosisResponse | null;
  diagnosis_text: string | null;
}

/**
 * Create a new symptom entry
 */
export async function createSymptomEntry(
  data: SymptomEntryRequest
): Promise<SymptomEntryResponse> {
  const token = getToken()
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}/symptoms`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * Get a symptom entry by ID
 */
export async function getSymptomEntry(
  symptomId: number
): Promise<SymptomEntryWithDiagnosis> {
  const response = await fetch(`${API_BASE_URL}/symptoms/${symptomId}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * Create a diagnosis for a symptom entry
 */
export async function createDiagnosis(data: {
  symptom_entry_id: number;
  diagnosis_text: string;
  confidence_score?: string;
  possible_conditions?: string[];
  recommendations?: string;
}): Promise<DiagnosisResponse> {
  const response = await fetch(`${API_BASE_URL}/diagnoses`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

