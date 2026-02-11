import React, { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import './Table.css';
import './VirtualTable.css';

const ROW_HEIGHT = 48; // Fixed row height in px
const OVERSCAN = 8; // Extra rows rendered above/below viewport

const VirtualTable = ({
    columns,
    data,
    onRowClick,
    sortable = true,
    className = '',
    maxHeight = 'calc(100vh - 320px)', // Fits in page without page scroll
    ...props
}) => {
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
    const scrollContainerRef = useRef(null);
    const [scrollTop, setScrollTop] = useState(0);
    const [containerHeight, setContainerHeight] = useState(600);

    const handleSort = (key) => {
        if (!sortable) return;
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    const sortedData = useMemo(() => {
        if (!sortConfig.key) return data;
        return [...data].sort((a, b) => {
            const aVal = a[sortConfig.key];
            const bVal = b[sortConfig.key];
            if (aVal == null && bVal == null) return 0;
            if (aVal == null) return 1;
            if (bVal == null) return -1;
            if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
            return 0;
        });
    }, [data, sortConfig]);

    // Measure container height
    useEffect(() => {
        const container = scrollContainerRef.current;
        if (!container) return;

        const observer = new ResizeObserver(entries => {
            for (const entry of entries) {
                setContainerHeight(entry.contentRect.height);
            }
        });
        observer.observe(container);
        return () => observer.disconnect();
    }, []);

    const handleScroll = useCallback((e) => {
        setScrollTop(e.target.scrollTop);
    }, []);

    const totalHeight = sortedData.length * ROW_HEIGHT;
    const startIndex = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - OVERSCAN);
    const visibleCount = Math.ceil(containerHeight / ROW_HEIGHT) + 2 * OVERSCAN;
    const endIndex = Math.min(sortedData.length, startIndex + visibleCount);
    const visibleRows = sortedData.slice(startIndex, endIndex);
    const offsetTop = startIndex * ROW_HEIGHT;

    return (
        <div className={`virtual-table-wrapper ${className}`} {...props}>
            <div className="virtual-table-header-container">
                <table className="table virtual-table">
                    <thead>
                        <tr>
                            {columns.map((column) => (
                                <th
                                    key={column.key}
                                    onClick={() => column.sortable !== false && handleSort(column.key)}
                                    className={sortable && column.sortable !== false ? 'sortable' : ''}
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
                </table>
            </div>
            <div
                className="virtual-table-scroll-container"
                ref={scrollContainerRef}
                onScroll={handleScroll}
                style={{ maxHeight, overflowY: 'auto' }}
            >
                <div style={{ height: totalHeight, position: 'relative' }}>
                    <table className="table virtual-table" style={{ position: 'absolute', top: offsetTop, width: '100%' }}>
                        <tbody>
                            {visibleRows.map((row, index) => (
                                <tr
                                    key={row.id || (startIndex + index)}
                                    onClick={() => onRowClick && onRowClick(row)}
                                    className={onRowClick ? 'clickable' : ''}
                                    style={{ height: ROW_HEIGHT }}
                                >
                                    {columns.map((column) => (
                                        <td key={column.key}>
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
            </div>
        </div>
    );
};

export default VirtualTable;
