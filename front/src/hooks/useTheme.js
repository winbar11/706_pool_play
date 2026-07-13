import { useQuery } from "@tanstack/react-query";
import { api } from "../utils/api.js";

export function useTheme() {
  const { data } = useQuery({
    queryKey: ["settings"],
    queryFn: api.settings.get,
    staleTime: 60_000,
  });
  return data?.theme ?? localStorage.getItem("theme") ?? "masters";
}
