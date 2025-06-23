import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8082/api/v1';

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <div style={{ color: 'var(--accent)', fontWeight: 700, fontSize: '1.01rem', marginBottom: 8 }}>{title}</div>
      {children}
    </div>
  );
}

export default function ConfigPanel() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [firstLoad, setFirstLoad] = useState(true);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = () => {
    setLoading(true);
    axios.get(`${API_URL}/config`)
      .then(res => {
        setConfig(res.data);
        setLoading(false);
        setFirstLoad(false);
      })
      .catch(() => {
        setError('API bağlantı hatası');
        setLoading(false);
        setFirstLoad(false);
      });
  };

  const handleUpdate = async (setting_path, value) => {
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      await axios.post(`${API_URL}/config/update`, { setting_path, value });
      setSuccess('Başarıyla güncellendi!');
      fetchConfig();
    } catch (err) {
      setError('Güncelleme hatası');
    }
    setSaving(false);
  };

  if (firstLoad && loading) return <div>Yükleniyor...</div>;
  if (error) return <div style={{ color: 'red' }}>{error}</div>;
  if (!config) return null;

  return (
    <div className="card">
      <div className="card-header">Ayarlar</div>
      <div className="card-body">
        <Section title="Timeout Ayarları (saniye)">
          {Object.entries(config.timeouts).map(([key, value]) => (
            <div key={key} style={{ marginBottom: 10, display: 'flex', alignItems: 'center', gap: 10 }}>
              <label style={{ minWidth: 90, color: 'var(--text-fade)', fontSize: '0.97rem' }}>{key}: <b style={{ color: 'var(--accent)' }}>{value}</b></label>
              <input type="range" min={60} max={3600} value={value} disabled={saving}
                onChange={e => handleUpdate(`timeouts.${key}`, parseInt(e.target.value, 10))} style={{ flex: 1 }} />
            </div>
          ))}
        </Section>
        <Section title="Kaynak Limitleri">
          {Object.entries(config.resources).map(([key, value]) => (
            <div key={key} style={{ marginBottom: 10, display: 'flex', alignItems: 'center', gap: 10 }}>
              <label style={{ minWidth: 120, color: 'var(--text-fade)', fontSize: '0.97rem' }}>{key}: <b style={{ color: 'var(--accent)' }}>{value}</b></label>
              <input type="range"
                min={key.includes('mb') ? 100 : key.includes('gb') ? 1 : 1}
                max={key.includes('mb') ? 2000 : key.includes('gb') ? 16 : 8}
                value={value} disabled={saving}
                onChange={e => handleUpdate(`resources.${key}`, parseInt(e.target.value, 10))} style={{ flex: 1 }} />
            </div>
          ))}
        </Section>
        <Section title="Performans Ayarları">
          {Object.entries(config.performance).map(([key, value]) => (
            <div key={key} style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 10 }}>
              <input className="form-check-input" type="checkbox" id={key} checked={!!value} disabled={saving}
                onChange={e => handleUpdate(`performance.${key}`, e.target.checked)} style={{ marginRight: 8 }} />
              <label className="form-check-label" htmlFor={key} style={{ color: 'var(--text-fade)', fontSize: '0.97rem' }}>{key}</label>
            </div>
          ))}
        </Section>
        <Section title="Temizlik Ayarları">
          {Object.entries(config.cleanup).map(([key, value]) => (
            <div key={key} style={{ marginBottom: 10, display: 'flex', alignItems: 'center', gap: 10 }}>
              {key === 'auto_cleanup_temp_files' ? (
                <>
                  <input className="form-check-input" type="checkbox" id={key} checked={!!value} disabled={saving}
                    onChange={e => handleUpdate(`cleanup.${key}`, e.target.checked)} style={{ marginRight: 8 }} />
                  <label className="form-check-label" htmlFor={key} style={{ color: 'var(--text-fade)', fontSize: '0.97rem' }}>{key}</label>
                </>
              ) : (
                <>
                  <label style={{ minWidth: 120, color: 'var(--text-fade)', fontSize: '0.97rem' }}>{key}: <b style={{ color: 'var(--accent)' }}>{value}</b></label>
                  <input type="range" min={300} max={86400} value={value} disabled={saving}
                    onChange={e => handleUpdate(`cleanup.${key}`, parseInt(e.target.value, 10))} style={{ flex: 1 }} />
                </>
              )}
            </div>
          ))}
        </Section>
        {saving && <div>Kaydediliyor...</div>}
        {success && <div style={{ color: 'green' }}>{success}</div>}
        {error && <div style={{ color: 'red' }}>{error}</div>}
      </div>
    </div>
  );
} 