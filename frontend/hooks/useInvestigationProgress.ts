"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { insforge } from "@/services/insforge";

export type ProgressStatus = "pending" | "active" | "complete" | "error";

export type ProgressStep = {
  key: string;
  label: string;
  status: ProgressStatus;
};

const STEP_LABELS = [
  ["pods", "Checking Pods"],
  ["logs", "Reading Logs"],
  ["events", "Analyzing Events"],
  ["deployments", "Inspecting Deployments"],
  ["network", "Checking Networking"],
  ["ai", "AI Reasoning"],
  ["root-cause", "Root Cause Found"],
] as const;

function initialSteps(): ProgressStep[] {
  return STEP_LABELS.map(([key, label]) => ({
    key,
    label,
    status: "pending",
  }));
}

export function useInvestigationProgress() {
  const [steps, setSteps] = useState<ProgressStep[]>(initialSteps);
  const [channel, setChannel] = useState("");
  const [realtimeError, setRealtimeError] = useState("");
  const channelRef = useRef("");

  const completedCount = useMemo(
    () => steps.filter((step) => step.status === "complete").length,
    [steps],
  );

  const markStep = useCallback((key: string, status: ProgressStatus) => {
    setSteps((current) =>
      current.map((step) =>
        step.key === key
          ? { ...step, status }
          : step.status === "active" && status === "active"
            ? { ...step, status: "complete" }
            : step,
      ),
    );
  }, []);

  const publishProgress = useCallback(
    async (key: string, status: ProgressStatus) => {
      markStep(key, status);

      const currentChannel = channelRef.current;
      if (!currentChannel) return;

      try {
        await insforge.realtime.publish(currentChannel, "investigation_progress", {
          key,
          status,
        });
      } catch {
        setRealtimeError("Realtime progress is unavailable; showing local progress.");
      }
    },
    [markStep],
  );

  const startProgress = useCallback(async () => {
    const nextChannel = `investigation:${crypto.randomUUID()}`;
    setChannel(nextChannel);
    channelRef.current = nextChannel;
    setSteps(initialSteps());
    setRealtimeError("");

    try {
      await insforge.realtime.connect();
      const response = await insforge.realtime.subscribe(nextChannel);
      if (!response.ok) {
        setRealtimeError(response.error?.message ?? "Realtime subscription failed");
      }
    } catch {
      setRealtimeError("Realtime progress is unavailable; showing local progress.");
    }

    return nextChannel;
  }, []);

  useEffect(() => {
    const handler = (payload: { key?: string; status?: ProgressStatus }) => {
      if (!payload.key || !payload.status) return;
      markStep(payload.key, payload.status);
    };

    insforge.realtime.on("investigation_progress", handler);
    return () => {
      insforge.realtime.off("investigation_progress", handler);
      if (channel) {
        insforge.realtime.unsubscribe(channel);
      }
    };
  }, [channel, markStep]);

  return {
    channel,
    steps,
    completedCount,
    realtimeError,
    startProgress,
    publishProgress,
  };
}
