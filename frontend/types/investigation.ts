export type Diagnosis = {
  root_cause: string;
  explanation: string;
  fix: string;
  kubectl_commands: string[];
  kubectl_command: string;
  prevention: string;
  confidence: number;
  confidence_reasoning: string;
};

export type InvestigationResponse = {
  status: string;
  diagnosis: Diagnosis;
  investigation: Record<string, unknown>;
};

export type ClusterContextsResponse = {
  status: string;
  contexts: string[];
  current_context: string;
  error: string;
};

export type InvestigationHistoryItem = {
  id: string;
  root_cause: string;
  namespace: string | null;
  confidence: number;
  status: string;
  created_at: string;
};
