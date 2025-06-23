// Servis Durumu (API, CELERY, REDIS) kartı - bağımsız bileşen
import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8082/api/v1';

export default function ServiceStatus() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [firstLoad, setFirstLoad] = useState(true);

  const fetchData = () => {
    axios.get(`${API_URL}/status/system/health`)
      .then(res => {
        setHealth(res.data);
        setLoading(false);
        setFirstLoad(false);
      })
      .catch(() => {
        setError('API bağlantı hatası');
        setLoading(false);
        setFirstLoad(false);
      });
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="card">
      <div className="card-header">Servis Durumu</div>
      <div className="card-body">
        {firstLoad && loading ? <div>Yükleniyor...</div> : error ? <div style={{ color: 'red' }}>{error}</div> : health && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.7rem', textAlign: 'center' }}>
            <div>
              <div className="metric-label">API</div>
              <div className="metric-value text-success">{health?.services?.api?.status || '-'}</div>
            </div>
            <div>
              <div className="metric-label">CELERY</div>
              <div className={`metric-value ${health?.services?.celery?.status === 'healthy' ? 'text-success' : 'text-danger'}`}>{health?.services?.celery?.status || '-'}</div>
            </div>
            <div>
              <div className="metric-label">REDIS</div>
              <div className={`metric-value ${health?.services?.redis?.status === 'healthy' ? 'text-success' : 'text-danger'}`}>{health?.services?.redis?.status || '-'}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 