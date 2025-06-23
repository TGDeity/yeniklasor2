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
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 14 }}>
            <span style={{ fontWeight: 600, fontSize: '1.01rem', color: 'var(--accent)' }}>Performans Parametreleri</span>
            <div style={{ position: 'relative', display: 'inline-block', marginLeft: 8 }}>
              <span
                style={{
                  display: 'inline-block',
                  width: 20,
                  height: 20,
                  borderRadius: '50%',
                  background: '#232336',
                  color: '#fff',
                  textAlign: 'center',
                  lineHeight: '20px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  border: '1.5px solid #444',
                  fontSize: '1.05rem',
                  boxShadow: '0 1px 4px #0002'
                }}
                tabIndex={0}
                onMouseEnter={e => e.currentTarget.nextSibling.style.display = 'block'}
                onMouseLeave={e => e.currentTarget.nextSibling.style.display = 'none'}
                onFocus={e => e.currentTarget.nextSibling.style.display = 'block'}
                onBlur={e => e.currentTarget.nextSibling.style.display = 'none'}
              >i</span>
              <div
                style={{
                  display: 'none',
                  position: 'absolute',
                  left: 28,
                  top: -8,
                  zIndex: 10,
                  background: '#232336',
                  color: '#e0e0e0',
                  border: '1.5px solid #444',
                  borderRadius: 7,
                  padding: '12px 16px',
                  minWidth: 270,
                  fontSize: '0.97rem',
                  lineHeight: 1.6,
                  boxShadow: '0 2px 12px #0003',
                  pointerEvents: 'none'
                }}
              >
                <b>enable_gpu_acceleration:</b> GPU hızlandırmayı aktif eder. Açık olduğunda, Whisper ve FFmpeg işlemleri GPU üzerinden çok daha hızlı çalışır.<br/>
                <b>enable_model_caching:</b> Modellerin bellekte (RAM) tutulmasını sağlar. Açık olduğunda, Whisper ve çeviri modelleri tekrar tekrar yüklenmez, hız artar.<br/>
                <b>enable_batch_processing:</b> Özellikle altyazı çevirisinde toplu işlem yapar. Açık olduğunda, çok sayıda altyazı satırı bir arada çevrilir ve çeviri işlemi hızlanır.
              </div>
            </div>
          </div>
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