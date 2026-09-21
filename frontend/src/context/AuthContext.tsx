import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../api/client';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isLoading: boolean;
  login: (credentials: { email: string; password: string }) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('adani_auth_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('adani_auth_token');
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('adani_auth_token');
      if (storedToken) {
        try {
          const profile = await api.getMe();
          setUser(profile);
          localStorage.setItem('adani_auth_user', JSON.stringify(profile));
        } catch (err) {
          console.error('Session expired or invalid token:', err);
          logout();
        }
      }
      setIsLoading(false);
    };
    initAuth();
  }, []);

  const login = async (credentials: { email: string; password: string }) => {
    const res = await api.login(credentials);
    setToken(res.access_token);
    setUser(res.user as User);
    localStorage.setItem('adani_auth_token', res.access_token);
    localStorage.setItem('adani_auth_user', JSON.stringify(res.user));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('adani_auth_token');
    localStorage.removeItem('adani_auth_user');
  };

  const refreshUser = async () => {
    try {
      const profile = await api.getMe();
      setUser(profile);
      localStorage.setItem('adani_auth_user', JSON.stringify(profile));
    } catch (err) {
      console.error('Failed to refresh user profile:', err);
    }
  };

  const isAdmin = user?.role?.toUpperCase() === 'ADMIN';

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isAdmin,
        isLoading,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
