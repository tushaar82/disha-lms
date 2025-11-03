/**
 * Heatmap JavaScript Module
 * Uses Google Charts Calendar API for rendering attendance heatmaps
 */

class HeatmapManager {
    constructor() {
        this.charts = new Map();
        this.loadGoogleCharts();
    }

    loadGoogleCharts() {
        if (typeof google === 'undefined' || !google.charts) {
            const script = document.createElement('script');
            script.src = 'https://www.gstatic.com/charts/loader.js';
            script.onload = () => {
                google.charts.load('current', {'packages':['calendar']});
                google.charts.setOnLoadCallback(() => {
                    this.onGoogleChartsLoaded();
                });
            };
            document.head.appendChild(script);
        } else {
            google.charts.load('current', {'packages':['calendar']});
            google.charts.setOnLoadCallback(() => {
                this.onGoogleChartsLoaded();
            });
        }
    }

    onGoogleChartsLoaded() {
        document.dispatchEvent(new Event('googleChartsLoadedForHeatmap'));
    }

    initHeatmap(containerId, data, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return null;
        }

        // Show loading state
        container.innerHTML = '<div class="flex items-center justify-center h-64"><span class="loading loading-spinner loading-lg"></span></div>';

        // Wait for Google Charts to load
        if (typeof google === 'undefined' || !google.visualization) {
            document.addEventListener('googleChartsLoadedForHeatmap', () => {
                this.renderHeatmap(containerId, data, options);
            }, { once: true });
        } else {
            this.renderHeatmap(containerId, data, options);
        }
    }

    renderHeatmap(containerId, data, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) return;

        try {
            const dataTable = new google.visualization.DataTable();
            dataTable.addColumn({ type: 'date', id: 'Date' });
            dataTable.addColumn({ type: 'number', id: 'Hours' });

            // Process data
            const rows = [];
            for (let i = 1; i < data.length; i++) {
                const row = data[i];
                const dateStr = row[0];
                const hours = row[1];
                
                const date = this.parseDate(dateStr);
                if (date) {
                    rows.push([date, hours]);
                }
            }

            dataTable.addRows(rows);

            // Determine intensity levels
            const maxHours = Math.max(...rows.map(r => r[1]));
            
            // Default options
            const defaultOptions = {
                title: options.title || 'Attendance Calendar',
                height: options.height || 200,
                calendar: {
                    cellSize: options.cellSize || 20,
                    cellColor: {
                        stroke: '#e0e0e0',
                        strokeOpacity: 0.5,
                        strokeWidth: 1
                    },
                    focusedCellColor: {
                        stroke: '#4F46E5',
                        strokeOpacity: 1,
                        strokeWidth: 2
                    },
                    monthLabel: {
                        fontName: 'Inter',
                        fontSize: 12,
                        color: '#374151',
                        bold: true
                    },
                    dayOfWeekLabel: {
                        fontName: 'Inter',
                        fontSize: 10,
                        color: '#6B7280'
                    }
                },
                colorAxis: {
                    minValue: 0,
                    maxValue: maxHours,
                    colors: ['#F3F4F6', '#DBEAFE', '#93C5FD', '#3B82F6', '#1E40AF']
                },
                noDataPattern: {
                    backgroundColor: '#F9FAFB',
                    color: '#E5E7EB'
                },
                ...options
            };

            const chart = new google.visualization.Calendar(container);
            
            // Add select event for date clicks
            google.visualization.events.addListener(chart, 'select', () => {
                const selection = chart.getSelection();
                if (selection.length > 0) {
                    const row = selection[0].row;
                    this.onDateClick(containerId, rows[row]);
                }
            });

            chart.draw(dataTable, defaultOptions);
            this.charts.set(containerId, { chart, dataTable, options: defaultOptions, data: rows });

        } catch (error) {
            console.error('Error rendering heatmap:', error);
            container.innerHTML = '<div class="alert alert-error">Failed to render heatmap</div>';
        }
    }

    parseDate(dateString) {
        if (!dateString) return null;
        
        try {
            // Handle YYYY-MM-DD format
            if (dateString.match(/^\d{4}-\d{2}-\d{2}$/)) {
                const [year, month, day] = dateString.split('-').map(Number);
                return new Date(year, month - 1, day);
            }
            
            // Try parsing as Date object
            return new Date(dateString);
        } catch (error) {
            console.error('Error parsing date:', dateString, error);
            return null;
        }
    }

    updateHeatmap(containerId, newData) {
        if (this.charts.has(containerId)) {
            const { options } = this.charts.get(containerId);
            this.renderHeatmap(containerId, newData, options);
        }
    }

    exportHeatmap(containerId, filename = 'heatmap.png') {
        if (!this.charts.has(containerId)) {
            console.error('Chart not found');
            return;
        }

        const { chart } = this.charts.get(containerId);
        const imageURI = chart.getImageURI();
        
        // Create download link
        const link = document.createElement('a');
        link.href = imageURI;
        link.download = filename;
        link.click();
    }

    onDateClick(containerId, rowData) {
        const [date, hours] = rowData;
        
        // Show modal with date details
        this.showDateDetails(date, hours);
        
        // Emit custom event
        const event = new CustomEvent('heatmapDateClick', {
            detail: {
                containerId,
                date,
                hours
            }
        });
        document.dispatchEvent(event);
    }

    showDateDetails(date, hours) {
        // Create modal for date details
        const modal = document.createElement('div');
        modal.className = 'modal modal-open';
        modal.innerHTML = `
            <div class="modal-box">
                <h3 class="font-bold text-lg">Attendance Details</h3>
                <div class="py-4">
                    <p class="text-sm"><strong>Date:</strong> ${date.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
                    <p class="text-sm mt-2"><strong>Hours Studied:</strong> ${hours.toFixed(1)} hours</p>
                    <div class="mt-4">
                        <div class="radial-progress text-primary" style="--value:${Math.min((hours / 8) * 100, 100)};" role="progressbar">
                            ${Math.round((hours / 8) * 100)}%
                        </div>
                        <p class="text-xs text-gray-500 mt-2">of 8-hour target</p>
                    </div>
                </div>
                <div class="modal-action">
                    <button class="btn btn-sm" onclick="this.closest('.modal').remove()">Close</button>
                </div>
            </div>
            <div class="modal-backdrop" onclick="this.closest('.modal').remove()"></div>
        `;
        
        document.body.appendChild(modal);
    }

    addLegend(containerId) {
        const container = document.getElementById(containerId);
        if (!container || !this.charts.has(containerId)) return;

        const { data } = this.charts.get(containerId);
        const maxHours = Math.max(...data.map(r => r[1]));

        const legend = document.createElement('div');
        legend.className = 'flex items-center gap-2 mt-4 text-sm';
        legend.innerHTML = `
            <span class="text-gray-600">Less</span>
            <div class="flex gap-1">
                <div class="w-4 h-4 rounded" style="background-color: #F3F4F6;"></div>
                <div class="w-4 h-4 rounded" style="background-color: #DBEAFE;"></div>
                <div class="w-4 h-4 rounded" style="background-color: #93C5FD;"></div>
                <div class="w-4 h-4 rounded" style="background-color: #3B82F6;"></div>
                <div class="w-4 h-4 rounded" style="background-color: #1E40AF;"></div>
            </div>
            <span class="text-gray-600">More</span>
            <span class="text-gray-500 ml-4">(Max: ${maxHours.toFixed(1)} hours)</span>
        `;

        container.parentElement.appendChild(legend);
    }

    setDateRange(containerId, startDate, endDate) {
        // Filter data by date range and re-render
        if (!this.charts.has(containerId)) return;

        const { data, options } = this.charts.get(containerId);
        const filteredData = [['Date', 'Hours']];
        
        for (const row of data) {
            const date = row[0];
            if (date >= startDate && date <= endDate) {
                filteredData.push([date.toISOString().split('T')[0], row[1]]);
            }
        }

        this.renderHeatmap(containerId, filteredData, options);
    }

    destroy(containerId) {
        if (this.charts.has(containerId)) {
            const container = document.getElementById(containerId);
            if (container) {
                container.innerHTML = '';
            }
            this.charts.delete(containerId);
        }
    }
}

// Global instance
window.heatmapManager = new HeatmapManager();

// Helper function for easy initialization
window.initHeatmap = (containerId, data, options) => {
    return window.heatmapManager.initHeatmap(containerId, data, options);
};
