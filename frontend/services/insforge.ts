"use client";

import { createClient } from "@insforge/sdk";

export const insforgeConfig = {
  baseUrl: process.env.NEXT_PUBLIC_INSFORGE_URL ?? "",
  anonKey: process.env.NEXT_PUBLIC_INSFORGE_ANON_KEY ?? "",
};

export function hasInsforgeConfig() {
  return Boolean(insforgeConfig.baseUrl && insforgeConfig.anonKey);
}

export const insforge = createClient({
  baseUrl: insforgeConfig.baseUrl,
  anonKey: insforgeConfig.anonKey,
});
