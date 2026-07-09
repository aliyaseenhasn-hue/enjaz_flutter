import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { servicesApi } from '../api';
import type { Category, ServiceRequest } from '../types';
import NearbyAgents from '../components/NearbyAgents';
import { useAuth } from '../contexts/AuthContext';

const HomePage: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [categories, setCategories] = useState<Category[]>([]);
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNearbyAgents, setShowNearbyAgents] = useState(false);
  const [professionFilter, setProfessionFilter] = useState('');
  const [radius, setRadius] = useState(10);
  const navigate = useNavigate();

  useEffect(() => {
    const loadData = async () => {
      try {
        const [cats, reqs] = await Promise.all([
          servicesApi.getCategories(),
          servicesApi.getMyRequests(),
        ]);
        setCategories(cats.slice(0, 6));
        setRequests(reqs.slice(0, 3));
      } catch (err) {
        console.error('Error loading data:', err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  if (loading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.loader}></div>
        <p>جاري التحميل...</p>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerContent}>
          <h1 style={styles.headerTitle}>منصة إنجاز</h1>
          <nav style={styles.nav}>
            {isAuthenticated ? (
              <div style={styles.authNav}>
                <Link 
                  to="/profile" 
                  style={styles.navLink}
                >
                  {user?.full_name || 'الملف الشخصي'}
                </Link>
                <Link 
                  to="/requests" 
                  style={styles.navLink}
                >
                  طلباتي
                </Link>
                <Link 
                  to="/create-request" 
                  style={styles.createRequestLink}
                >
                  إنشاء طلب
                </Link>
              </div>
            ) : (
              <div style={styles.authNav}>
                <Link 
                  to="/login" 
                  style={styles.navLink}
                >
                  تسجيل الدخول
                </Link>
                <Link 
                  to="/register" 
                  style={styles.createRequestLink}
                >
                  اشتراك
                </Link>
              </div>
            )}
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section style={styles.hero}>
        <h2 style={styles.heroTitle}>وصل إلى المهنيين الأقرب إليك</h2>
        <p style={styles.heroSubtitle}>
          منصة إنجاز تربطك بأفضل المهنيين في منطقتك. ابحث عن الخدمات التي تحتاجها، واحصل على أفضل الأسعار وجودة العمل.
        </p>
      </section>
      
      {/* Find Nearby Agents Section */}
      <section style={styles.nearbyAgentsSection}>
        <div style={styles.sectionHeaderRow}>
          <h2 style={styles.nearbyAgentsTitle}>
            ابحث عن المهنيين القريبين
          </h2>
        </div>
        
        <div style={styles.filtersRow}>
          <div style={styles.filterGroup}>
            <label style={styles.filterLabel}>
              نوع المهنة
            </label>
            <select
              value={professionFilter}
              onChange={(e) => setProfessionFilter(e.target.value)}
              style={styles.filterSelect}
            >
              <option value="">جميع المهن</option>
              <option value="lawyer">محامٍ</option>
              <option value="electrician">كهربائي</option>
              <option value="plumber">سباك</option>
              <option value="mason">بناء</option>
              <option value="painter">دهان</option>
              <option value="carpenter">نجار</option>
              <option value="hvac">فني تبريد وتكييف</option>
              <option value="tile_mason">سيراميك</option>
              <option value="developer">مبرمج</option>
              <option value="engineer">مهندس</option>
              <option value="security_tech">فني أنظمة أمنية</option>
              <option value="clearance_agent">معقب معاملات</option>
              <option value="accountant">محاسب</option>
              <option value="other">خدمات أخرى</option>
            </select>
          </div>
          
          <div style={styles.filterGroup}>
            <label style={styles.filterLabel}>
              نصف القطر (كم)
            </label>
            <input
              type="number"
              min="1"
              max="50"
              value={radius}
              onChange={(e) => setRadius(parseInt(e.target.value) || 10)}
              style={styles.filterInput}
            />
          </div>
        </div>
        
        <div style={styles.searchButtonContainer}>
          <button
            onClick={() => setShowNearbyAgents(!showNearbyAgents)}
            style={styles.searchButton}
          >
            {showNearbyAgents ? 'إخفاء النتائج' : 'ابحث عن المهنيين القريبين'}
          </button>
        </div>
        
        {showNearbyAgents && (
          <div style={styles.nearbyAgentsResults}>
            <NearbyAgents 
              professionFilter={professionFilter} 
              radius={radius} 
            />
          </div>
        )}
      </section>
      
      {/* Features Section */}
      <section style={styles.featuresSection}>
        <div style={styles.featureCard}>
          <div style={styles.featureIcon}>🔧</div>
          <h3 style={styles.featureTitle}>خدمات متنوعة</h3>
          <p style={styles.featureDescription}>
            ابحث عن مختلف الخدمات من كهرباء، نجارة، سباكة، تكييف، وخدمات أخرى في مكان واحد.
          </p>
        </div>
        
        <div style={styles.featureCard}>
          <div style={styles.featureIcon}>📍</div>
          <h3 style={styles.featureTitle}>قريب منك</h3>
          <p style={styles.featureDescription}>
            اكتشف المهنيين الأقرب إليك بناءً على موقعك الجغرافي.
          </p>
        </div>
        
        <div style={styles.featureCard}>
          <div style={styles.featureIcon}>⭐</div>
          <h3 style={styles.featureTitle}>جودة مضمونة</h3>
          <p style={styles.featureDescription}>
            تقييمات من العملاء السابقين تساعدك في اختيار أفضل المهنيين.
          </p>
        </div>
      </section>

      {/* Categories */}
      <section style={styles.section}>
        <div style={styles.sectionHeader}>
          <h3 style={styles.sectionTitle}>التصنيفات</h3>
          <button style={styles.seeAll} onClick={() => navigate('/categories')}>عرض الكل</button>
        </div>
        <div style={styles.categoriesGrid}>
          {categories.map((cat) => (
            <div key={cat.id} style={styles.categoryCard}>
              <div style={styles.categoryIcon}>{cat.icon || '📋'}</div>
              <span style={styles.categoryName}>{cat.name}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Recent Requests */}
      <section style={styles.section}>
        <div style={styles.sectionHeader}>
          <h3 style={styles.sectionTitle}>طلباتك الأخيرة</h3>
          <button style={styles.seeAll} onClick={() => navigate('/requests')}>عرض الكل</button>
        </div>
        {requests.length === 0 ? (
          <div style={styles.emptyState}>
            <p>لا توجد طلبات بعد</p>
            <button style={styles.createBtn} onClick={() => navigate('/create-request')}>
              إنشاء طلب جديد
            </button>
          </div>
        ) : (
          requests.map((req) => (
            <div key={req.id} style={styles.requestCard}>
              <div style={styles.requestHeader}>
                <h4 style={styles.requestTitle}>{req.title}</h4>
                <span style={{
                  ...styles.statusBadge,
                  background: req.status === 'completed' ? '#d1fae5' :
                              req.status === 'in_progress' ? '#dbeafe' :
                              req.status === 'pending' ? '#fef3c7' : '#fee2e2',
                  color: req.status === 'completed' ? '#065f46' :
                         req.status === 'in_progress' ? '#1e40af' :
                         req.status === 'pending' ? '#92400e' : '#991b1b',
                }}>
                  {req.status === 'pending' ? 'قيد الانتظار' :
                   req.status === 'accepted' ? 'مقبول' :
                   req.status === 'in_progress' ? 'قيد التنفيذ' :
                   req.status === 'completed' ? 'مكتمل' : 'ملغي'}
                </span>
              </div>
              <p style={styles.requestDesc}>{req.description}</p>
              <div style={styles.requestMeta}>
                <span>{req.category_name}</span>
                <span>{req.price} د.ع</span>
              </div>
            </div>
          ))
        )}
      </section>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '16px',
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
  hero: {
    background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
    borderRadius: '16px',
    padding: '32px',
    textAlign: 'center',
    color: '#fff',
    marginBottom: '24px',
  },
  heroTitle: {
    fontSize: '24px',
    fontWeight: 'bold',
    margin: '0 0 8px 0',
  },
  heroSubtitle: {
    fontSize: '14px',
    opacity: 0.9,
    margin: '0 0 20px 0',
  },
  heroButton: {
    padding: '12px 32px',
    background: '#fff',
    color: '#2563eb',
    border: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer',
  },
  section: {
    marginBottom: '24px',
  },
  sectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
  },
  sectionTitle: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#1f2937',
    margin: 0,
  },
  seeAll: {
    background: 'none',
    border: 'none',
    color: '#2563eb',
    fontWeight: '500',
    cursor: 'pointer',
    fontSize: '14px',
  },
  categoriesGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '12px',
  },
  categoryCard: {
    background: '#fff',
    borderRadius: '12px',
    padding: '16px',
    textAlign: 'center',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    cursor: 'pointer',
  },
  categoryIcon: {
    fontSize: '28px',
    marginBottom: '8px',
  },
  categoryName: {
    fontSize: '13px',
    color: '#374151',
    fontWeight: '500',
  },
  emptyState: {
    background: '#fff',
    borderRadius: '12px',
    padding: '32px',
    textAlign: 'center',
    color: '#6b7280',
  },
  createBtn: {
    padding: '10px 24px',
    background: '#2563eb',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    fontWeight: 'bold',
    cursor: 'pointer',
    marginTop: '12px',
  },
  requestCard: {
    background: '#fff',
    borderRadius: '12px',
    padding: '16px',
    marginBottom: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  requestHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  requestTitle: {
    fontSize: '16px',
    fontWeight: 'bold',
    color: '#1f2937',
    margin: 0,
  },
  statusBadge: {
    padding: '4px 10px',
    borderRadius: '20px',
    fontSize: '12px',
    fontWeight: '500',
  },
  requestDesc: {
    color: '#6b7280',
    fontSize: '14px',
    margin: '0 0 12px 0',
    lineHeight: 1.5,
  },
  requestMeta: {
    display: 'flex',
    justifyContent: 'space-between',
    color: '#9ca3af',
    fontSize: '13px',
  },
};

export default HomePage;