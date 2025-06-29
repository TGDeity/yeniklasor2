import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8082/api/v1';

export default function ActiveTasks() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [canceling, setCanceling] = useState('');
  const [success, setSuccess] = useState('');
  const [firstLoad, setFirstLoad] = useState(true);

  const fetchTasks = () => {
    axios.get(`${API_URL}/status/tasks/active`)
      .then(res => {
        setTasks(res.data.active_tasks || []);
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
    fetchTasks();
    const interval = setInterval(fetchTasks, 10000);
    return () => clearInterval(interval);
  }, []);

  const cancelTask = async (taskId) => {
    if (!window.confirm('Bu görevi iptal etmek istediğinize emin misiniz?')) return;
    setCanceling(taskId);
    setError('');
    setSuccess('');
    try {
      await axios.delete(`${API_URL}/status/tasks/${taskId}`);
      setSuccess('Görev iptal edildi!');
      fetchTasks();
    } catch (err) {
      setError('İptal hatası');
    }
    setCanceling('');
  };

  return (
    <div className="card">
      <div className="card-header">Aktif Görevler</div>
      <div className="card-body">
        {firstLoad && loading ? <div>Yükleniyor...</div> : error ? <div style={{ color: 'red' }}>{error}</div> : (
          tasks.length === 0 ? <div>Aktif görev yok</div> : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.98rem' }}>
                <thead>
                  <tr style={{ color: 'var(--accent)', fontWeight: 600 }}>
                    <th style={{ padding: '0.3rem 0.5rem' }}>Task ID</th>
                    <th style={{ padding: '0.3rem 0.5rem' }}>İsim</th>
                    <th style={{ padding: '0.3rem 0.5rem' }}>Worker</th>
                    <th style={{ padding: '0.3rem 0.5rem' }}>Başlangıç</th>
                    <th style={{ padding: '0.3rem 0.5rem' }}>Aksiyon</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.map(task => (
                    <tr key={task.task_id} style={{ background: 'none', borderBottom: '1px solid #23233644' }}>
                      <td style={{ padding: '0.3rem 0.5rem' }}><code>{task.task_id.slice(0, 8)}...</code></td>
                      <td style={{ padding: '0.3rem 0.5rem' }}>{task.name}</td>
                      <td style={{ padding: '0.3rem 0.5rem' }}>{task.worker}</td>
                      <td style={{ padding: '0.3rem 0.5rem' }}>{task.time_start || 'Bilinmiyor'}</td>
                      <td style={{ padding: '0.3rem 0.5rem' }}>
                        <button className="btn btn-sm btn-danger" disabled={canceling === task.task_id} onClick={() => cancelTask(task.task_id)}>
                          {canceling === task.task_id ? 'İptal...' : 'İptal Et'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        )}
        {success && <div style={{ color: 'green', marginTop: 8 }}>{success}</div>}
      </div>
    </div>
  );
} 