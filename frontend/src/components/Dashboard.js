import React, { useMemo, useState } from 'react';
import './Dashboard.css';
import { toast } from 'react-toastify';

function Dashboard({ history, onClear, user }) {
  const [dateFilter, setDateFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [search, setSearch] = useState('');

  const filteredHistory = useMemo(() => {
    const query = search.trim().toLowerCase();

    return history.filter(item => {
      const itemDate = item.date || '';
      const matchesDate = !dateFilter || itemDate === dateFilter;
      const matchesSource = sourceFilter === 'All' || item.source === sourceFilter;
      const matchesStatus = statusFilter === 'All' || item.status === statusFilter;
      const searchable = [
        item.filename,
        item.pincode,
        item.district,
        item.state,
        item.suggestion,
        item.message,
        item.ocr_engine,
      ].join(' ').toLowerCase();
      const matchesSearch = !query || searchable.includes(query);

      return matchesDate && matchesSource && matchesStatus && matchesSearch;
    });
  }, [dateFilter, history, search, sourceFilter, statusFilter]);

  const total = filteredHistory.length;
  const valid = filteredHistory.filter(item => item.status === 'Valid').length;
  const mismatch = filteredHistory.filter(item => item.status === 'Mismatch').length;
  const errors = filteredHistory.filter(item => item.status === 'Error').length;
  const bySource = filteredHistory.reduce((acc, item) => {
    acc[item.source] = (acc[item.source] || 0) + 1;
    return acc;
  }, {});

  const hasFilters = dateFilter || sourceFilter !== 'All' || statusFilter !== 'All' || search.trim();

  const clearFilters = () => {
    setDateFilter('');
    setSourceFilter('All');
    setStatusFilter('All');
    setSearch('');
  };

  const exportCSV = () => {
    if (filteredHistory.length === 0) {
      toast.error('No dashboard rows to export');
      return;
    }

    const headers = ['Time', 'Source', 'File', 'Status', 'PIN Code', 'District', 'State', 'Suggested PIN', 'OCR Engine', 'Message'];
    const rows = filteredHistory.map(item => [
      item.time,
      item.source,
      item.filename,
      item.status,
      item.pincode,
      item.district,
      item.state,
      item.suggestion,
      item.ocr_engine,
      `"${String(item.message || '').replace(/"/g, '""')}"`,
    ]);
    const csv = [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pin-dashboard-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Dashboard CSV exported');
  };

  return (
    <div className="dashboard">
      <div className="dashboard-top">
        <div>
          <h2 className="dashboard-title">Validation Dashboard</h2>
          <p className="dashboard-sub">
            {user
              ? `Signed in as ${user.email}. History is saved to your account.`
              : 'Guest history is stored locally in this browser.'}
          </p>
        </div>
        <div className="dashboard-actions">
          <button className="export-btn" onClick={exportCSV}>Export CSV</button>
          <button className="export-btn danger" onClick={onClear} disabled={history.length === 0}>Clear History</button>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="metric-card">
          <span className="metric-label">Total</span>
          <span className="metric-value">{total}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Valid</span>
          <span className="metric-value text-valid">{valid}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Mismatch</span>
          <span className="metric-value text-mismatch">{mismatch}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Errors</span>
          <span className="metric-value text-error">{errors}</span>
        </div>
      </div>

      <div className="source-row">
        {['Scan', 'Lookup', 'Bulk', 'Live'].map(source => (
          <span key={source} className="source-pill">{source}: {bySource[source] || 0}</span>
        ))}
      </div>

      <div className="filter-panel">
        <div className="filter-field">
          <label>Date</label>
          <input type="date" value={dateFilter} onChange={(e) => setDateFilter(e.target.value)} />
        </div>
        <div className="filter-field">
          <label>Source</label>
          <select value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)}>
            <option>All</option>
            <option>Scan</option>
            <option>Lookup</option>
            <option>Bulk</option>
            <option>Live</option>
          </select>
        </div>
        <div className="filter-field">
          <label>Status</label>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option>All</option>
            <option>Valid</option>
            <option>Mismatch</option>
            <option>Error</option>
          </select>
        </div>
        <div className="filter-field filter-search">
          <label>Search</label>
          <input
            type="search"
            placeholder="PIN, district, state, file..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <button className="export-btn filter-clear" onClick={clearFilters} disabled={!hasFilters}>
          Clear Filters
        </button>
      </div>

      <div className="dashboard-table-wrap">
        <table className="dashboard-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Time</th>
              <th>Source</th>
              <th>File</th>
              <th>Status</th>
              <th>PIN</th>
              <th>District</th>
              <th>State</th>
              <th>Suggestion</th>
            </tr>
          </thead>
          <tbody>
            {filteredHistory.length === 0 ? (
              <tr>
                <td colSpan="9" className="empty-history">
                  {history.length === 0 ? 'No validations yet.' : 'No results match the selected filters.'}
                </td>
              </tr>
            ) : filteredHistory.map((item, index) => (
              <tr key={item.id}>
                <td className="cell-num">{index + 1}</td>
                <td>{item.time}</td>
                <td>{item.source}</td>
                <td className="cell-file" title={item.filename}>{item.filename}</td>
                <td><span className={`dash-badge dash-${item.status.toLowerCase()}`}>{item.status}</span></td>
                <td className="cell-pin">{item.pincode}</td>
                <td>{item.district}</td>
                <td>{item.state}</td>
                <td className="cell-pin">{item.suggestion}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Dashboard;
