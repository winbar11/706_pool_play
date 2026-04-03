import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "./context/AuthContext.js";
import Layout from "./components/Layout.js";
import LoginPage from "./pages/LoginPage.js";
import RegisterPage from "./pages/RegisterPage.js";
import LeaderboardPage from "./pages/LeaderboardPage.js";
import DraftPage from "./pages/DraftPage.js";
import MyTeamPage from "./pages/MyTeamPage.js";
import AdminPage from "./pages/AdminPage.js";
import RulesPage from "./pages/RulesPage.js";
import "./index.css";

const qc = new QueryClient({ defaultOptions: { queries: { staleTime: 60_000 } } });

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
          <Routes>
            <Route path="/login"    element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
              <Route index element={<LeaderboardPage />} />
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