import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { servicesApi } from '../api';
import type { Category } from '../types';
import MapPicker from '../components/MapPicker';

const CreateRequestPage: React.FC = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [formData, setFormData] = useState({
    category: 0,
    title: '',
    description: '',
    location: '',
  });
  const [mapLocation, setMapLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [catsLoading, setCatsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    servicesApi.getCategories()
      .then((data) => {
        setCategories(data);
        setCatsLoading(false);
      })
      .catch((err) => {
        console.error('خطأ في تحميل التصنيفات:', err);
        setError('فشل تحميل التصنيفات. تأكد من اتصال الخادم.');
        setCatsLoading(false);
      });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const requestData: any = {
        category: formData.category,
        title: formData.title,
        description: formData.description,
        location: formData.location,
      };

      // إضافة إحداثيات الخريطة إذا تم اختيار موقع
      if (mapLocation) {
        requestData.lat = mapLocation.lat;
        requestData.lng = mapLocation.lng;
      }

      await servicesApi.createRequest(requestData);
      navigate('/requests');
    } catch (err: any) {
      const detail = err.response?.data?.detail ||
        err.response?.data?.message ||
        'حدث خطأ أثناء إنشاء الطلب';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>إنشاء طلب جديد</h2>

        {error && <div style={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.inputGroup}>
            <label style={styles.label}>التصنيف</label>
            {catsLoading ? (
              <div style={styles.loadingSelect}>جاري تحميل التصنيفات...</div>
            ) : categories.length === 0 ? (
              <div style={styles.noData}>لا توجد تصنيفات متاحة</div>
            ) : (
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: Number(e.target.value) })}
                style={styles.select}
                required
              >
                <option value={0}>اختر تصنيف</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            )}
          </div>

          <div style={styles.inputGroup}>
            <label style={styles.label}>عنوان الطلب</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              style={styles.input}
              placeholder="مثال: تصليح مكيف سبليت"
              required
            />
          </div>

          <div style={styles.inputGroup}>
            <label style={styles.label}>وصف الطلب</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              style={styles.textarea}
              placeholder="اشرح تفاصيل الخدمة التي تطلبها..."
              rows={5}
              required
            />
          </div>

          <div style={styles.inputGroup}>
            <label style={styles.label}>الموقع (نص)</label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              style={styles.input}
              placeholder="بغداد - الكرخ"
              required
            />
          </div>

          <div style={styles.inputGroup}>
            <label style={styles.label}>اختر الموقع على الخريطة</label>
            <p style={styles.hint}>انقر على الخريطة لتحديد موقع الطلب بدقة</p>
            <MapPicker
              value={mapLocation}
              onChange={setMapLocation}
              height="350px"
            />
          </div>

          <button type="submit" style={styles.button} disabled={loading}>
            {loading ? 'جاري الإنشاء...' : 'إنشاء الطلب'}
          </button>
        </form>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: '600px',
    margin: '0 auto',
    padding: '20px 16px',
  },
  card: {
    background: '#fff',
    borderRadius: '16px',
    padding: '24px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  title: {
    fontSize: '22px',
    fontWeight: 'bold',
    color: '#1f2937',
    margin: '0 0 24px 0',
    textAlign: 'center',
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
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  label: {
    color: '#374151',
    fontSize: '14px',
    fontWeight: '500',
  },
  hint: {
    color: '#9ca3af',
    fontSize: '12px',
    margin: 0,
  },
  input: {
    padding: '12px 16px',
    border: '2px solid #e5e7eb',
    borderRadius: '8px',
    fontSize: '16px',
    outline: 'none',
    width: '100%',
    boxSizing: 'border-box',
  },
  select: {
    padding: '12px 16px',
    border: '2px solid #e5e7eb',
    borderRadius: '8px',
    fontSize: '16px',
    outline: 'none',
    width: '100%',
    boxSizing: 'border-box',
    background: '#fff',
  },
  loadingSelect: {
    padding: '12px 16px',
    border: '2px solid #e5e7eb',
    borderRadius: '8px',
    color: '#9ca3af',
    fontSize: '14px',
  },
  noData: {
    padding: '12px 16px',
    border: '2px solid #fee2e2',
    borderRadius: '8px',
    color: '#dc2626',
    fontSize: '14px',
    background: '#fef2f2',
  },
  textarea: {
    padding: '12px 16px',
    border: '2px solid #e5e7eb',
    borderRadius: '8px',
    fontSize: '16px',
    outline: 'none',
    width: '100%',
    boxSizing: 'border-box',
    resize: 'vertical',
    fontFamily: 'inherit',
  },
  button: {
    padding: '14px',
    background: '#2563eb',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer',
    marginTop: '8px',
  },
};

export default CreateRequestPage;