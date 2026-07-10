"use client";

import { useCallback, useEffect, useState } from "react";
import { insforge } from "@/services/insforge";
import type { Diagnosis, InvestigationHistoryItem } from "@/types/investigation";

function getNamespace(investigation: Record<string, unknown>): string | null {
  const pods = investigation.pods as
    | { problematic_pods?: Array<{ namespace?: string }> }
    | undefined;
  const events = investigation.events as
    | { findings?: Array<{ namespace?: string }> }
    | undefined;
  const deployments = investigation.deployments as
    | { unhealthy_deployments?: Array<{ namespace?: string }> }
    | undefined;
  const network = investigation.network as
    | { issues?: Array<{ namespace?: string }> }
    | undefined;

  return (
    pods?.problematic_pods?.[0]?.namespace ??
    events?.findings?.[0]?.namespace ??
    deployments?.unhealthy_deployments?.[0]?.namespace ??
    network?.issues?.[0]?.namespace ??
    "all namespaces"
  );
}

export function useInvestigationHistory(userId: string | null) {
  const [history, setHistory] = useState<InvestigationHistoryItem[]>([]);
  const [historyError, setHistoryError] = useState("");

  const loadHistory = useCallback(async () => {
    if (!userId) return;

    const { data, error } = await insforge.database
      .from("investigations")
      .select("id, root_cause, namespace, confidence, status, created_at")
      .order("created_at", { ascending: false })
      .limit(8);

    if (error) {
      setHistoryError(error.message ?? "Could not load investigation history");
      return;
    }

    setHistory((data ?? []) as InvestigationHistoryItem[]);
    setHistoryError("");
  }, [userId]);

  const saveInvestigation = useCallback(
    async (
      diagnosis: Diagnosis,
      investigation: Record<string, unknown>,
    ) => {
      if (!userId) return;

      const { error } = await insforge.database.from("investigations").insert([
        {
          user_id: userId,
          root_cause: diagnosis.root_cause,
          namespace: getNamespace(investigation),
          confidence: diagnosis.confidence,
          status: "completed",
        },
      ]);

      if (error) {
        setHistoryError(error.message ?? "Could not save investigation");
        return;
      }

      await loadHistory();
    },
    [loadHistory, userId],
  );

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  return {
    history,
    historyError,
    loadHistory,
    saveInvestigation,
  };
}
