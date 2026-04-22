import React from 'react';
import './BulkResults.css';
import { toast } from 'react-toastify';

function BulkResults({ results }) {
  if (!results || results.length === 0) return null;

  const validCount = results.filter(r => r.status === 'Valid').length;
  const errorCount = results.filter(r => r.status === 'Error').length;

  const exportCSV = () => {
    const headers = ['File', 'Status', 'PIN Code', 'District', 'State', 'Suggested PIN', 'OCR Engine', 'Message'];
    const rows = results.map(r => [
      r.filename,
      r.status,
      r.pincode,
      r.district,
      r.state,
      r.suggestion,
      r.ocr_engine,
      `"${r.message.replace(/"/g, '""')}"`,
    ]);
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pin-validation-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('CSV exported');
  };

  return (
    <div className="bulk-results">
      {/* Summary bar */}
      <div className="bulk-summary">
        <div className="bulk-summary-left">
          <h2 className="bulk-title">Bulk Results</h2>
          <div className="bulk-stats">
            <span className="stat">{results.length} total</span>
            <span className="stat stat-valid">{validCount} valid</span>
            <span className="stat stat-mismatch">{results.length - validCount - errorCount} mismatch</span>
            {errorCount > 0 && <span className="stat stat-error">{errorCount} errors</span>}
          </div>
        </div>
        <button className="export-btn" onClick={exportCSV}>
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
            <path d="M8 1v10M8 11L5 8M8 11l3-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M2 12v2h12v-2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Export CSV
        </button>
      </div>

      {/* Results table */}
      <div className="bulk-table-wrap">
        <table className="bulk-table">
          <thead>
            <tr>
              <th>#</th>
              <th>File</th>
              <th>Status</th>
              <th>PIN</th>
              <th>District</th>
              <th>State</th>
              <th>Suggestion</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r, i) => (
              <tr key={i} className={`row-${r.status.toLowerCase()}`}>
                <td className="cell-num">{i + 1}</td>
                <td className="cell-file" title={r.filename}>
                  {r.filename.length > 24 ? r.filename.slice(0, 22) + '...' : r.filename}
                </td>
                <td>
                  <span className={`table-badge ${
                    r.status === 'Valid' ? 'tb-valid' :
                    r.status === 'Error' ? 'tb-error' : 'tb-mismatch'
                  }`}>
                    {r.status}
                  </span>
                </td>
                <td className="cell-pin">{r.pincode}</td>
                <td>{r.district}</td>
                <td>{r.state}</td>
                <td className="cell-pin">{r.suggestion}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default BulkResults;
