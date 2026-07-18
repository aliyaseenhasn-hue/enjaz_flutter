import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { User, LoginData, RegisterData } from '../types';
import { authApi } from '../api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  updateUser: (data: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const userData = await authApi.getProfile();
      setUser(userData);
    } catch {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = async (data: LoginData) => {
    const res = await authApi.login(data);
    localStorage.setItem('access_token', res.access);
    localStorage.setItem('refresh_token', res.refresh);

    // تحميل بيانات المستخدم بعد تسجيل الدخول
    try {
      const userData = await authApi.getProfile();
      setUser(userData);
    } catch {
      // إذا فشل تحميل البروفايل، نستخدم البيانات المتاحة من الاستجابة
      if (res.user) {
        setUser(res.user);
      }
    }
  };

  const register = async (data: RegisterData) => {
    const res = await authApi.register(data);
    localStorage.setItem('access_token', res.access);
    localStorage.setItem('refresh_token', res.refresh);

    // تحميل بيانات المستخدم بعد التسجيل
    try {
      const userData = await authApi.getProfile();
      setUser(userData);
    } catch {
      if (res.user) {
        setUser(res.user);
      }
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const updateUser = (data: Partial<User>) => {
    if (user) {
      setUser({ ...user, ...data });
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        updateUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};