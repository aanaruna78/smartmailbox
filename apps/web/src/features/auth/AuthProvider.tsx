import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { config } from '../../config';

interface User {
  email: string;
  role: string;
  full_name?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: () => void; // Just triggers re-fetch
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(
    config.auth.bypassAuth
      ? { email: 'test@example.com', role: 'admin', full_name: 'Test User' }
      : null,
  );
  const [loading, setLoading] = useState(!config.auth.bypassAuth);

  const fetchUser = async () => {
    if (config.auth.bypassAuth) {
      setLoading(false);
      return;
    }
    try {
      const token = localStorage.getItem('token');
      const headers: Record<string, string> = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const res = await fetch(`${config.api.baseUrl}/auth/me`, {
        headers,
        credentials: 'include',
      });
      if (res.ok) {
        const userData = await res.json();
        setUser(userData);
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const login = () => {
    fetchUser();
  };

  const logout = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers: Record<string, string> = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      await fetch(`${config.api.baseUrl}/auth/logout`, {
        method: 'POST',
        headers,
        credentials: 'include',
      });
      localStorage.removeItem('token'); // Clear token on logout
      setUser(null);
    } catch (error) {
      console.error('Logout failed', error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, isAuthenticated: !!user }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
