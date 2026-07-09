import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminApi } from '../api';
import { useAuth } from '../contexts/AuthContext';
import type { AdminStats, AdminUser } from '../types';

const AdminDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // تحقق من أن المستخدم أدمن
  useEffect(() => {
    if (user && user.role !== 'admin' && !user.is_agent_approved) {
      navigate('/');
      return;
    }
  }, [user, navigate]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [statsData, usersData] = await Promise.all([
          adminApi.getStats(),
          adminApi.getUsers(),
        ]);
        setStats(statsData);
        setUsers(usersData);
      } catch (err: any) {
        setError('فشل تحميل بيانات لوحة التحكم');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const handleApprove = async (userId: number) => {
    try {
      await adminApi.approveAgent(userId);
      // تحديث حالة المستخدم
      setUsers(users.map(u => 
        u.id === userId ? { ...u, verification_status: 'approved', is_verified: true } : u
      ));
    } catch (err) {
      setError('فشل عملية التوثيق');
    }
  };

  const handleReject = async (userId: number) => {
    try {
      await adminApi.rejectAgent(userId);
      setUsers(users.map(u => 
        u.id === userId ? { ...u, verification_status: 'rejected', is_verified: false } : u
      ));
    } catch (err) {
      setError('فشل عملية الرفض');
    }
  };

  if (loading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.loader}></div>
        <p>جاري تحميل لوحة التحكم...</p>
      </div>
    );
  }

  // المستخدمين المهنيين المعلقين
  const pendingAgents = users.filter(u => 
    u.role === 'agent' && u.verification_status === 'pending'
  );

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>لوحة التحكم</h2>
        <span style={styles.badge}>مشرف</span>
      </div>

      {error && <div style={styles.error}>{error}</div>}

      {/* بطاقات الإحصائيات */}
      {stats && (
        <div style={styles.statsGrid}>
          <div style={styles.statCard}>
            <span style={{ ...styles.statIcon, background: '#dbeafe', color: '#1e40af' }}>👥</span>
            <span style={styles.statNumber}>{stats.total_users}</span>
            <span style={styles.statLabel}>إجمالي المستخدمين</span>
          </div>
          <div style={styles.statCard}>
            <span style={{ ...styles.statIcon, background: '#d1fae5', color: '#065f46' }}>✅</span>
            <span style={styles.statNumber}>{stats.completed_requests}</span>
            <span style={styles.statLabel}>طلبات مكتملة</span>
          </div>
          <div style={styles.statCard}>
            <span style={{ ...styles.statIcon, background: '#fef3c7', color: '#92400e' }}>⏳</span>
            <span style={styles.statNumber}>{stats.pending_requests}</span>
            <span style={styles.statLabel}>طلبات معلقة</span>
          </div>
          <div style={styles.statCard}>
            <span style={{ ...styles.statIcon, background: '#fce7f3', color: '#9d174d' }}>📊</span>
            <span style={styles.statNumber}>{stats.new_reports}</span>
            <span style={styles.statLabel}>تقارير جديدة</span>
          </div>
        </div>
      )}

      {/* طلبات توثيق المهنيين */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>
          طلبات توثيق المهنيين
          {pendingAgents.length > 0 && (
            <span style={styles.countBadge}>{pendingAgents.length}</span>
          )}
        </h3>

        {pendingAgents.length === 0 ? (
          <div style={styles.emptyState}>
            <p>لا توجد طلبات توثيق معلقة</p>
          </div>
        ) : (
          pendingAgents.map((agent) => (
            <div key={agent.id} style={styles.userCard}>
              <div style={styles.userInfo}>
                <div style={styles.userAvatar}>
                  {agent.name?.charAt(0) || 'U'}
                </div>
                <div>
                  <h4 style={styles.userName}>{agent.name}</h4>
                  <p style={styles.userPhone}>{agent.phone}</p>
                  <span style={styles.roleTag}>مهني</span>
                </div>
              </div>
              <div style={styles.actionButtons}>
                {agent.id_card_front && (
                  <a
                    href={agent.id_card_front}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={styles.viewBtn}
                  >
                    عرض البطاقة
                  </a>
                )}
                <button
                  style={styles.approveBtn}
                  onClick={() => handleApprove(agent.id)}
                >
                  ✅ توثيق
                </button>
                <button
                  style={styles.rejectBtn}
                  onClick={() => handleReject(agent.id)}
                >
                  ❌ رفض
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* جميع المستخدمين */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>المستخدمين</h3>
        {users.map((u) => (
          <div key={u.id} style={styles.userCard}>
            <div style={styles.userInfo}>
              <div style={styles.userAvatar}>
                {u.name?.charAt(0) || 'U'}
              </div>
              <div>
                <h4 style={styles.userName}>{u.name}</h4>
                <p style={styles.userPhone}>{u.phone}</p>
                <div style={styles.tags}>
                  <span style={{
                    ...styles.tag,
                    background: u.role === 'admin' ? '#fce7f3' :
                               u.role === 'agent' ? '#dbeafe' : '#d1fae5',
                    color: u.role === 'admin' ? '#9d174d' :
                           u.role === 'agent' ? '#1e40af' : '#065f46',
                  }}>
                    {u.role === 'admin' ? 'مشرف' : u.role === 'agent' ? 'مهني' : 'عميل'}
                  </span>
                  {u.verification_status === 'approved' && (
                    <span style={{ ...styles.tag, background: '#d1fae5', color: '#065f46' }}>
                      ✅ موثق
                    </span>
                  )}
                </div>
              </div>
            </div>
            <div style={styles.dateJoin}>
              {new Date(u.date_joined).toLocaleDateString('ar-IQ')}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '20px 16px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px',
  },
  title: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#1f2937',
    margin: 0,
  },
  badge: {
    padding: '4px 12px',
    background: '#fce7f3',
    color: '#9d174d',
    borderRadius: '20px',
    fontSize: '13px',
    fontWeight: '500',
  },
  error: {
    background: '#fee2e2',
    color: '#dc2626',
    padding: '12px',
    borderRadius: '8px',
    marginBottom: '16px',
    fontSize: '14px',
    textAlign: 'center',
  },
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '60vh',
    color: '#6b7280',
  },
  loader: {
    width: '40px',
    height: '40px',
    border: '4px solid #e5e7eb',
    borderTop: '4px solid #2563eb',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
    marginBottom: '16px',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '12px',
    marginBottom: '24px',
  },
  statCard: {
    background: '#fff',
    borderRadius: '12px',
    padding: '20px 16px',
    textAlign: 'center',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  statIcon: {
    display: 'inline-block',
    padding: '8px 12px',
    borderRadius: '8px',
    fontSize: '24px',
    marginBottom: '8px',
  },
  statNumber: {
    display: 'block',
    fontSize: '28px',
    fontWeight: 'bold',
    color: '#1f2937',
  },
  statLabel: {
    display: 'block',
    fontSize: '13px',
    color: '#6b7280',
    marginTop: '4px',
  },
  section: {
    marginBottom: '24px',
  },
  sectionTitle: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#1f2937',
    margin: '0 0 12px 0',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  countBadge: {
    background: '#dc2626',
    color: '#fff',
    padding: '2px 8px',
    borderRadius: '12px',
    fontSize: '12px',
  },
  emptyState: {
    background: '#fff',
    borderRadius: '12px',
    padding: '24px',
    textAlign: 'center',
    color: '#6b7280',
  },
  userCard: {
    background: '#fff',
    borderRadius: '12px',
    padding: '16px',
    marginBottom: '8px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '12px',
  },
  userInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    flex: 1,
  },
  userAvatar: {
    width: '44px',
    height: '44px',
    borderRadius: '50%',
    background: '#2563eb',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold',
    fontSize: '18px',
    flexShrink: 0,
  },
  userName: {
    fontSize: '15px',
    fontWeight: 'bold',
    color: '#1f2937',
    margin: '0 0 2px 0',
  },
  userPhone: {
    fontSize: '13px',
    color: '#6b7280',
    margin: '0 0 4px 0',
  },
  tags: {
    display: 'flex',
    gap: '6px',
    flexWrap: 'wrap',
  },
  tag: {
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '11px',
    fontWeight: '500',
  },
  roleTag: {
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '11px',
    fontWeight: '500',
    background: '#dbeafe',
    color: '#1e40af',
  },
  dateJoin: {
    color: '#9ca3af',
    fontSize: '12px',
    whiteSpace: 'nowrap',
  },
  actionButtons: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap',
  },
  viewBtn: {
    padding: '8px 12px',
    background: '#f3f4f6',
    color: '#374151',
    borderRadius: '8px',
    fontSize: '13px',
    fontWeight: '500',
    cursor: 'pointer',
    textDecoration: 'none',
    display: 'inline-block',
  },
  approveBtn: {
    padding: '8px 12px',
    background: '#d1fae5',
    color: '#065f46',
    border: 'none',
    borderRadius: '8px',
    fontSize: '13px',
    fontWeight: 'bold',
    cursor: 'pointer',
  },
  rejectBtn: {
    padding: '8px 12px',
    background: '#fee2e2',
    color: '#991b1b',
    border: 'none',
    borderRadius: '8px',
    fontSize: '13px',
    fontWeight: 'bold',
    cursor: 'pointer',
  },
};

export default AdminDashboardPage;