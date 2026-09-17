import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "./AuthContext";
import type { Role } from "../types/auth";

export function RequireRole({ roles, children }: { roles: Role[]; children: ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) return null;
  if (!user) return <Navigate to="/" replace />;
  if (!roles.includes(user.role)) return <Navigate to="/" replace />;

  return <>{children}</>;
}
