import client from './client';
import type { LoginData, RegisterData, AuthResponse, User } from '../types';

export const authApi = {
  login: async (data: LoginData): Promise<AuthResponse> => {
    const res = await client.post('/auth/login/', {
      phone_number: data.phone_number,
      password: data.password,
    });
    return res.data;
  },

  register: async (data: RegisterData): Promise<AuthResponse> => {
    const res = await client.post('/auth/register/', {
      phone_number: data.phone_number,
      password: data.password,
      password_confirm: data.password_confirm,
      first_name: data.first_name,
      last_name: data.last_name,
      role: data.role || 'customer',
    });
    return res.data;
  },

  loginWithGoogle: async (token: string): Promise<AuthResponse> => {
    const res = await client.post('/auth/google/', { token });
    return res.data;
  },

  getProfile: async (): Promise<User> => {
    const res = await client.get('/auth/profile/');
    const data = res.data;
    // تعيين full_name من الحقول المتاحة
    return {
      ...data,
      full_name: data.full_name || `${data.first_name || ''} ${data.last_name || ''}`.trim(),
      username: data.username || data.phone_number,
      phone_number: data.phone_number || data.username,
      avatar: data.avatar_url || data.avatar,
      avatar_url: data.avatar_url || data.avatar,
      email: data.email || '',
      city: data.location || data.city,
      location: data.location || data.city,
      rating: data.agent_profile?.rating || data.rating || 0,
      completed_orders: data.agent_profile?.total_jobs || data.completed_orders || 0,
      is_verified: data.agent_profile?.is_verified || data.is_verified || false,
      is_agent_approved: data.agent_profile?.verification_status === 'approved',
      bio: data.agent_profile?.bio || data.bio || '',
      profession: data.agent_profile?.profession_display || data.profession || '',
    } as User;
  },

  updateProfile: async (data: Partial<User>): Promise<User> => {
    const res = await client.patch('/auth/profile/', data);
    return res.data;
  },

  changePassword: async (oldPassword: string, newPassword: string): Promise<void> => {
    await client.post('/auth/profile/change-password/', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },

  sendVerificationCode: async (phone: string): Promise<void> => {
    await client.post('/auth/send-verification-code/', { phone_number: phone });
  },

  verifyPhone: async (code: string, newPassword?: string, confirmPassword?: string): Promise<void> => {
    await client.post('/auth/verify-phone/', {
      code,
      new_password: newPassword,
      confirm_password: confirmPassword,
    });
  },
};