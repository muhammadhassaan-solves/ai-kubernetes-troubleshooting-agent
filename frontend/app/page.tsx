"use client";

import { FormEvent, useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useInvestigationHistory } from "@/hooks/useInvestigationHistory";
import {
  ProgressStep,
  useInvestigationProgress,
} from "@/hooks/useInvestigationProgress";
import { getClusterContexts, runInvestigation } from "@/services/api";
import type { Diagnosis } from "@/types/investigation";

function statusSymbol(status: ProgressStep["status"]) {
  if (status === "complete") return "OK";
  if (status === "active") return "...";
  if (status === "error") return "!";
  return "-";
}

function friendlyError(error: unknown) {
  if (error instanceof Error && error.message.includes("timeout")) {
    return "The investigation timed out. Verify the backend can reach the selected cluster and try again.";
  }

  if (error instanceof Error) {
    return `Investigation failed: ${error.message}`;
  }

  return "Investigation failed. Please verify cluster access, kubectl permissions, and backend logs.";
}

export default function Home() {
  const {
    user,
    loading,
    authError,
    signIn,
    signOut,
    signUp,
    verifyEmail,
  } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [pendingVerificationEmail, setPendingVerificationEmail] = useState("");
  const [authMode, setAuthMode] = useState<"sign-in" | "sign-up">("sign-in");
  const [authMessage, setAuthMessage] = useState("");
  const [diagnosis, setDiagnosis] = useState<Diagnosis | null>(null);
  const [apiError, setApiError] = useState("");
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [clusters, setClusters] = useState<string[]>([]);
  const [selectedCluster, setSelectedCluster] = useState("");
  const [clustersError, setClustersError] = useState("");
  const { history, historyError, saveInvestigation } = useInvestigationHistory(
    user?.id ?? null,
  );
  const {
    steps,
    completedCount,
    realtimeError,
    startProgress,
    publishProgress,
  } = useInvestigationProgress();

  useEffect(() => {
    if (!user) return;

    async function loadClusters() {
      try {
        const result = await getClusterContexts();
        setClusters(result.contexts);
        setSelectedCluster(result.current_context || result.contexts[0] || "");
        setClustersError(
          result.status === "error"
            ? result.error || "Unable to read kubeconfig contexts."
            : "",
        );
      } catch {
        setClusters([]);
        setSelectedCluster("");
        setClustersError(
          "Unable to load Kubernetes clusters. Verify kubectl and kubeconfig access on the backend.",
        );
      }
    }

    void loadClusters();
  }, [user]);

  async function handleAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthMessage("");

    try {
      if (authMode === "sign-in") {
        await signIn(email, password);
        setAuthMessage("");
      } else {
        const result = await signUp(email, password);
        setAuthMessage(result.message);
        if (result.verificationRequired) {
          setPendingVerificationEmail(email);
          setVerificationCode("");
        }
      }
    } catch {
      setAuthMessage("");
    }
  }

  async function handleVerifyEmail(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthMessage("");

    try {
      await verifyEmail(pendingVerificationEmail, verificationCode);
      setPendingVerificationEmail("");
      setVerificationCode("");
    } catch {
      setAuthMessage("");
    }
  }

  async function handleInvestigate() {
    setApiError("");
    setDiagnosis(null);

    if (!selectedCluster) {
      setApiError(
        "Select a Kubernetes cluster before starting an investigation. If none are listed, verify kubeconfig access on the backend.",
      );
      return;
    }

    setIsInvestigating(true);

    const channel = await startProgress();
    const timeline = ["pods", "logs", "events", "deployments", "network", "ai"];

    let timelineIndex = 0;
    const interval = window.setInterval(() => {
      const key = timeline[timelineIndex];
      if (!key) return;
      void publishProgress(key, "active");
      timelineIndex += 1;
    }, 650);

    try {
      const result = await runInvestigation(channel, selectedCluster);
      window.clearInterval(interval);

      for (const key of timeline) {
        await publishProgress(key, "complete");
      }

      await publishProgress("root-cause", "complete");
      setDiagnosis(result.diagnosis);
      await saveInvestigation(result.diagnosis, result.investigation);
    } catch (error) {
      window.clearInterval(interval);
      await publishProgress("root-cause", "error");
      setApiError(friendlyError(error));
    } finally {
      setIsInvestigating(false);
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-50 px-6 py-10 text-slate-950">
        <section className="mx-auto max-w-5xl">
          <h1 className="text-3xl font-semibold">AI Kubernetes Agent</h1>
          <p className="mt-4 text-slate-600">Loading session...</p>
        </section>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="min-h-screen bg-slate-50 px-6 py-10 text-slate-950">
        <section className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-md flex-col justify-center">
          <h1 className="text-3xl font-semibold">AI Kubernetes Agent</h1>
          <p className="mt-2 text-slate-600">
            Sign in to investigate your cluster and view diagnosis history.
          </p>

          {pendingVerificationEmail ? (
            <form
              onSubmit={handleVerifyEmail}
              className="mt-8 border border-slate-200 bg-white p-6 shadow-sm"
            >
              <h2 className="text-lg font-semibold">Verify Email</h2>
              <p className="mt-2 text-sm text-slate-600">
                Enter the verification code sent to {pendingVerificationEmail}.
              </p>

              <label className="mt-5 block text-sm font-medium text-slate-700">
                Verification Code
                <input
                  type="text"
                  value={verificationCode}
                  onChange={(event) => setVerificationCode(event.target.value)}
                  required
                  inputMode="numeric"
                  minLength={6}
                  maxLength={6}
                  className="mt-2 w-full border border-slate-300 px-3 py-2 tracking-widest outline-none focus:border-cyan-700"
                />
              </label>

              <button
                type="submit"
                className="mt-6 w-full bg-slate-950 px-4 py-3 text-sm font-semibold text-white transition hover:bg-cyan-700"
              >
                Verify and Continue
              </button>

              <button
                type="button"
                onClick={() => {
                  setPendingVerificationEmail("");
                  setVerificationCode("");
                  setAuthMode("sign-in");
                }}
                className="mt-3 w-full border border-slate-300 px-4 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-950 hover:text-slate-950"
              >
                Back to Sign In
              </button>

              {(authError || authMessage) && (
                <p className="mt-4 text-sm text-slate-700">
                  {authError || authMessage}
                </p>
              )}
            </form>
          ) : (
            <form
              onSubmit={handleAuth}
              className="mt-8 border border-slate-200 bg-white p-6 shadow-sm"
            >
              <div className="grid grid-cols-2 border border-slate-200 text-sm font-medium">
                <button
                  type="button"
                  onClick={() => setAuthMode("sign-in")}
                  className={`px-3 py-2 ${authMode === "sign-in" ? "bg-slate-950 text-white" : "bg-white text-slate-700"}`}
                >
                  Sign In
                </button>
                <button
                  type="button"
                  onClick={() => setAuthMode("sign-up")}
                  className={`px-3 py-2 ${authMode === "sign-up" ? "bg-slate-950 text-white" : "bg-white text-slate-700"}`}
                >
                  Sign Up
                </button>
              </div>

              <label className="mt-5 block text-sm font-medium text-slate-700">
                Email
                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  className="mt-2 w-full border border-slate-300 px-3 py-2 outline-none focus:border-cyan-700"
                />
              </label>

              <label className="mt-4 block text-sm font-medium text-slate-700">
                Password
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  minLength={8}
                  className="mt-2 w-full border border-slate-300 px-3 py-2 outline-none focus:border-cyan-700"
                />
              </label>

              <button
                type="submit"
                className="mt-6 w-full bg-slate-950 px-4 py-3 text-sm font-semibold text-white transition hover:bg-cyan-700"
              >
                {authMode === "sign-in" ? "Sign In" : "Create Account"}
              </button>

              {(authError || authMessage) && (
                <p className="mt-4 text-sm text-slate-700">
                  {authError || authMessage}
                </p>
              )}
            </form>
          )}
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50 px-6 py-8 text-slate-950">
      <section className="mx-auto max-w-6xl">
        <header className="flex flex-col gap-4 border-b border-slate-200 pb-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-semibold">AI Kubernetes Agent</h1>
            <p className="mt-1 text-sm text-slate-600">{user.email}</p>
          </div>
          <button
            type="button"
            onClick={() => void signOut()}
            className="w-fit border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-950 hover:text-slate-950"
          >
            Sign Out
          </button>
        </header>

        <div className="grid gap-6 py-8 lg:grid-cols-[1fr_360px]">
          <section className="space-y-6">
            <div className="border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h2 className="text-xl font-semibold">Investigation</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    Choose a kubeconfig context, then run evidence collection and
                    AI reasoning.
                  </p>
                </div>
                <div className="flex w-full flex-col gap-3 sm:w-80">
                  <label className="text-sm font-medium text-slate-700">
                    Kubernetes Cluster
                    <select
                      value={selectedCluster}
                      onChange={(event) => setSelectedCluster(event.target.value)}
                      className="mt-2 w-full border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-cyan-700"
                    >
                      {clusters.length > 0 ? (
                        clusters.map((cluster) => (
                          <option key={cluster} value={cluster}>
                            {cluster}
                          </option>
                        ))
                      ) : (
                        <option value="">No kubeconfig contexts found</option>
                      )}
                    </select>
                  </label>
                  <button
                    type="button"
                    onClick={() => void handleInvestigate()}
                    disabled={isInvestigating || !selectedCluster}
                    className="min-h-11 bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-cyan-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                  >
                    {isInvestigating ? "Investigating..." : "Investigate Cluster"}
                  </button>
                </div>
              </div>

              {clustersError && (
                <p className="mt-4 text-sm text-amber-700">{clustersError}</p>
              )}
              {isInvestigating && (
                <p className="mt-4 text-sm font-medium text-cyan-700">
                  Investigating Kubernetes Cluster...
                </p>
              )}

              <div className="mt-6">
                <div className="mb-3 flex items-center justify-between text-sm">
                  <span className="font-medium">Investigation Status</span>
                  <span className="text-slate-500">
                    {completedCount}/{steps.length}
                  </span>
                </div>
                <div className="space-y-2">
                  {steps.map((step) => (
                    <div
                      key={step.key}
                      className="flex items-center gap-3 border border-slate-200 px-3 py-2 text-sm"
                    >
                      <span
                        className={`flex h-6 w-8 items-center justify-center text-xs font-semibold ${
                          step.status === "complete"
                            ? "text-emerald-700"
                            : step.status === "active"
                              ? "text-cyan-700"
                              : step.status === "error"
                                ? "text-red-700"
                                : "text-slate-400"
                        }`}
                      >
                        {statusSymbol(step.status)}
                      </span>
                      <span>{step.label}</span>
                    </div>
                  ))}
                </div>
                {realtimeError && (
                  <p className="mt-3 text-sm text-amber-700">{realtimeError}</p>
                )}
                {apiError && (
                  <p className="mt-3 text-sm text-red-700">{apiError}</p>
                )}
              </div>
            </div>

            <div className="border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-xl font-semibold">Diagnosis</h2>
              {diagnosis ? (
                <div className="mt-5 space-y-5">
                  <div>
                    <p className="text-sm font-medium text-slate-500">
                      Root Cause
                    </p>
                    <p className="mt-1 text-lg font-semibold">
                      {diagnosis.root_cause}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-500">
                      Explanation
                    </p>
                    <p className="mt-1 text-slate-700">
                      {diagnosis.explanation}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-500">
                      Suggested Fix
                    </p>
                    <p className="mt-1 text-slate-700">{diagnosis.fix}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-500">
                      kubectl Command
                    </p>
                    <code className="mt-2 block overflow-x-auto bg-slate-950 px-3 py-3 text-sm text-white">
                      {diagnosis.kubectl_command || "No command suggested"}
                    </code>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-500">
                      Confidence
                    </p>
                    <p className="mt-1 text-2xl font-semibold">
                      {diagnosis.confidence}%
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                      {diagnosis.confidence_reasoning}
                    </p>
                  </div>
                </div>
              ) : (
                <p className="mt-4 text-sm text-slate-600">
                  Run an investigation to see the root cause analysis. If no
                  issue is found, the diagnosis will show that the cluster
                  appears healthy.
                </p>
              )}
            </div>
          </section>

          <aside className="border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold">Recent Investigations</h2>
            {historyError && (
              <p className="mt-3 text-sm text-amber-700">{historyError}</p>
            )}
            <div className="mt-5 overflow-hidden border border-slate-200">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-100 text-slate-600">
                  <tr>
                    <th className="px-3 py-2 font-medium">Root Cause</th>
                    <th className="px-3 py-2 font-medium">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {history.length > 0 ? (
                    history.map((item) => (
                      <tr key={item.id} className="border-t border-slate-200">
                        <td className="px-3 py-3">
                          <p className="font-medium">{item.root_cause}</p>
                          <p className="mt-1 text-xs text-slate-500">
                            {item.namespace ?? "all namespaces"}
                          </p>
                        </td>
                        <td className="px-3 py-3">{item.confidence}%</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td className="px-3 py-4 text-slate-500" colSpan={2}>
                        No investigations yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}
