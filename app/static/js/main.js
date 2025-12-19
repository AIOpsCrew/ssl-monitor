// main.js - Client-side functionality for SSL Certificate Monitor

document.addEventListener('DOMContentLoaded', function() {
    // Status Filter Functionality
    const filterButtons = document.querySelectorAll('.filter-btn');
    const websiteRows = document.querySelectorAll('.grid-row');

    if (filterButtons.length > 0 && websiteRows.length > 0) {
        filterButtons.forEach(function(button) {
            button.addEventListener('click', function() {
                const filterStatus = this.getAttribute('data-status');

                // Update active button
                filterButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');

                // Filter rows
                websiteRows.forEach(function(row) {
                    const rowStatus = row.getAttribute('data-status');

                    if (filterStatus === 'all') {
                        row.classList.remove('hidden');
                    } else if (rowStatus === filterStatus) {
                        row.classList.remove('hidden');
                    } else {
                        row.classList.add('hidden');
                    }
                });
            });
        });
    }

    // Handle bulk import textarea for better UX
    const bulkImportTextarea = document.getElementById('domains');
    
    if (bulkImportTextarea) {
        // Auto-detect and format pasted content (handle CSV, etc.)
        bulkImportTextarea.addEventListener('paste', function(e) {
            // Wait for the paste to complete
            setTimeout(function() {
                const content = bulkImportTextarea.value;
                
                // Check if content seems to be a CSV file
                if (content.includes(',') && content.includes('\n')) {
                    // Try to extract domains from CSV format
                    const lines = content.split('\n');
                    const domains = [];
                    
                    for (const line of lines) {
                        const parts = line.split(',');
                        // Assume the first column contains the domain
                        if (parts.length > 0 && parts[0].trim()) {
                            // Remove http/https if present
                            let domain = parts[0].trim()
                                .replace(/^https?:\/\//i, '')
                                .replace(/\/.*$/, '');
                            domains.push(domain);
                        }
                    }
                    
                    if (domains.length > 0) {
                        // Replace textarea content with the extracted domains
                        bulkImportTextarea.value = domains.join(',');
                    }
                }
            }, 0);
        });
    }
    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash');
    
    if (flashMessages.length > 0) {
        setTimeout(function() {
            flashMessages.forEach(function(message) {
                message.style.opacity = '0';
                message.style.transition = 'opacity 0.5s ease';
                
                // Remove from DOM after fade out
                setTimeout(function() {
                    message.remove();
                }, 500);
            });
        }, 5000);
    }
    
    // Add confirmation for Remove button
    const removeButtons = document.querySelectorAll('a[href*="remove"]');
    
    removeButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            if (!confirm('Are you sure you want to remove this website?')) {
                event.preventDefault();
            }
        });
    });
    
    // Add tooltip functionality for status flags
    const statusFlags = document.querySelectorAll('.status-flag');
    
    statusFlags.forEach(function(flag) {
        const title = flag.getAttribute('title');
        
        if (title) {
            const tooltip = document.createElement('div');
            tooltip.classList.add('tooltip');
            tooltip.textContent = title;
            
            flag.addEventListener('mouseover', function() {
                flag.appendChild(tooltip);
                
                // Position the tooltip
                const flagRect = flag.getBoundingClientRect();
                tooltip.style.top = flagRect.height + 5 + 'px';
                tooltip.style.left = (flagRect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
            });
            
            flag.addEventListener('mouseout', function() {
                if (tooltip.parentNode === flag) {
                    flag.removeChild(tooltip);
                }
            });
        }
    });
});