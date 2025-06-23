import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8082/api/v1';

function formatMB(val) {
  if (typeof val !== 'number') return '-';
  if (val >= 1000) return (val / 1000).toFixed(1) + ' GB';
  return val.toLocaleString('tr-TR', { maximumFractionDigits: 2 }) + ' MB';
}

export default function StorageInfo() {
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [firstLoad, setFirstLoad] = useState(true);

  const fetchInfo = () => {
    axios.get(`${API_URL}/status/system/storage`)
      .then(res => {
        setInfo(res.data);
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
    fetchInfo();
    const interval = setInterval(fetchInfo, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="card">
      <div className="card-header">Depolama Bilgisi</div>
      <div className="card-body">
        {firstLoad && loading ? <div>Yükleniyor...</div> : error ? <div style={{ color: 'red' }}>{error}</div> : info && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.7rem' }}>
            {Object.entries(info).map(([dir, data]) => (
              <div className="card resource-card" key={dir} style={{ margin: 0, background: 'rgba(36,36,54,0.92)', boxShadow: '0 2px 12px 0 #0002', border: '1.2px solid #23233644', padding: '0.7rem 0.5rem', minWidth: 0 }}>
                <div className="card-body text-center" style={{ padding: 0 }}>
                  <b style={{ color: 'var(--accent)', fontSize: '1.01rem' }}>{dir}</b><br />
                  <span className="metric-value">{formatMB(data.size_mb)}</span><br />
                  <small className="metric-label">{data.file_count} dosya</small><br />
                  {!data.exists && <span className="bg-warning" style={{ display: 'inline-block', marginTop: 4 }}>Yok</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
} 