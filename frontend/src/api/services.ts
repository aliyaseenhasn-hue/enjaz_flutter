import client from './client';
import type { Category, ServiceRequest, CreateRequestData } from '../types';

export interface Agent {
  id: number;
  full_name: string;
  phone_number: string;
  avatar: string | null;
  profession: string;
  profession_display: string;
  city: string;
  rating: number;
  total_jobs: number;
  bio: string;
  is_verified: boolean;
  lat: number;
  lon: number;
  distance_km: number;
  service_min_price: number | null;
  service_max_price: number | null;
}

export interface NearbyAgentsResponse {
  agents: Agent[];
  count: number;
  radius_km: number;
  user_lat: number;
  user_lon: number;
}

export const servicesApi = {
  getCategories: async (): Promise<Category[]> => {
    const res = await client.get('/services/categories/');
    return res.data;
  },

  createRequest: async (data: CreateRequestData): Promise<ServiceRequest> => {
    const res = await client.post('/services/requests/', data);
    return res.data;
  },

  getMyRequests: async (): Promise<ServiceRequest[]> => {
    const res = await client.get('/services/requests/my/');
    return res.data;
  },

  getRequestDetail: async (id: number): Promise<ServiceRequest> => {
    const res = await client.get(`/services/requests/${id}/`);
    return res.data;
  },

  cancelRequest: async (id: number): Promise<void> => {
    await client.post(`/services/requests/${id}/cancel/`);
  },

  submitReview: async (id: number, rating: number, comment: string): Promise<void> => {
    await client.post(`/services/requests/${id}/review/`, { rating, comment });
  },

  // Agent endpoints
  getAvailableRequests: async (): Promise<ServiceRequest[]> => {
    const res = await client.get('/services/agent/available/');
    return res.data;
  },

  acceptRequest: async (id: number): Promise<void> => {
    await client.post(`/services/agent/accept/${id}/`);
  },

  updateRequestStatus: async (id: number, status: string): Promise<void> => {
    await client.post(`/services/agent/update/${id}/`, { status });
  },

  // Nearby agents endpoint
  getNearbyAgents: async (
    lat: number,
    lon: number,
    radius?: number,
    profession?: string
  ): Promise<NearbyAgentsResponse> => {
    const params = new URLSearchParams();
    params.append('lat', lat.toString());
    params.append('lon', lon.toString());
    if (radius) params.append('radius', radius.toString());
    if (profession) params.append('profession', profession);

    const res = await client.get(`/services/agents/nearby/?${params}`);
    return res.data;
  },
};