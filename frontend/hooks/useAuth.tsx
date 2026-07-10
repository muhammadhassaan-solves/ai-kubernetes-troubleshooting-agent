"use client";

import type { ReactNode } from "react";
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { hasInsforgeConfig, insforge } from "@/services/insforge";

type AuthUser = {
  id: string;
  email?: string;
};

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  authError: string;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<{
    message: string;
    verificationRequired: boolean;
  }>;
  verifyEmail: (email: string, otp: string) => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function hydrateAuth() {
      if (!hasInsforgeConfig()) {
        if (!cancelled) {
          setAuthError(
            "InsForge is not configured. Set NEXT_PUBLIC_INSFORGE_URL and NEXT_PUBLIC_INSFORGE_ANON_KEY, then rebuild the frontend container.",
          );
          setLoading(false);
        }
        return;
      }

      const { data, error } = await insforge.auth.getCurrentUser();
      if (cancelled) return;

      setUser(error ? null : ((data?.user as AuthUser | undefined) ?? null));
      setLoading(false);
    }

    void hydrateAuth();

    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      authError,
      async signIn(email: string, password: string) {
        setAuthError("");
        if (!hasInsforgeConfig()) {
          const message =
            "InsForge is not configured. Set NEXT_PUBLIC_INSFORGE_URL and NEXT_PUBLIC_INSFORGE_ANON_KEY, then rebuild the frontend container.";
          setAuthError(message);
          throw new Error(message);
        }

        const { data, error } = await insforge.auth.signInWithPassword({
          email,
          password,
        });

        if (error) {
          setAuthError(error.message ?? "Sign in failed");
          throw error;
        }

        setUser((data?.user as AuthUser | undefined) ?? null);
      },
      async signUp(email: string, password: string) {
        setAuthError("");
        if (!hasInsforgeConfig()) {
          const message =
            "InsForge is not configured. Set NEXT_PUBLIC_INSFORGE_URL and NEXT_PUBLIC_INSFORGE_ANON_KEY, then rebuild the frontend container.";
          setAuthError(message);
          throw new Error(message);
        }

        const { data, error } = await insforge.auth.signUp({
          email,
          password,
          redirectTo: window.location.origin,
        });

        if (error) {
          setAuthError(error.message ?? "Sign up failed");
          throw error;
        }

        if (data?.requireEmailVerification) {
          return {
            message: "Account created. Enter the verification code from your email.",
            verificationRequired: true,
          };
        }

        setUser((data?.user as AuthUser | undefined) ?? null);
        return {
          message: "Account created.",
          verificationRequired: false,
        };
      },
      async verifyEmail(email: string, otp: string) {
        setAuthError("");
        if (!hasInsforgeConfig()) {
          const message =
            "InsForge is not configured. Set NEXT_PUBLIC_INSFORGE_URL and NEXT_PUBLIC_INSFORGE_ANON_KEY, then rebuild the frontend container.";
          setAuthError(message);
          throw new Error(message);
        }

        const { data, error } = await insforge.auth.verifyEmail({
          email,
          otp,
        });

        if (error) {
          setAuthError(error.message ?? "Email verification failed");
          throw error;
        }

        setUser((data?.user as AuthUser | undefined) ?? null);
      },
      async signOut() {
        setAuthError("");
        await insforge.auth.signOut();
        setUser(null);
      },
    }),
    [authError, loading, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
