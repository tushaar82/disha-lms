/**
 * Gantt Chart JavaScript Module
 * Uses Google Charts Timeline API for rendering Gantt charts
 */

class GanttChartManager {
    constructor() {
        this.charts = new Map();
        this.loadGoogleCharts();
    }

    loadGoogleCharts() {
        if (typeof google === 'undefined' || !google.charts) {
            const script = document.createElement('script');
            script.src = 'https://www.gstatic.com/charts/loader.js';
            script.onload = () => {
                google.charts.load('current', {'packages':['timeline']});
                google.charts.setOnLoadCallback(() => {
                    this.onGoogleChartsLoaded();
                });
            };
            document.head.appendChild(script);
        } else {
            google.charts.load('current', {'packages':['timeline']});
            google.charts.setOnLoadCallback(() => {
                this.onGoogleChartsLoaded();
            });
        }
    }

    onGoogleChartsLoaded() {
        // Trigger custom event
        document.dispatchEvent(new Event('googleChartsLoaded'));
    }

    initGanttChart(containerId, data, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return null;
        }

        // Show loading state
        container.innerHTML = '<div class="flex items-center justify-center h-64"><span class="loading loading-spinner loading-lg"></span></div>';

        // Wait for Google Charts to load
        if (typeof google === 'undefined' || !google.visualization) {
            document.addEventListener('googleChartsLoaded', () => {
                this.renderGanttChart(containerId, data, options);
            }, { once: true });
        } else {
            this.renderGanttChart(containerId, data, options);
        }
    }

    renderGanttChart(containerId, data, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) return;

        try {
            const dataTable = new google.visualization.DataTable();
            dataTable.addColumn({ type: 'string', id: 'Task' });
            dataTable.addColumn({ type: 'string', id: 'Name' });
            dataTable.addColumn({ type: 'date', id: 'Start' });
            dataTable.addColumn({ type: 'date', id: 'End' });

            // Process data
            const rows = [];
            for (let i = 1; i < data.length; i++) {
                const row = data[i];
                const taskName = row[0];
                const startDate = this.parseDateTime(row[1]);
                const endDate = this.parseDateTime(row[2]);
                
                if (startDate && endDate) {
                    rows.push([
                        taskName,
                        taskName,
                        startDate,
                        endDate
                    ]);
                }
            }

            dataTable.addRows(rows);

            // Default options
            const defaultOptions = {
                height: Math.max(rows.length * 50, 300),
                timeline: {
                    showRowLabels: true,
                    showBarLabels: true,
                    groupByRowLabel: false
                },
                colors: ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'],
                backgroundColor: '#ffffff',
                ...options
            };

            const chart = new google.visualization.Timeline(container);
            
            // Add click event
            google.visualization.events.addListener(chart, 'select', () => {
                const selection = chart.getSelection();
                if (selection.length > 0) {
                    const row = selection[0].row;
                    this.onBarClick(containerId, rows[row]);
                }
            });

            chart.draw(dataTable, defaultOptions);
            this.charts.set(containerId, { chart, dataTable, options: defaultOptions });

        } catch (error) {
            console.error('Error rendering Gantt chart:', error);
            container.innerHTML = '<div class="alert alert-error">Failed to render chart</div>';
        }
    }

    parseDateTime(dateString) {
        if (!dateString) return null;
        
        try {
            // Handle different date formats
            if (dateString.includes('new Date')) {
                // Extract date parts from "new Date(year, month, day, hour, minute)"
                const match = dateString.match(/new Date\((\d+),\s*(\d+),\s*(\d+)(?:,\s*(\d+),\s*(\d+))?\)/);
                if (match) {
                    const year = parseInt(match[1]);
                    const month = parseInt(match[2]);
                    const day = parseInt(match[3]);
                    const hour = match[4] ? parseInt(match[4]) : 0;
                    const minute = match[5] ? parseInt(match[5]) : 0;
                    return new Date(year, month, day, hour, minute);
                }
            }
            
            // Try parsing as ISO string
            return new Date(dateString);
        } catch (error) {
            console.error('Error parsing date:', dateString, error);
            return null;
        }
    }

    updateGanttChart(containerId, newData) {
        if (this.charts.has(containerId)) {
            const { options } = this.charts.get(containerId);
            this.renderGanttChart(containerId, newData, options);
        }
    }

    exportGanttChart(containerId, filename = 'gantt-chart.png') {
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

    onBarClick(containerId, rowData) {
        // Emit custom event for bar click
        const event = new CustomEvent('ganttBarClick', {
            detail: {
                containerId,
                taskName: rowData[0],
                startDate: rowData[2],
                endDate: rowData[3]
            }
        });
        document.dispatchEvent(event);
    }

    changeView(containerId, view) {
        // Change time scale (daily, weekly, monthly)
        if (!this.charts.has(containerId)) return;

        const { dataTable, options } = this.charts.get(containerId);
        const container = document.getElementById(containerId);
        
        const viewOptions = {
            daily: { timeline: { ...options.timeline, barHeight: 30 } },
            weekly: { timeline: { ...options.timeline, barHeight: 20 } },
            monthly: { timeline: { ...options.timeline, barHeight: 15 } }
        };

        const newOptions = { ...options, ...viewOptions[view] };
        const chart = new google.visualization.Timeline(container);
        chart.draw(dataTable, newOptions);
        
        this.charts.set(containerId, { chart, dataTable, options: newOptions });
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
window.ganttChartManager = new GanttChartManager();

// Helper function for easy initialization
window.initGanttChart = (containerId, data, options) => {
    return window.ganttChartManager.initGanttChart(containerId, data, options);
};
