import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { servicesApi } from '../api';
import type { ServiceRequest } from '../types';

const RequestsPage: React.FC = () => {
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const load = async () => {
      try {
        const data = await servicesApi.getMyRequests();
        setRequests(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
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
      <div style={styles.header}>
        <h2 style={styles.title}>طلباتي</h2>
        <button style={styles.addButton} onClick={() => navigate('/create-request')}>
          + طلب جديد
        </button>
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
          <div
            key={req.id}
            style={styles.requestCard}
            onClick={() => navigate(`/requests/${req.id}`)}
          >
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
              <span style={styles.price}>{req.price} د.ع</span>
            </div>
            <div style={styles.date}>
              {new Date(req.created_at).toLocaleDateString('ar-IQ')}
            </div>
          </div>
        ))
      )}
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
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
  },
  title: {
    fontSize: '22px',
    fontWeight: 'bold',
    color: '#1f2937',
    margin: 0,
  },
  addButton: {
    padding: '10px 20px',
    background: '#2563eb',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    fontWeight: 'bold',
    cursor: 'pointer',
    fontSize: '14px',
  },
  emptyState: {
    background: '#fff',
    borderRadius: '12px',
    padding: '40px',
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
    cursor: 'pointer',
    transition: 'transform 0.1s',
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
  price: {
    color: '#059669',
    fontWeight: 'bold',
  },
  date: {
    color: '#9ca3af',
    fontSize: '12px',
    marginTop: '8px',
  },
};

export default RequestsPage;