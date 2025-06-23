import React, { useState } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8082/api';

export default function ManualCleanup() {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const triggerCleanup = async () => {
    if (!window.confirm('Manuel temizlik başlatılsın mı?')) return;
    setLoading(true);
    setSuccess('');
    setError('');
    try {
      const res = await axios.post(`${API_URL.replace(/\/$/, '')}/v1/status/system/cleanup`);
      setSuccess(res.data.message || 'Temizlik başlatıldı!');
    } catch (err) {
      setError('Temizlik hatası');
    }
    setLoading(false);
  };

  return (
    <div className="card">
      <div className="card-header"><b>Manuel Temizlik</b></div>
      <div className="card-body text-center">
        <button className="btn" style={{ minWidth: 160, fontSize: '1.05rem', padding: '0.5rem 1.2rem' }} onClick={triggerCleanup} disabled={loading}>
          {loading ? 'Çalışıyor...' : 'Temizliği Başlat'}
        </button>
        {success && <div style={{ color: 'green', marginTop: 8 }}>{success}</div>}
        {error && <div style={{ color: 'red', marginTop: 8 }}>{error}</div>}
      </div>
    </div>
  );
} 