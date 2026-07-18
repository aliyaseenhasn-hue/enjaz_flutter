import client from './client';
import type { AdminStats, AdminUser } from '../types';

export const adminApi = {
  getStats: async (): Promise<AdminStats> => {
    const res = await client.get('/api/admin/stats/');
    return res.data;
  },

  getUsers: async (): Promise<AdminUser[]> => {
    const res = await client.get('/api/admin/all-users/');
    return res.data;
  },

  approveAgent: async (userId: number): Promise<void> => {
    await client.post(`/api/admin/agents/${userId}/approve/`);
  },

  rejectAgent: async (userId: number): Promise<void> => {
    await client.post(`/api/admin/agents/${userId}/reject/`);
  },
};