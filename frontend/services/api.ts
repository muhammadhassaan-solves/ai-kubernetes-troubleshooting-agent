import axios from "axios";
import type { HealthResponse } from "@/types/health";
import type {
  ClusterContextsResponse,
  InvestigationResponse,
} from "@/types/investigation";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  timeout: 120000,
});

export async function getHealthStatus(): Promise<HealthResponse> {
  const response = await api.get<HealthResponse>("/health");
  return response.data;
}

export async function runInvestigation(
  realtimeChannel?: string,
  kubeContext?: string,
): Promise<InvestigationResponse> {
  const response = await api.post<InvestigationResponse>("/investigate", {
    realtime_channel: realtimeChannel,
    kube_context: kubeContext,
  });
  return response.data;
}

export async function getClusterContexts(): Promise<ClusterContextsResponse> {
  const response = await api.get<ClusterContextsResponse>("/clusters");
  return response.data;
}

export default api;
