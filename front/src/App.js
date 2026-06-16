import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "./context/AuthContext.js";
import { api } from "./utils/api.js";
import Layout from "./components/Layout.js";
import LoginPage from "./pages/LoginPage.js";
import RegisterPage from "./pages/RegisterPage.js";
import ForgotPasswordPage from "./pages/ForgotPasswordPage.js";
import ResetPasswordPage from "./pages/ResetPasswordPage.js";
import LeaderboardPage from "./pages/LeaderboardPage.js";
import DraftPage from "./pages/DraftPage.js";
import MyTeamPage from "./pages/MyTeamPage.js";
import AdminPage from "./pages/AdminPage.js";
import RulesPage from "./pages/RulesPage.js";
import WelcomePage from "./pages/WelcomePage.js";
import "./index.css";

const qc = new QueryClient({ defaultOptions: { queries: { staleTime: 60_000 } } });

function ThemeSync() {
  const { data } = useQuery({
    queryKey: ["settings"],
    queryFn: api.settings.get,
    staleTime: 60_000,
  });
  useEffect(() => {
    const theme = data?.theme ?? localStorage.getItem("theme") ?? "masters";
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", theme === "us-open" ? "#002855" : "#0a1f0a");
  }, [data]);
  return null;
}

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading-screen"><span className="loader" /></div>;
  return user ? children : <Navigate to="/login" />;
}

function AdminRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading-screen"><span className="loader" /></div>;
  if (!user) return <Navigate to="/login" />;
  if (!user.is_admin) return <Navigate to="/" />;
  return children;
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <BrowserRouter>
          <ThemeSync />
          <Routes>
            <Route path="/welcome"  element={<Navigate to="/" />} />
            <Route path="/login"           element={<LoginPage />} />
            <Route path="/register"        element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password"  element={<ResetPasswordPage />} />
            <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
              <Route index element={<WelcomePage />} />
              <Route path="leaderboard" element={<LeaderboardPage />} />
              <Route path="draft"   element={<DraftPage />} />
              <Route path="my-team" element={<MyTeamPage />} />
              <Route path="rules"   element={<RulesPage />} />
              <Route path="admin"   element={<AdminRoute><AdminPage /></AdminRoute>} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}