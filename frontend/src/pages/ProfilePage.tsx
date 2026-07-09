import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const ProfilePage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!user) return null;

  return (
    <div style={styles.container}>
      {/* Profile Card */}
      <div style={styles.profileCard}>
        <div style={styles.avatarLarge}>
          {user.full_name?.charAt(0) || 'U'}
        </div>
        <h2 style={styles.fullName}>{user.full_name}</h2>
        <p style={styles.email}>{user.email}</p>
        <div style={styles.roleBadge}>
          {user.role === 'admin' ? 'مشرف' : user.role === 'agent' ? 'مهني' : 'عميل'}
        </div>
      </div>

      {/* Stats */}
      <div style={styles.statsContainer}>
        <div style={styles.statCard}>
          <span style={styles.statNumber}>{user.completed_orders}</span>
          <span style={styles.statLabel}>طلبات مكتملة</span>
        </div>
        <div style={styles.statCard}>
          <span style={styles.statNumber}>{user.rating || '-'}</span>
          <span style={styles.statLabel}>التقييم</span>
        </div>
        <div style={styles.statCard}>
          <span style={styles.statNumber}>{user.is_verified ? 'نعم' : 'لا'}</span>
          <span style={styles.statLabel}>موثق</span>
        </div>
      </div>

      {/* Menu Items */}
      <div style={styles.menuSection}>
        <button style={styles.menuItem} onClick={() => navigate('/settings')}>
          <span style={styles.menuIcon}>⚙️</span>
          <span>الإعدادات</span>
          <span style={styles.arrow}>←</span>
        </button>

        <button style={styles.menuItem} onClick={() => navigate('/notifications')}>
          <span style={styles.menuIcon}>🔔</span>
          <span>الإشعارات</span>
          <span style={styles.arrow}>←</span>
        </button>

        <button style={styles.menuItem} onClick={() => navigate('/transactions')}>
          <span style={styles.menuIcon}>💰</span>
          <span>المحفظة</span>
          <span style={styles.arrow}>←</span>
        </button>

        <button style={styles.menuItem} onClick={() => navigate('/faq')}>
          <span style={styles.menuIcon}>❓</span>
          <span>المساعدة</span>
          <span style={styles.arrow}>←</span>
        </button>
      </div>

      {/* Logout */}
      <button style={styles.logoutButton} onClick={handleLogout}>
        تسجيل الخروج
      </button>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: '500px',
    margin: '0 auto',
    padding: '20px 16px',
  },
  profileCard: {
    background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
    borderRadius: '16px',
    padding: '32px 24px',
    textAlign: 'center',
    color: '#fff',
    marginBottom: '20px',
  },
  avatarLarge: {
    width: '80px',
    height: '80px',
    borderRadius: '50%',
    background: 'rgba(255,255,255,0.2)',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '36px',
    fontWeight: 'bold',
    margin: '0 auto 16px',
    border: '3px solid rgba(255,255,255,0.3)',
  },
  fullName: {
    fontSize: '22px',
    fontWeight: 'bold',
    margin: '0 0 4px 0',
  },
  email: {
    fontSize: '14px',
    opacity: 0.9,
    margin: '0 0 12px 0',
  },
  roleBadge: {
    display: 'inline-block',
    padding: '4px 16px',
    borderRadius: '20px',
    background: 'rgba(255,255,255,0.2)',
    fontSize: '13px',
    fontWeight: '500',
  },
  statsContainer: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '12px',
    marginBottom: '20px',
  },
  statCard: {
    background: '#fff',
    borderRadius: '12px',
    padding: '16px',
    textAlign: 'center',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  statNumber: {
    display: 'block',
    fontSize: '20px',
    fontWeight: 'bold',
    color: '#1f2937',
  },
  statLabel: {
    display: 'block',
    fontSize: '12px',
    color: '#6b7280',
    marginTop: '4px',
  },
  menuSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    marginBottom: '20px',
  },
  menuItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '16px',
    background: '#fff',
    border: 'none',
    borderRadius: '12px',
    cursor: 'pointer',
    fontSize: '15px',
    color: '#374151',
    textAlign: 'right',
    fontWeight: '500',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    width: '100%',
  },
  menuIcon: {
    fontSize: '20px',
  },
  arrow: {
    marginLeft: 'auto',
    color: '#9ca3af',
  },
  logoutButton: {
    width: '100%',
    padding: '14px',
    background: '#fff',
    border: '2px solid #fee2e2',
    borderRadius: '12px',
    color: '#dc2626',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer',
  },
};

export default ProfilePage;