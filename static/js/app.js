const app = document.getElementById('app');
const toast = document.getElementById('toast');
const tokenKey = 'enjaz_pwa_token';
const userKey = 'enjaz_pwa_user';
const apiBase = window.location.origin + '/api';
let deferredPrompt = null;

const state = {
  token: localStorage.getItem(tokenKey),
  user: JSON.parse(localStorage.getItem(userKey) || 'null'),
};

const showToast = (message) => {
  const text = typeof message === 'string' ? message : JSON.stringify(message);
  toast.textContent = text;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3200);
};

const updateAuthUI = () => {
  document.body.classList.toggle('authenticated', !!state.token);
  updateSidebarActive();
};

const fetchJson = async (url, options = {}) => {
  const headers = options.headers || {};
  if (state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }
  options.headers = { 'Accept': 'application/json', ...headers };
  options.cache = options.cache || 'no-store';
  const response = await fetch(url, options);
  const contentType = response.headers.get('content-type') || '';
  const body = contentType.includes('application/json') ? await response.json() : null;
  if (!response.ok) {
    let errorMessage = `خطأ ${response.status}`;
    if (body) {
      if (body.detail) errorMessage = body.detail;
      else if (body.error) errorMessage = body.error;
      else if (body.non_field_errors) errorMessage = body.non_field_errors[0];
      else if (typeof body === 'string') errorMessage = body;
      else if (typeof body === 'object') {
        const firstValue = Object.values(body)[0];
        if (Array.isArray(firstValue)) errorMessage = firstValue[0];
        else if (typeof firstValue === 'string') errorMessage = firstValue;
      }
    } else if (response.statusText) {
      errorMessage = `خطأ ${response.status}: ${response.statusText}`;
    }
    throw new Error(errorMessage);
  }
  return body;
};

const saveSession = ({ access, user }) => {
  state.token = access;
  state.user = user;
  localStorage.setItem(tokenKey, access);
  localStorage.setItem(userKey, JSON.stringify(user));
  updateAuthUI();
};

const clearSession = () => {
  state.token = null;
  state.user = null;
  localStorage.removeItem(tokenKey);
  localStorage.removeItem(userKey);
  renderApp();
  updateAuthUI();
};

const renderLogin = (initialForm = 'login') => {
  app.innerHTML = `
    <section id="login-section" class="section">
      <div id="register-section" style="position:absolute;top:0;left:0;width:1px;height:1px;visibility:hidden;"></div>
      <div class="login-header">
        <div class="brand centered">إنجاز</div>
      </div>
      <div class="card">
        <div style="display:flex;align-items:center;justify-content:center;gap:16px;flex-wrap:wrap;text-align:center;">
          <div>
            <div class="hero-badge">🔐 تسجيل الدخول</div>
            <h2 style="margin:12px 0 8px;">تسجيل الدخول</h2>
            <p class="small-text">استخدم هاتفك وكلمة المرور للدخول إلى لوحة إنجاز.</p>
          </div>
        </div>
        <div class="nav-buttons" style="margin-top:26px;justify-content:center;display:flex;">
          <button id="show-login" class="active-tab">تسجيل دخول</button>
          <button id="show-register" class="secondary">إنشاء حساب</button>
        </div>
        <div id="auth-form"></div>
      </div>
    </section>
    <section class="hero" id="overview">
      <h1>سجل دخولك الآن لتحصل على الخدمات السريعة</h1>
      <p>واجهة إنجاز الذكية
        تطبيق الويب التقدمي للعميل والمندوب. سجّل دخولك الآن للوصول إلى لوحة التحكم وإدارة الطلبات بسهولة.
      </p>
    </section>
  `;
  const authForm = document.getElementById('auth-form');
  const loginTab = document.getElementById('show-login');
  const registerTab = document.getElementById('show-register');

  const updateActiveTab = (type) => {
    if (type === 'login') {
      loginTab.classList.add('active-tab');
      registerTab.classList.remove('active-tab');
    } else {
      registerTab.classList.add('active-tab');
      loginTab.classList.remove('active-tab');
    }
  };

  const renderForm = (type) => {
    updateActiveTab(type);
    authForm.innerHTML = type === 'login' ? 
      `
        <div class="form-grid">
          <input id="phone" placeholder="رقم الهاتف" type="text" autocomplete="tel" autocorrect="off" autocapitalize="none" />
          <input id="password" placeholder="كلمة المرور" type="password" autocomplete="current-password" />
          <button id="login-button" type="button">دخول الآن</button>
          <button id="forgot-password" class="secondary" type="button">نسيت كلمة المرور؟</button>
          <div style="text-align:center;margin:16px 0;position:relative;">
            <span style="background:white;padding:0 8px;position:relative;z-index:1;">أو</span>
            <div style="position:absolute;top:50%;left:0;right:0;height:1px;background:#E2E8EE;z-index:0;"></div>
          </div>
          <div id="google-login-button"></div>
        </div>
      ` :
      `
        <div class="form-grid">
          <input id="first_name" placeholder="الاسم الأول" type="text" />
          <input id="last_name" placeholder="اسم العائلة" type="text" />
          <input id="phone" placeholder="رقم الهاتف" type="text" />
          <input id="password" placeholder="كلمة المرور" type="password" />
          <input id="password_confirm" placeholder="تأكيد كلمة المرور" type="password" />
          <select id="role">
            <option value="customer">عميل</option>
            <option value="agent">مندوب</option>
          </select>
          <button id="register-button">إنشاء حساب</button>
          <div style="text-align:center;margin:16px 0;position:relative;">
            <span style="background:white;padding:0 8px;position:relative;z-index:1;">أو</span>
            <div style="position:absolute;top:50%;left:0;right:0;height:1px;background:#E2E8EE;z-index:0;"></div>
          </div>
          <div id="google-register-button"></div>
        </div>
      `;

    const handleGoogleSignIn = async (response) => {
      try {
        const data = await fetchJson(`${apiBase}/auth/google/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token: response.credential }),
        });
        saveSession(data);
        renderApp();
        showToast('تم تسجيل الدخول بنجاح');
      } catch (err) {
        showToast(err.message);
      }
    };

    if (type === 'login') {
      document.getElementById('login-button').addEventListener('click', async () => {
        try {
          const payload = {
            phone_number: document.getElementById('phone').value.trim(),
            password: document.getElementById('password').value.trim(),
          };
          const data = await fetchJson(`${apiBase}/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          });
          saveSession(data);
          renderApp();
          showToast('تم تسجيل الدخول بنجاح');
        } catch (err) {
          showToast(err.message);
        }
      });
      document.getElementById('forgot-password').addEventListener('click', () => {
        showToast('يرجى التواصل مع الدعم لإعادة تعيين كلمة المرور');
      });
      
      if (window.google && window.GOOGLE_CLIENT_ID) {
        google.accounts.id.initialize({ client_id: window.GOOGLE_CLIENT_ID });
        google.accounts.id.renderButton(
          document.getElementById('google-login-button'),
          { theme: 'outline', size: 'large', text: 'signin_with', width: '300' }
        );
        google.accounts.id.setup({ callback: handleGoogleSignIn });
      }
    } else {
      document.getElementById('register-button').addEventListener('click', async () => {
        try {
          const payload = {
            first_name: document.getElementById('first_name').value.trim(),
            last_name: document.getElementById('last_name').value.trim(),
            phone_number: document.getElementById('phone').value.trim(),
            password: document.getElementById('password').value,
            password_confirm: document.getElementById('password_confirm').value,
            role: document.getElementById('role').value,
          };
          const data = await fetchJson(`${apiBase}/auth/register/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          });
          saveSession(data);
          renderApp();
          showToast('تم إنشاء الحساب بنجاح');
        } catch (err) {
          showToast(err.message);
        }
      });
      
      if (window.google && window.GOOGLE_CLIENT_ID) {
        google.accounts.id.initialize({ client_id: window.GOOGLE_CLIENT_ID });
        google.accounts.id.renderButton(
          document.getElementById('google-register-button'),
          { theme: 'outline', size: 'large', text: 'signup_with', width: '300' }
        );
        google.accounts.id.setup({ callback: handleGoogleSignIn });
      }
    }
  };

  loginTab.addEventListener('click', () => renderForm('login'));
  registerTab.addEventListener('click', () => renderForm('register'));
  renderForm(initialForm);
  updateSidebarActive();
};

const renderDashboard = async () => {
  app.innerHTML = `
    <section id="dashboard" class="section">
      <div class="brand-bar">
        <div class="brand"><span>إن</span> إنجاز</div>
        <button class="secondary" id="logout">خروج</button>
      </div>
      <div class="dashboard-actions">
        <button class="nav-link action-button" type="button" onclick="document.getElementById('dashboard-section').scrollIntoView({ behavior: 'smooth' })">📊 لوحة البيانات</button>
        <button class="nav-link action-button" type="button" onclick="document.getElementById('requests').scrollIntoView({ behavior: 'smooth' })">🗂️ طلباتي</button>
      </div>
      <div class="install-banner" id="install-banner" style="display:none;">
        <div>يمكنك تثبيت التطبيق على الشاشة الرئيسية للحصول على تجربة أسرع وبدون متصفح.</div>
        <button id="install-button">تثبيت التطبيق</button>
      </div>
      <div id="main-area"></div>
      <div id="dashboard-section" class="card">
        <h2>مرحباً، ${state.user?.full_name || 'المستخدم'}</h2>
        <p class="small-text">${state.user?.role === 'agent' ? 'لوحة المندوب' : 'لوحة العميل'}</p>
      </div>
    </section>
  `;

  document.getElementById('logout').addEventListener('click', clearSession);
  updateSidebarActive();

  if (deferredPrompt) {
    const banner = document.getElementById('install-banner');
    banner.style.display = 'grid';
    document.getElementById('install-button').addEventListener('click', async () => {
      deferredPrompt.prompt();
      const choice = await deferredPrompt.userChoice;
      if (choice.outcome === 'accepted') {
        showToast('تم تثبيت التطبيق');
      }
      deferredPrompt = null;
      banner.style.display = 'none';
    });
  }

  const mainArea = document.getElementById('main-area');
  mainArea.innerHTML = `<div class="card"><h2>تحميل البيانات...</h2></div>`;

  try {
    const [notifications, categories, requests] = await Promise.all([
      fetchJson(`${apiBase}/notifications/`),
      fetchJson(`${apiBase}/services/categories/`),
      fetchJson(`${apiBase}/services/requests/my/`),
    ]);

    const unreadCount = notifications.filter(item => !item.is_read).length;
    mainArea.innerHTML = `
      <div class="card">
        <div class="form-grid">
          <div><strong>الإشعارات غير المقروءة</strong> (${unreadCount})</div>
          <button class="secondary" id="mark-read">وضع الكل كمقروء</button>
        </div>
      </div>
        <div class="card">
        <h2>أحدث الطلبات</h2>
        ${requests.length ? requests.map(renderRequestItem).join('') : '<p class="small-text">لا توجد طلبات حتى الآن.</p>'}
      </div>
      <div id="requests" class="card">
        <h2>إنشاء طلب جديد</h2>
        <div class="form-grid">
          <input id="title" placeholder="عنوان الطلب" />
          <select id="category_id">${categories.map(cat => `<option value="${cat.id}">${cat.name}</option>`).join('')}</select>
          <textarea id="details" placeholder="وصف الطلب"></textarea>
          <input id="location" placeholder="موقع التنفيذ" />
          <input id="attachments" type="file" multiple />
          <button id="create-request">إرسال الطلب</button>
        </div>
      </div>
    `;

    document.getElementById('mark-read').addEventListener('click', async () => {
      await fetchJson(`${apiBase}/notifications/read-all/`, { method: 'POST' });
      showToast('تم وضع الإشعارات كمقروءة');
      renderDashboard();
    });

    document.getElementById('create-request').addEventListener('click', async () => {
      try {
        const form = new FormData();
        form.append('title', document.getElementById('title').value);
        form.append('details', document.getElementById('details').value);
        form.append('location', document.getElementById('location').value);
        form.append('category_id', document.getElementById('category_id').value);
        const files = document.getElementById('attachments').files;
        for (const file of files) {
          form.append('attachments', file);
        }
        await fetchJson(`${apiBase}/services/requests/`, {
          method: 'POST',
          body: form,
        });
        showToast('تم إرسال الطلب بنجاح');
        renderDashboard();
      } catch (err) {
        showToast(err.message);
      }
    });
  } catch (err) {
    mainArea.innerHTML = `<div class="card"><p class="small-text">${err.message}</p></div>`;
  }
};

const updateSidebarActive = () => {
  const hash = window.location.hash || '#overview';
  const links = document.querySelectorAll('.sidebar .nav-link');
  links.forEach((link) => {
    const href = link.getAttribute('href');
    if (href === hash) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });
};

const renderRequestItem = (request) => `
  <div class="request-item">
    <div class="request-meta">
      <span><strong>العنوان:</strong> ${request.title}</span>
      <span class="status-badge status-${request.status}">${request.status_display}</span>
    </div>
    <div class="small-text">${request.category_name} • ${request.customer_name || ''}</div>
    <p class="small-text">${request.estimated_price ? 'السعر المتوقع: ' + request.estimated_price + ' د.ع' : ''}</p>
  </div>
`;

const renderApp = () => {
  if (!state.token) {
    renderLogin();
    updateAuthUI();
    return;
  }
  renderDashboard();
  updateAuthUI();
};

window.addEventListener('beforeinstallprompt', (event) => {
  event.preventDefault();
  deferredPrompt = event;
});

window.addEventListener('hashchange', () => {
  updateSidebarActive();
  if (!state.token) {
    const hash = window.location.hash;
    if (hash === '#register-section') {
      renderLogin('register');
    } else {
      renderLogin('login');
    }
  }
});

window.addEventListener('load', () => {
  renderApp();
  updateSidebarActive();
});
