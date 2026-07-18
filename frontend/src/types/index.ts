// ===== أنواع المستخدم =====
export interface User {
  id: number;
  email: string;
  full_name: string;
  username: string;
  phone_number: string;
  first_name: string;
  last_name: string;
  role: 'client' | 'agent' | 'admin';
  avatar: string | null;
  avatar_url: string | null;
  is_verified: boolean;
  is_agent_approved: boolean;
  profession: string | null;
  bio: string | null;
  city: string | null;
  location: string | null;
  rating: number;
  completed_orders: number;
  needs_phone_completion: boolean;
  join_date: string;
  date_joined?: string;
}

// ===== أنواع المصادقة =====
export interface LoginData {
  phone_number: string;
  password: string;
}

export interface RegisterData {
  phone_number: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
  role: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user?: User;
  role?: string;
  detail?: string;
}

export interface VerifyPhoneData {
  code: string;
  new_password?: string;
  confirm_password?: string;
}

// ===== أنواع الخدمات =====
export interface Category {
  id: number;
  name: string;
  slug: string;
  icon: string | null;
  description: string;
}

export interface ServiceRequest {
  id: number;
  client: number;
  client_name: string;
  agent: number | null;
  agent_name: string | null;
  category: number;
  category_name: string;
  title: string;
  description: string;
  status: 'pending' | 'accepted' | 'in_progress' | 'completed' | 'cancelled';
  price: string;
  location: string;
  lat?: number;
  lng?: number;
  created_at: string;
  updated_at: string;
}

export interface CreateRequestData {
  category: number;
  title: string;
  description: string;
  location: string;
  lat?: number;
  lng?: number;
}

// ===== أنواع المحادثة =====
export interface Message {
  id: number;
  sender: number;
  sender_name: string;
  request: number;
  content: string;
  created_at: string;
}

export interface Conversation {
  id: number;
  request_id: number;
  title: string;
  other_user: string;
  last_message: string;
  last_message_time: string;
  unread_count: number;
}

// ===== أنواع المحفظة =====
export interface Wallet {
  balance: string;
  pending_balance: string;
}

export interface Transaction {
  id: number;
  type: 'deposit' | 'withdrawal' | 'payment' | 'refund';
  amount: string;
  description: string;
  created_at: string;
  status: 'completed' | 'pending' | 'failed';
}

// ===== أنواع الإشعارات =====
export interface Notification {
  id: number;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  notification_type: string;
}

// ===== أنواع المهنيين =====
export interface Professional {
  id: number;
  full_name: string;
  profession: string;
  city: string;
  rating: number;
  completed_orders: number;
  avatar: string | null;
  bio: string | null;
  is_featured: boolean;
}

// ===== أنواع لوحة التحكم (Admin) =====
export interface AdminStats {
  total_users: number;
  completed_requests: number;
  pending_requests: number;
  new_reports: number;
}

export interface AdminUser {
  id: number;
  name: string;
  phone: string;
  role: string;
  is_active: boolean;
  is_verified: boolean | null;
  verification_status: string | null;
  date_joined: string;
  avatar: string | null;
  id_card_front: string | null;
  id_card_back: string | null;
}