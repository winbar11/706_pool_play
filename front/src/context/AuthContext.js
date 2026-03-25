import React, { createContext, useContext, useState, useEffect } from "react";
import { api } from "../utils/api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("masters_token");
    if (token) {
      api.auth.me()
        .then(setUser)
        .catch(() => localStorage.removeItem("masters_token"))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username, password) => {
    const data = await api.auth.login(username, password);
    localStorage.setItem("masters_token", data.token);
    setUser({ username: data.username, is_admin: data.is_admin, user_id: data.user_id });
    return data;
  };

  const register = async (username, email, password) => {
    const data = await api.auth.register(username, email, password);
    localStorage.setItem("masters_token", data.token);
    setUser({ username: data.username, is_admin: data.is_admin, user_id: data.user_id });
    return data;
  };

  const logout = () => {
    localStorage.removeItem("masters_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}