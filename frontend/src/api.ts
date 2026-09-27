const BASE = import.meta.env.VITE_API_URL || '';
export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE}${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...options.headers } });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(typeof data?.detail === 'string' ? data.detail : `Không thực hiện được yêu cầu (${response.status}).`);
  }
  return response.status === 204 ? undefined as T : await response.json() as T;
}
export function workspace(tenant: string) { return tenant ? `?tenant_id=${encodeURIComponent(tenant)}` : ''; }
