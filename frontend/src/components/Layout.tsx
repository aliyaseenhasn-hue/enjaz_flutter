import React from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Layout: React.FC = () => {
  const { user, isAuthenticated } = useAuth();

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerContent}>
          <NavLink to="/" style={styles.logo}>
            <h1 style={styles.logoText}>إنجاز</h1>
          </NavLink>

          {isAuthenticated && (
            <div style={styles.userSection}>
              <span style={styles.userName}>{user?.full_name}</span>
              <div style={styles.avatar}>
                {user?.full_name?.charAt(0) || 'U'}
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main style={styles.main}>
        <Outlet />
      </main>

      {/* Bottom Navigation */}
      {isAuthenticated && (
        <nav style={styles.bottomNav}>
          <NavLink to="/" style={({ isActive }) => ({
            ...styles.navItem,
            color: isActive ? '#2563eb' : '#6b7280',
          })}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
            <span style={styles.navLabel}>الرئيسية</span>
          </NavLink>

          <NavLink to="/requests" style={({ isActive }) => ({
            ...styles.navItem,
            color: isActive ? '#2563eb' : '#6b7280',
          })}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
            <span style={styles.navLabel}>الطلبات</span>
          </NavLink>

          <NavLink to="/profile" style={({ isActive }) => ({
            ...styles.navItem,
            color: isActive ? '#2563eb' : '#6b7280',
          })}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
            <span style={styles.navLabel}>الملف الشخصي</span>
          </NavLink>
        </nav>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    background: '#f3f4f6',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    background: '#fff',
    borderBottom: '1px solid #e5e7eb',
    padding: '12px 20px',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  headerContent: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    maxWidth: '1200px',
    margin: '0 auto',
    width: '100%',
  },
  logo: {
    textDecoration: 'none',
  },
  logoText: {
    color: '#2563eb',
    fontSize: '24px',
    fontWeight: 'bold',
    margin: 0,
  },
  userSection: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  userName: {
    color: '#374151',
    fontSize: '14px',
    fontWeight: '500',
  },
  avatar: {
    width: '36px',
    height: '36px',
    borderRadius: '50%',
    background: '#2563eb',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold',
    fontSize: '16px',
  },
  main: {
    flex: 1,
    paddingBottom: '80px',
  },
  bottomNav: {
    position: 'fixed',
    bottom: 0,
    left: 0,
    right: 0,
    background: '#fff',
    borderTop: '1px solid #e5e7eb',
    display: 'flex',
    justifyContent: 'space-around',
    alignItems: 'center',
    padding: '8px 0',
    paddingBottom: '12px',
    zIndex: 100,
  },
  navItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '2px',
    textDecoration: 'none',
    fontSize: '12px',
  },
  navLabel: {
    fontSize: '11px',
  },
};

export default Layout;