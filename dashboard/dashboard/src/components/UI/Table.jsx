import React, { useState, useMemo } from 'react';
import './Table.css';

const Table = ({
    columns,
    data,
    onRowClick,
    sortable = true,
    className = '',
    pageSize = 15,
    ...props
}) => {
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
    const [currentPage, setCurrentPage] = useState(0);

    const handleSort = (key) => {
        if (!sortable) return;

        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
        setCurrentPage(0); // Reset to first page on sort
    };

    const sortedData = useMemo(() => {
        if (!sortConfig.key) return data;

        return [...data].sort((a, b) => {
            const aVal = a[sortConfig.key];
            const bVal = b[sortConfig.key];

            if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
            return 0;
        });
    }, [data, sortConfig]);

    // Reset page if data changes and current page is out of bounds
    const totalPages = Math.max(1, Math.ceil(sortedData.length / pageSize));
    const safePage = Math.min(currentPage, totalPages - 1);
    if (safePage !== currentPage) setCurrentPage(safePage);

    const paginatedData = useMemo(() => {
        const start = safePage * pageSize;
        return sortedData.slice(start, start + pageSize);
    }, [sortedData, safePage, pageSize]);

    const renderPagination = () => {
        if (sortedData.length <= pageSize) return null;

        const startItem = safePage * pageSize + 1;
        const endItem = Math.min((safePage + 1) * pageSize, sortedData.length);

        // Generate smart page numbers
        const pages = [];
        const maxVisible = 5;
        let startPage = Math.max(0, safePage - Math.floor(maxVisible / 2));
        let endPage = Math.min(totalPages - 1, startPage + maxVisible - 1);
        if (endPage - startPage < maxVisible - 1) {
            startPage = Math.max(0, endPage - maxVisible + 1);
        }

        if (startPage > 0) {
            pages.push(0);
            if (startPage > 1) pages.push('...');
        }
        for (let i = startPage; i <= endPage; i++) pages.push(i);
        if (endPage < totalPages - 1) {
            if (endPage < totalPages - 2) pages.push('...');
            pages.push(totalPages - 1);
        }

        return (
            <div className="table-pagination">
                <span className="pagination-info">
                    {startItem}–{endItem} of {sortedData.length}
                </span>
                <div className="pagination-controls">
                    <button
                        className="pagination-btn"
                        disabled={safePage === 0}
                        onClick={() => setCurrentPage(safePage - 1)}
                    >
                        ‹
                    </button>
                    {pages.map((p, i) =>
                        p === '...' ? (
                            <span key={`dots-${i}`} className="pagination-dots">…</span>
                        ) : (
                            <button
                                key={p}
                                className={`pagination-btn ${safePage === p ? 'active' : ''}`}
                                onClick={() => setCurrentPage(p)}
                            >
                                {p + 1}
                            </button>
                        )
                    )}
                    <button
                        className="pagination-btn"
                        disabled={safePage >= totalPages - 1}
                        onClick={() => setCurrentPage(safePage + 1)}
                    >
                        ›
                    </button>
                </div>
            </div>
        );
    };

    return (
        <div className={`table-wrapper ${className}`} {...props}>
            <div className="table-container">
                <table className="table">
                    <thead>
                        <tr>
                            {columns.map((column) => (
                                <th
                                    key={column.key}
                                    onClick={() => column.sortable !== false && handleSort(column.key)}
                                    className={`${sortable && column.sortable !== false ? 'sortable' : ''} col-${column.key}`}
                                >
                                    <div className="th-content">
                                        {column.label}
                                        {sortable && column.sortable !== false && sortConfig.key === column.key && (
                                            <span className="sort-icon">
                                                {sortConfig.direction === 'asc' ? '↑' : '↓'}
                                            </span>
                                        )}
                                    </div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {paginatedData.map((row, index) => (
                            <tr
                                key={row.id || index}
                                onClick={() => onRowClick && onRowClick(row)}
                                className={onRowClick ? 'clickable' : ''}
                            >
                                {columns.map((column) => (
                                    <td key={column.key} className={`col-${column.key}`}>
                                        {column.render ? column.render(row[column.key], row) : row[column.key]}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            {sortedData.length === 0 && (
                <div className="table-empty">
                    <p>No data available</p>
                </div>
            )}
            {renderPagination()}
        </div>
    );
};

export default React.memo(Table);
