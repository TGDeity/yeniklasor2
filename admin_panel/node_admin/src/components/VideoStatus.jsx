import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8082/api/v1';

function formatPercent(val) {
  if (typeof val !== 'number') return '-';
  return val.toFixed(1) + '%';
}

export default function VideoStatus() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [firstLoad, setFirstLoad] = useState(true);

  const fetchVideos = () => {
    axios.get(`${API_URL}/status/videos`)
      .then(res => {
        setVideos(res.data.videos || []);
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
    fetchVideos();
    const interval = setInterval(fetchVideos, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="card">
      <div className="card-header">Video İşleme Durumu</div>
      <div className="card-body">
        {firstLoad && loading ? <div>Yükleniyor...</div> : error ? <div style={{ color: 'red' }}>{error}</div> : (
          videos.length === 0 ? <div>Video bulunamadı</div> : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.98rem' }}>
                <thead>
                  <tr style={{ color: 'var(--accent)', fontWeight: 600 }}>
                    <th style={{ padding: '0.3rem 0.5rem' }}>Video ID</th>
                    <th style={{ padding: '0.3rem 0.5rem' }}>Durum</th>
                    <th style={{ padding: '0.3rem 0.5rem' }}>İlerleme</th>
                    <th style={{ padding: '0.3rem 0.5rem' }}>Güncellendi</th>
                    <th style={{ padding: '0.3rem 0.5rem' }}>Aksiyon</th>
                  </tr>
                </thead>
                <tbody>
                  {videos.map(video => (
                    <tr key={video.video_id} style={{ background: 'none', borderBottom: '1px solid #23233644' }}>
                      <td style={{ padding: '0.3rem 0.5rem' }}><code>{video.video_id.slice(0, 8)}...</code></td>
                      <td style={{ padding: '0.3rem 0.5rem' }}>
                        <span style={{
                          display: 'inline-block',
                          borderRadius: 8,
                          padding: '2px 10px',
                          fontSize: '0.97em',
                          fontWeight: 600,
                          background: video.status === 'completed' ? 'var(--success)' : video.status === 'processing' ? 'var(--warning)' : video.status === 'failed' ? 'var(--danger)' : '#444',
                          color: '#fff',
                          minWidth: 60,
                          textAlign: 'center'
                        }}>
                          {video.status || 'unknown'}
                        </span>
                      </td>
                      <td style={{ padding: '0.3rem 0.5rem', minWidth: 100 }}>
                        {typeof video.progress === 'number' ? (
                          <div style={{ background: '#232336', borderRadius: 8, height: 16, width: '100%', position: 'relative' }}>
                            <div style={{
                              background: 'var(--accent)',
                              width: `${video.progress}%`,
                              height: '100%',
                              borderRadius: 8,
                              color: '#fff',
                              fontWeight: 600,
                              fontSize: '0.95em',
                              textAlign: 'center',
                              lineHeight: '16px',
                              transition: 'width 0.3s'
                            }}>{formatPercent(video.progress)}</div>
                          </div>
                        ) : <span className="text-muted">-</span>}
                      </td>
                      <td style={{ padding: '0.3rem 0.5rem' }}>{video.modified}</td>
                      <td style={{ padding: '0.3rem 0.5rem' }}>
                        {video.status === 'completed' && (
                          <a href={`${API_URL}/status/download/${video.video_id}`} className="btn btn-sm btn-success" target="_blank" rel="noopener noreferrer">
                            İndir
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        )}
      </div>
    </div>
  );
} 