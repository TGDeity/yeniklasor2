// Sistem Kaynakları (CPU, RAM, Disk, GPU) kartı - bağımsız bileşen
import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8082/api/v1';

function formatGB(val) {
  if (typeof val !== 'number') return '-';
  if (val >= 1000) return (val / 1000).toFixed(1) + ' TB';
  return val.toFixed(1) + ' GB';
}
function formatPercent(val) {
  if (typeof val !== 'number') return '-';
  return val.toFixed(1) + '%';
}

export default function SystemResources() {
  const [resources, setResources] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [firstLoad, setFirstLoad] = useState(true);

  const fetchData = () => {
    axios.get(`${API_URL}/status/system/resources`)
      .then(res => {
        setResources(res.data);
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
      <div className="card-header">Sistem Kaynakları</div>
      <div className="card-body">
        {firstLoad && loading ? <div>Yükleniyor...</div> : error ? <div style={{ color: 'red' }}>{error}</div> : resources && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.7rem' }}>
            <div className="text-center">
              <div className="metric-label">CPU</div>
              <div className="metric-value text-primary">{formatPercent(resources.cpu_percent)}</div>
              <div className="metric-label">({resources.cpu_cores} çekirdek)</div>
            </div>
            <div className="text-center">
              <div className="metric-label">RAM</div>
              <div className="metric-value text-info">{formatGB(resources.memory_used_gb)}/{formatGB(resources.memory_total_gb)}</div>
              <div className="metric-label">({formatPercent(resources.memory_percent)})</div>
            </div>
            <div className="text-center">
              <div className="metric-label">Disk</div>
              <div className="metric-value text-success">{formatGB(resources.disk_total_gb - resources.disk_free_gb)}/{formatGB(resources.disk_total_gb)}</div>
              <div className="metric-label">({formatPercent(resources.disk_percent)})</div>
            </div>
            <div className="text-center">
              <div className="metric-label">GPU</div>
              <div className="metric-value text-danger">{resources.gpu && resources.gpu.available ? `${resources.gpu.gpus.length} GPU` : 'Yok'}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 