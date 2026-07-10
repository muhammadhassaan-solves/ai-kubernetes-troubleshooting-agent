import { useQuery } from "@tanstack/react-query";
import { getHealthStatus } from "@/services/api";

export function useHealthStatus() {
  return useQuery({
    queryKey: ["health"],
    queryFn: getHealthStatus,
    enabled: false,
  });
}

