import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8082/api/v1';

function formatNumber(val) {
  if (typeof val !== 'number') return '-';
  return val.toLocaleString('tr-TR');
}

export default function PerformanceMetrics() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchMetrics = () => {
    setLoading(true);
    axios.get(`${API_URL}/status/system/performance`)
      .then(res => {
        setMetrics(res.data);
        setLoading(false);
      })
      .catch(() => {
        setError('API bağlantı hatası');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="card">
      <div className="card-header">Performans Metrikleri</div>
      <div className="card-body">
        {loading ? <div>Yükleniyor...</div> : error ? <div style={{ color: 'red' }}>{error}</div> : metrics && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.7rem', textAlign: 'center' }}>
            <div>
              <div className="metric-value text-primary">{formatNumber(metrics.upload_count || 0)}</div>
              <div className="metric-label">Uploads</div>
            </div>
            <div>
              <div className="metric-value text-info">{formatNumber(metrics.processing_count || 0)}</div>
              <div className="metric-label">Processing</div>
            </div>
            <div>
              <div className="metric-value text-success">{formatNumber(metrics.success_count || 0)}</div>
              <div className="metric-label">Success</div>
            </div>
            <div>
              <div className="metric-value text-danger">{formatNumber(metrics.error_count || 0)}</div>
              <div className="metric-label">Errors</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 