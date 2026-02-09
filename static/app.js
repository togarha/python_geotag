/**
 * Geotag Application - Main JavaScript
 */

// Global State
const state = {
    currentView: 'thumbnails',
    currentFolder: '',
    photos: [],
    filteredPhotos: [],
    gpxTracks: [],
    selectedPhotoIndex: null,
    filterType: 'all',
    searchQuery: '',
    dateFrom: null,
    dateTo: null,
    sortBy: 'time',
    thumbnailSize: 200,
    mapProvider: 'osm', // 'osm' or 'google'
    gpxMap: null,
    photoMap: null,
    photoMapMarkers: {
        exif: null,
        gpx: null,
        manual: null,
        final: null
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeMenu();
    initializeViews();
    initializeThumbnailsView();
    initializeGPXView();
    initializePositionsView();
    initializeSettingsView();
    initializeLargePhotoView();
    initializeEditMetadataModal();
    initializeKeyboardShortcuts();
    
    // Load settings from backend
    loadSettings();
});

// ==================== Menu Management ====================

function initializeMenu() {
    const menuToggle = document.getElementById('menu-toggle');
    const sideMenu = document.getElementById('side-menu');
    const mainContent = document.getElementById('main-content');
    const menuLinks = document.querySelectorAll('.menu-link');

    // Toggle menu on button click
    menuToggle.addEventListener('click', () => {
        sideMenu.classList.toggle('expanded');
        mainContent.classList.toggle('menu-open');
    });

    // Expand menu on hover
    sideMenu.addEventListener('mouseenter', () => {
        sideMenu.classList.add('expanded');
        mainContent.classList.add('menu-open');
    });

    // Collapse menu when mouse leaves (optional, can be removed for sticky behavior)
    sideMenu.addEventListener('mouseleave', () => {
        // Uncomment to auto-collapse on mouse leave
        // sideMenu.classList.remove('expanded');
        // mainContent.classList.remove('menu-open');
    });

    // Menu link clicks
    menuLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const view = link.dataset.view;
            switchView(view);
            
            // Update active state
            menuLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });
}

function switchView(viewName) {
    const views = document.querySelectorAll('.view-container');
    views.forEach(view => view.classList.remove('active'));
    
    const targetView = document.getElementById(`${viewName}-view`);
    if (targetView) {
        targetView.classList.add('active');
        state.currentView = viewName;
        
        // Initialize or refresh GPX map if switching to GPX view
        if (viewName === 'gpx') {
            // Sync GPX map provider selector with current state
            const gpxMapProviderSelect = document.getElementById('gpx-map-provider');
            if (gpxMapProviderSelect) {
                gpxMapProviderSelect.value = state.gpxMapProvider;
            }
            
            if (!state.gpxMap) {
                initializeGPXMap();
            } else {
                // Map exists, just ensure proper sizing
                state.gpxMap.invalidateSize();
            }
            // Reload tracks if they exist
            if (state.gpxTracks && state.gpxTracks.length > 0) {
                displayGPXTracks();
            }
        }
        
        // Load format if switching to settings view
        if (viewName === 'settings') {
            loadFilenameFormat();
        }
    }
}

function initializeViews() {
    // Set initial view
    switchView('thumbnails');
}

// ==================== Thumbnails View ====================

function initializeThumbnailsView() {
    const folderPathInput = document.getElementById('folder-path-input');
    const loadFolderBtn = document.getElementById('load-folder-btn');
    const recursiveCheckbox = document.getElementById('recursive-checkbox');
    const mapProviderSelect = document.getElementById('map-provider');
    const sortSelect = document.getElementById('sort-select');
    const filterSelect = document.getElementById('filter-select');
    const searchInput = document.getElementById('search-input');
    const dateRangeToggle = document.getElementById('date-range-toggle');
    const dateRangeControls = document.getElementById('date-range-controls');
    const dateFrom = document.getElementById('date-from');
    const dateTo = document.getElementById('date-to');
    const clearDateRange = document.getElementById('clear-date-range');
    const tagAllVisibleBtn = document.getElementById('tag-all-visible');
    const untagAllVisibleBtn = document.getElementById('untag-all-visible');
    const exportAllBtn = document.getElementById('export-all');
    const exportTaggedBtn = document.getElementById('export-tagged');
    const thumbnailSizeSlider = document.getElementById('thumbnail-size');
    const sizeValue = document.getElementById('size-value');

    // Map provider select
    mapProviderSelect.addEventListener('change', () => {
        state.mapProvider = mapProviderSelect.value;
        state.gpxMapProvider = mapProviderSelect.value; // Sync GPX map provider
        
        // Update GPX map provider selector
        const gpxMapProviderSelect = document.getElementById('gpx-map-provider');
        if (gpxMapProviderSelect) {
            gpxMapProviderSelect.value = mapProviderSelect.value;
        }
        
        // Properly remove Leaflet maps before resetting
        if (state.photoMap) {
            if (state.photoMap.remove) {
                state.photoMap.remove();
            }
            state.photoMap = null;
        }
        if (state.gpxMap) {
            if (state.gpxMap.remove) {
                state.gpxMap.remove();
            }
            state.gpxMap = null;
        }
        
        // Refresh GPX tracks if tracks are loaded AND GPX view is visible
        const gpxView = document.getElementById('gpx-view');
        if (state.gpxTracks && state.gpxTracks.length > 0 && gpxView && gpxView.style.display !== 'none') {
            displayGPXTracks();
        }
        
        // Refresh current photo display if in large photo view
        if (state.currentPhotoIndex !== null && state.photos && state.photos[state.currentPhotoIndex]) {
            displayPhotoMap(state.photos[state.currentPhotoIndex], state.currentPhotoIndex);
        }
    });

    // Load folder button
    if (loadFolderBtn) {
        loadFolderBtn.addEventListener('click', async () => {
            const folderPath = folderPathInput.value.trim();
            if (folderPath) {
                const recursive = recursiveCheckbox.checked;
                await scanFolder(folderPath, recursive);
            } else {
                alert('Please enter a folder path');
            }
        });
    }

    // Enter key in text input
    if (folderPathInput) {
        folderPathInput.addEventListener('keypress', async (e) => {
            if (e.key === 'Enter') {
                const folderPath = folderPathInput.value.trim();
                if (folderPath) {
                    const recursive = recursiveCheckbox.checked;
                    await scanFolder(folderPath, recursive);
                }
            }
        });
    }

    // Recursive checkbox
    recursiveCheckbox.addEventListener('change', () => {
        saveSettings();
        if (state.currentFolder) {
            scanFolder(state.currentFolder, recursiveCheckbox.checked);
        }
    });

    // Sort select
    sortSelect.addEventListener('change', async () => {
        state.sortBy = sortSelect.value;
        await fetch('/api/sort', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sort_by: state.sortBy })
        });
        await loadPhotos();
        saveSettings();
    });

    // Filter select (combined tag and GPS filter)
    filterSelect.addEventListener('change', () => {
        state.filterType = filterSelect.value;
        applyFilters();
    });
    
    // Search input
    searchInput.addEventListener('input', () => {
        state.searchQuery = searchInput.value.trim().toLowerCase();
        applyFilters();
    });
    
    // Date range toggle
    dateRangeToggle.addEventListener('click', () => {
        const isVisible = dateRangeControls.style.display !== 'none';
        dateRangeControls.style.display = isVisible ? 'none' : 'flex';
    });
    
    // Date range inputs
    dateFrom.addEventListener('change', () => {
        state.dateFrom = dateFrom.value ? new Date(dateFrom.value) : null;
        applyFilters();
    });
    
    dateTo.addEventListener('change', () => {
        state.dateTo = dateTo.value ? new Date(dateTo.value + 'T23:59:59') : null;
        applyFilters();
    });
    
    // Clear date range
    clearDateRange.addEventListener('click', () => {
        dateFrom.value = '';
        dateTo.value = '';
        state.dateFrom = null;
        state.dateTo = null;
        applyFilters();
    });
    
    // Tag all visible button
    tagAllVisibleBtn.addEventListener('click', async () => {
        if (state.filteredPhotos.length === 0) {
            alert('No photos to tag.');
            return;
        }
        
        if (!confirm(`Tag all ${state.filteredPhotos.length} visible photos?`)) {
            return;
        }
        
        await bulkTagPhotos(state.filteredPhotos.map(p => p.original_index), true);
    });
    
    // Untag all visible button
    untagAllVisibleBtn.addEventListener('click', async () => {
        if (state.filteredPhotos.length === 0) {
            alert('No photos to untag.');
            return;
        }
        
        if (!confirm(`Untag all ${state.filteredPhotos.length} visible photos?`)) {
            return;
        }
        
        await bulkTagPhotos(state.filteredPhotos.map(p => p.original_index), false);
    });
    
    // Export all button
    exportAllBtn.addEventListener('click', async () => {
        if (!confirm(`Export all photos to the configured export folder?`)) {
            return;
        }
        await exportPhotos('all');
    });
    
    // Export tagged button
    exportTaggedBtn.addEventListener('click', async () => {
        const taggedCount = state.photos.filter(p => p.tagged).length;
        if (taggedCount === 0) {
            alert('No tagged photos to export.');
            return;
        }
        
        if (!confirm(`Export ${taggedCount} tagged photos to the configured export folder?`)) {
            return;
        }
        await exportPhotos('tagged');
    });

    // Thumbnail size slider
    thumbnailSizeSlider.addEventListener('input', (e) => {
        state.thumbnailSize = parseInt(e.target.value);
        sizeValue.textContent = `${state.thumbnailSize}px`;
        updateThumbnailSizes();
    });
    
    thumbnailSizeSlider.addEventListener('change', () => {
        saveSettings();
    });
}

async function scanFolder(folderPath, recursive) {
    const loadingIndicator = document.getElementById('loading-indicator');
    
    try {
        // Show loading indicator
        if (loadingIndicator) {
            loadingIndicator.style.display = 'flex';
        }
        
        const response = await fetch('/api/scan-folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folder_path: folderPath, recursive })
        });

        const result = await response.json();
        
        if (result.success) {
            state.currentFolder = result.folder;
            state.photos = result.data;
            
            // Update window title
            document.getElementById('page-title').textContent = `Geotag - ${folderPath}`;
            
            // Save folder path to settings
            saveSettings();
            
            applyFilters();
        } else {
            alert('Error scanning folder: ' + result.detail);
        }
    } catch (error) {
        console.error('Error scanning folder:', error);
        alert('Error scanning folder. Make sure the server is running.');
    } finally {
        // Hide loading indicator
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
    }
}

async function loadPhotos() {
    try {
        // Fetch all photos (no backend filtering, we do it client-side)
        const response = await fetch(`/api/photos?filter_type=all`);
        const result = await response.json();
        
        if (result.success) {
            state.photos = result.data;
            applyFilters();
        }
    } catch (error) {
        console.error('Error loading photos:', error);
    }
}

function applyFilters() {
    // Start with all photos
    let filtered = [...state.photos];
    
    // Apply combined tag and GPS filter
    if (state.filterType && state.filterType !== 'all') {
        filtered = filtered.filter(photo => {
            const hasExif = photo.exif_latitude !== -360;
            const hasGpx = photo.gpx_latitude !== -360;
            const hasManual = photo.manual_latitude !== -360;
            const hasFinal = photo.final_latitude !== -360;
            const isTagged = photo.tagged;
            
            switch (state.filterType) {
                // Tag filters
                case 'tagged':
                    return isTagged;
                case 'untagged':
                    return !isTagged;
                
                // GPS filters
                case 'with-gps':
                    return hasFinal;
                case 'no-gps':
                    return !hasFinal;
                case 'with-exif':
                    return hasExif;
                case 'with-gpx':
                    return hasGpx;
                case 'with-manual':
                    return hasManual;
                
                // Combined filters
                case 'tagged-with-gps':
                    return isTagged && hasFinal;
                case 'tagged-no-gps':
                    return isTagged && !hasFinal;
                case 'untagged-with-gps':
                    return !isTagged && hasFinal;
                case 'untagged-no-gps':
                    return !isTagged && !hasFinal;
                
                default:
                    return true;
            }
        });
    }
    
    // Apply search filter
    if (state.searchQuery) {
        filtered = filtered.filter(photo => {
            return photo.filename.toLowerCase().includes(state.searchQuery);
        });
    }
    
    // Apply date range filter
    if (state.dateFrom || state.dateTo) {
        filtered = filtered.filter(photo => {
            // Use exif_capture_time or creation_time for filtering
            const photoDate = photo.exif_capture_time ? new Date(photo.exif_capture_time) : 
                             photo.creation_time ? new Date(photo.creation_time) : null;
            
            if (!photoDate) return false;
            
            if (state.dateFrom && photoDate < state.dateFrom) return false;
            if (state.dateTo && photoDate > state.dateTo) return false;
            
            return true;
        });
    }
    
    state.filteredPhotos = filtered;
    displayPhotos();
}

async function bulkTagPhotos(indices, tagged) {
    try {
        const response = await fetch('/api/photos/bulk-tag', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ indices, tagged })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Update local state
            indices.forEach(idx => {
                const photo = state.photos.find(p => p.original_index === idx);
                if (photo) {
                    photo.tagged = tagged;
                }
            });
            
            // Reload photos to reflect changes
            await loadPhotos();
            alert(`Successfully tagged ${result.count} photos.`);
        }
    } catch (error) {
        console.error('Error bulk tagging photos:', error);
        alert('Error tagging photos.');
    }
}

async function exportPhotos(exportType) {
    const modal = document.getElementById('export-progress-modal');
    const progressBar = document.getElementById('export-progress-bar');
    const progressText = document.getElementById('export-progress-text');
    const currentFileText = document.getElementById('export-current-file');
    
    try {
        // Show the progress modal
        modal.style.display = 'block';
        progressBar.style.width = '0%';
        progressBar.textContent = '0%';
        progressText.textContent = 'Preparing export...';
        currentFileText.textContent = '';
        
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ export_type: exportType })
        });
        
        if (!response.ok) {
            throw new Error('Export request failed');
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.error) {
                            modal.style.display = 'none';
                            alert('Export failed: ' + data.error);
                            return;
                        }
                        
                        if (data.progress !== undefined) {
                            progressBar.style.width = data.progress + '%';
                            progressBar.textContent = data.progress + '%';
                        }
                        
                        if (data.current && data.total) {
                            progressText.textContent = `Exporting photo ${data.current} of ${data.total}`;
                        }
                        
                        if (data.filename) {
                            currentFileText.textContent = data.filename;
                        }
                        
                        if (data.done) {
                            setTimeout(() => {
                                modal.style.display = 'none';
                                alert(data.message);
                            }, 500);
                        }
                    } catch (parseError) {
                        console.error('Failed to parse SSE data:', line, parseError);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error exporting photos:', error);
        modal.style.display = 'none';
        alert('Error exporting photos: ' + error.message);
    }
}


function displayPhotos() {
    displayPhotoList();
    displayPhotoGrid();
    updateStatusBar();
}

function updateStatusBar() {
    const totalPhotos = state.photos.length;
    const visiblePhotos = state.filteredPhotos.length;
    const taggedPhotos = state.photos.filter(photo => photo.tagged).length;
    
    document.getElementById('status-total').textContent = totalPhotos;
    document.getElementById('status-visible').textContent = visiblePhotos;
    document.getElementById('status-tagged').textContent = taggedPhotos;
}

function displayPhotoList() {
    const photoList = document.getElementById('photo-list');
    if (!photoList) {
        console.error('photo-list element not found!');
        return;
    }
    photoList.innerHTML = '';

    state.filteredPhotos.forEach((photo, index) => {
        const item = document.createElement('div');
        item.className = 'photo-list-item';
        item.textContent = photo.filename;
        item.dataset.index = index;
        
        item.addEventListener('click', () => selectPhoto(index));
        item.addEventListener('dblclick', () => openLargePhotoView(index));
        
        photoList.appendChild(item);
    });
}

function displayPhotoGrid() {
    const photoGrid = document.getElementById('photo-grid');
    if (!photoGrid) {
        console.error('photo-grid element not found!');
        return;
    }
    photoGrid.innerHTML = '';

    state.filteredPhotos.forEach((photo, index) => {
        const item = document.createElement('div');
        item.className = 'photo-grid-item';
        item.dataset.index = index;
        item.style.width = `${state.thumbnailSize}px`;
        item.style.height = `${state.thumbnailSize}px`;

        const img = document.createElement('img');
        // Use original_index from backend to get correct thumbnail
        const photoIndex = photo.original_index !== undefined ? photo.original_index : index;
        // Add timestamp to prevent caching issues when sort order changes
        img.src = `/api/photo-thumbnail/${photoIndex}?size=${state.thumbnailSize}&t=${Date.now()}`;
        img.alt = photo.filename;
        img.title = photo.filename; // Tooltip with filename
        img.loading = 'lazy';

        const checkboxOverlay = document.createElement('div');
        checkboxOverlay.className = 'checkbox-overlay';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = photo.tagged;
        checkbox.addEventListener('change', (e) => {
            e.stopPropagation();
            togglePhotoTag(photoIndex, checkbox.checked);
        });
        
        checkboxOverlay.appendChild(checkbox);

        item.appendChild(img);
        item.appendChild(checkboxOverlay);
        
        item.addEventListener('click', (e) => {
            if (e.target.type !== 'checkbox') {
                selectPhoto(index);
            }
        });
        
        item.addEventListener('dblclick', (e) => {
            if (e.target.type !== 'checkbox') {
                openLargePhotoView(index);
            }
        });

        photoGrid.appendChild(item);
    });
}

function updateThumbnailSizes() {
    const photoGrid = document.getElementById('photo-grid');
    
    // Update grid item sizes
    const items = photoGrid.querySelectorAll('.photo-grid-item');
    items.forEach(item => {
        item.style.width = `${state.thumbnailSize}px`;
        item.style.height = `${state.thumbnailSize}px`;
    });
    
    // Reload thumbnails with new size
    const images = photoGrid.querySelectorAll('img');
    images.forEach((img, index) => {
        img.src = `/api/photo-thumbnail/${index}?size=${state.thumbnailSize}`;
    });
}

function selectPhoto(index) {
    state.selectedPhotoIndex = index;
    
    // Update list items
    document.querySelectorAll('.photo-list-item').forEach((item, i) => {
        item.classList.toggle('selected', i === index);
    });
    
    // Update grid items
    document.querySelectorAll('.photo-grid-item').forEach((item, i) => {
        item.classList.toggle('selected', i === index);
    });
}

async function togglePhotoTag(index, tagged) {
    try {
        await fetch(`/api/photos/${index}/tag`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tagged })
        });
        
        // Update local state - find by original_index
        const photo = state.photos.find(p => p.original_index === index);
        if (photo) {
            photo.tagged = tagged;
        }
        
        // Refresh the displays to show updated tag status
        applyFilters();
    } catch (error) {
        console.error('Error toggling tag:', error);
    }
}

// ==================== GPX View ====================

function initializeGPXView() {
    const gpxUpload = document.getElementById('gpx-upload');
    const gpxMapProvider = document.getElementById('gpx-map-provider');
    const applyMainOffsetBtn = document.getElementById('apply-main-offset');
    
    gpxUpload.addEventListener('change', handleGPXUpload);
    applyMainOffsetBtn.addEventListener('click', applyMainOffset);
    
    // Map provider change handler
    gpxMapProvider.addEventListener('change', (e) => {
        state.gpxMapProvider = e.target.value;
        state.mapProvider = e.target.value; // Sync main map provider
        
        // Update settings map provider selector
        const mapProviderSelect = document.getElementById('map-provider');
        if (mapProviderSelect) {
            mapProviderSelect.value = e.target.value;
        }
        
        // Clear old map
        if (state.gpxMap) {
            if (state.gpxMap.remove) {
                state.gpxMap.remove();
            }
            state.gpxMap = null;
        }
        
        // Also clear photo map since provider changed
        if (state.photoMap) {
            if (state.photoMap.remove) {
                state.photoMap.remove();
            }
            state.photoMap = null;
        }
        
        // Redisplay tracks with new provider if they exist
        if (state.gpxTracks.length > 0) {
            displayGPXTracks();
        }
    });
    
    // Set default provider
    state.gpxMapProvider = 'osm';
}

function initializeGPXMap() {
    const mapElement = document.getElementById('gpx-map');
    
    if (state.gpxMapProvider === 'google') {
        // Google Maps
        state.gpxMap = new google.maps.Map(mapElement, {
            center: { lat: 39.4699, lng: -0.3763 },
            zoom: 10,
            mapTypeId: 'terrain'
        });
    } else {
        // OpenStreetMap or ESRI (Leaflet)
        state.gpxMap = L.map(mapElement).setView([39.4699, -0.3763], 10);
        
        if (state.gpxMapProvider === 'esri') {
            // ESRI World Imagery
            L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
                maxZoom: 19
            }).addTo(state.gpxMap);
        } else {
            // OpenStreetMap
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                maxZoom: 19
            }).addTo(state.gpxMap);
        }
        
        // Always invalidate size when displaying to ensure proper rendering
        state.gpxMap.invalidateSize();
    }
}

async function handleGPXUpload(e) {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    try {
        const response = await fetch('/api/gpx/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        
        if (result.success) {
            // Backend returns all tracks - use as source of truth
            state.gpxTracks = result.tracks;
            displayGPXTracks();
            displayGPXFiles();
            
            // Reload photos to get updated GPX coordinates
            if (state.photos.length > 0) {
                await loadPhotos();
            }
        }
    } catch (error) {
        console.error('Error loading GPX:', error);
        alert('Error loading GPX files.');
    }
    
    // Reset file input to allow re-uploading the same files
    e.target.value = '';
}

function displayGPXTracks() {
    // Initialize map if not already
    if (!state.gpxMap) {
        initializeGPXMap();
    } else {
        // Clear existing polylines/overlays without recreating the map
        if (state.gpxMapProvider === 'google') {
            // For Google Maps, we need to track and remove polylines differently
            // For now, reinitialize
            state.gpxMap = null;
            initializeGPXMap();
        } else {
            // For Leaflet, clear all layers except the tile layer
            state.gpxMap.eachLayer((layer) => {
                if (layer instanceof L.Polyline) {
                    state.gpxMap.removeLayer(layer);
                }
            });
            // Always invalidate size when displaying to ensure proper rendering
            state.gpxMap.invalidateSize();
        }
    }

    if (state.gpxMapProvider === 'google') {
        // Google Maps implementation
        const bounds = new google.maps.LatLngBounds();

        state.gpxTracks.forEach(track => {
            const path = track.points.map(p => ({ lat: p.lat, lng: p.lng }));
            
            const polyline = new google.maps.Polyline({
                path: path,
                geodesic: true,
                strokeColor: '#FF0000',
                strokeOpacity: 0.8,
                strokeWeight: 3,
                map: state.gpxMap
            });

            // Extend bounds
            path.forEach(point => bounds.extend(point));
        });

        // Fit map to bounds
        if (!bounds.isEmpty()) {
            state.gpxMap.fitBounds(bounds);
        }
    } else {
        // OpenStreetMap (Leaflet) implementation
        const bounds = [];

        state.gpxTracks.forEach(track => {
            const latlngs = track.points.map(p => [p.lat, p.lng]);
            
            const polyline = L.polyline(latlngs, {
                color: '#FF0000',
                opacity: 0.8,
                weight: 3
            }).addTo(state.gpxMap);

            // Collect bounds
            latlngs.forEach(latlng => bounds.push(latlng));
        });

        // Fit map to bounds
        if (bounds.length > 0) {
            state.gpxMap.fitBounds(bounds);
        }
        
        // Ensure tiles load properly after bounds adjustment
        state.gpxMap.invalidateSize();
    }

    // Display track info
    displayGPXFiles();
}

function displayGPXFiles() {
    const container = document.getElementById('gpx-files-container');
    container.innerHTML = '';

    if (state.gpxTracks.length === 0) {
        // Container will show "No GPX files loaded" via CSS ::before
        return;
    }

    // Group tracks by filename
    const fileMap = new Map();
    state.gpxTracks.forEach((track, index) => {
        // Extract filename from track name
        const fileName = track.file_name || track.name.split(' - ')[0] || track.name;
        
        if (!fileMap.has(fileName)) {
            fileMap.set(fileName, []);
        }
        fileMap.get(fileName).push(index);
    });

    // Create chip for each file
    fileMap.forEach((trackIndices, fileName) => {
        const chip = document.createElement('div');
        chip.className = 'gpx-file-chip';

        const nameSpan = document.createElement('span');
        nameSpan.className = 'file-name';
        nameSpan.textContent = fileName;

        const pointsSpan = document.createElement('span');
        pointsSpan.className = 'file-points';
        const totalPoints = trackIndices.reduce((sum, idx) => sum + state.gpxTracks[idx].points.length, 0);
        pointsSpan.textContent = `${totalPoints} pts`;

        // Individual offset control
        const offsetControl = document.createElement('div');
        offsetControl.className = 'offset-control';
        
        const offsetInput = document.createElement('input');
        offsetInput.type = 'text';
        offsetInput.className = 'offset-input';
        const trackIndex = trackIndices[0];
        const offsetSeconds = state.gpxTracks[trackIndex].offset_seconds || 0;
        offsetInput.value = formatOffsetSeconds(offsetSeconds);
        offsetInput.placeholder = '±hh:mm:ss';
        offsetInput.title = 'Time offset for this track';
        
        const applyBtn = document.createElement('button');
        applyBtn.className = 'btn-mini';
        applyBtn.textContent = '✓';
        applyBtn.title = 'Apply offset';
        applyBtn.onclick = (e) => {
            e.stopPropagation();
            applyTrackOffset(trackIndices, offsetInput.value);
        };

        offsetControl.appendChild(offsetInput);
        offsetControl.appendChild(applyBtn);

        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-btn';
        removeBtn.textContent = '×';
        removeBtn.title = 'Remove this GPX file';
        removeBtn.onclick = (e) => {
            e.stopPropagation();
            removeGPXFile(trackIndices);
        };

        chip.appendChild(nameSpan);
        chip.appendChild(pointsSpan);
        chip.appendChild(offsetControl);
        chip.appendChild(removeBtn);
        container.appendChild(chip);
    });
}

function formatOffsetSeconds(seconds) {
    const sign = seconds >= 0 ? '+' : '-';
    const abs_seconds = Math.abs(seconds);
    const hours = Math.floor(abs_seconds / 3600);
    const minutes = Math.floor((abs_seconds % 3600) / 60);
    const secs = abs_seconds % 60;
    return `${sign}${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

async function applyMainOffset() {
    const offsetInput = document.getElementById('gpx-main-offset');
    const offset = offsetInput.value;
    
    try {
        const response = await fetch('/api/gpx/set-main-offset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ offset: offset })
        });

        const result = await response.json();
        
        if (result.success) {
            // Update state with backend's track list
            state.gpxTracks = result.tracks;
            // Redraw the display to show updated offsets
            displayGPXFiles();
            
            // Reload photos to get updated GPX coordinates with new offset
            if (state.photos.length > 0) {
                await loadPhotos();
            }
        }
    } catch (error) {
        console.error('Error applying main offset:', error);
        alert('Error applying offset.');
    }
}

async function applyTrackOffset(trackIndices, offset) {
    // Apply to the first track in the group (they're grouped by filename)
    const trackIndex = trackIndices[0];
    
    try {
        const response = await fetch('/api/gpx/set-track-offset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                track_index: trackIndex,
                offset: offset 
            })
        });

        const result = await response.json();
        
        if (result.success) {
            // Update state with backend's track list
            state.gpxTracks = result.tracks;
            // Redraw the display to show updated offsets
            displayGPXFiles();
            
            // Reload photos to get updated GPX coordinates with new offset
            if (state.photos.length > 0) {
                await loadPhotos();
            }
        }
    } catch (error) {
        console.error('Error applying track offset:', error);
        alert('Error applying offset.');
    }
}

async function removeGPXFile(trackIndices) {
    try {
        // Send removal request to backend
        const response = await fetch('/api/gpx/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ indices: trackIndices })
        });

        const result = await response.json();
        
        if (result.success) {
            // Update state with backend's track list (source of truth)
            state.gpxTracks = result.tracks;
            
            // Clear and destroy the existing map properly
            if (state.gpxMap) {
                if (state.gpxMapProvider === 'google') {
                    state.gpxMap = null;
                } else {
                    state.gpxMap.remove();
                    state.gpxMap = null;
                }
            }

            // Always reinitialize the map (empty or with remaining tracks)
            if (state.gpxTracks.length > 0) {
                displayGPXTracks();
            } else {
                initializeGPXMap();
            }

            // Update file chips display
            displayGPXFiles();
            
            // Reload photos to get updated coordinates after GPX removal
            if (state.photos.length > 0) {
                await loadPhotos();
            }
        }
    } catch (error) {
        console.error('Error removing GPX tracks:', error);
        alert('Error removing GPX tracks.');
    }
}

// ==================== Positions View ====================

function initializePositionsView() {
    const positionsUpload = document.getElementById('positions-upload');
    positionsUpload.addEventListener('change', handlePositionsUpload);
    
    // Load existing positions if any
    loadPositions();
}

async function handlePositionsUpload(event) {
    const files = event.target.files;
    if (files.length === 0) return;
    
    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }
    
    try {
        const response = await fetch('/api/positions/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayPositions(result.positions);
        } else {
            alert('Error loading position files.');
        }
    } catch (error) {
        console.error('Error uploading position files:', error);
        alert('Error loading position files.');
    }
    
    // Reset file input
    event.target.value = '';
}

async function loadPositions() {
    try {
        const response = await fetch('/api/positions');
        const result = await response.json();
        
        if (result.success) {
            displayPositions(result.positions, result.by_file);
        }
    } catch (error) {
        console.error('Error loading positions:', error);
    }
}

function displayPositions(positions, byFile = null) {
    const container = document.getElementById('positions-container');
    container.innerHTML = '';
    
    if (!positions || positions.length === 0) {
        return;
    }
    
    // Group by file if not provided
    if (!byFile) {
        byFile = {};
        positions.forEach(pos => {
            const filename = pos.source_file;
            if (!byFile[filename]) {
                byFile[filename] = [];
            }
            byFile[filename].push(pos);
        });
    }
    
    // Create sections for each file
    for (const [filename, filePositions] of Object.entries(byFile)) {
        const fileSection = document.createElement('div');
        fileSection.className = 'position-file-section';
        
        const header = document.createElement('div');
        header.className = 'position-file-header';
        
        const fileInfo = document.createElement('div');
        const fileName = document.createElement('span');
        fileName.className = 'position-file-name';
        fileName.textContent = filename;
        
        const fileCount = document.createElement('span');
        fileCount.className = 'position-file-count';
        fileCount.textContent = ` (${filePositions.length} position${filePositions.length !== 1 ? 's' : ''})`;
        
        fileInfo.appendChild(fileName);
        fileInfo.appendChild(fileCount);
        
        const removeBtn = document.createElement('button');
        removeBtn.className = 'position-file-remove';
        removeBtn.textContent = '🗑️ Remove';
        removeBtn.onclick = () => removePositionFile(filename);
        
        header.appendChild(fileInfo);
        header.appendChild(removeBtn);
        
        const positionList = document.createElement('div');
        positionList.className = 'position-list';
        
        filePositions.forEach(pos => {
            const posItem = document.createElement('div');
            posItem.className = 'position-item';
            
            const posInfo = document.createElement('div');
            const posName = document.createElement('div');
            posName.className = 'position-name';
            posName.textContent = pos.name;
            
            const posCoords = document.createElement('div');
            posCoords.className = 'position-coords';
            let coordsText = `${pos.latitude.toFixed(6)}, ${pos.longitude.toFixed(6)}`;
            if (pos.altitude !== null && pos.altitude !== undefined) {
                coordsText += ` (${pos.altitude.toFixed(1)} m)`;
            }
            posCoords.textContent = coordsText;
            
            posInfo.appendChild(posName);
            posInfo.appendChild(posCoords);
            posItem.appendChild(posInfo);
            
            positionList.appendChild(posItem);
        });
        
        fileSection.appendChild(header);
        fileSection.appendChild(positionList);
        container.appendChild(fileSection);
    }
}

async function removePositionFile(filename) {
    if (!confirm(`Remove all positions from "${filename}"?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/positions/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayPositions(result.positions);
        }
    } catch (error) {
        console.error('Error removing position file:', error);
        alert('Error removing position file.');
    }
}

// ==================== Settings View ====================

function initializeSettingsView() {
    const applyFormatBtn = document.getElementById('apply-format');
    const previewNamesBtn = document.getElementById('preview-names');
    const applyTitleBtn = document.getElementById('apply-title');
    const applyTitleTaggedBtn = document.getElementById('apply-title-tagged');
    const clearTitleBtn = document.getElementById('clear-title');
    const applyTimeOffsetAllBtn = document.getElementById('apply-time-offset-all');
    const applyTimeOffsetTaggedBtn = document.getElementById('apply-time-offset-tagged');
    const applyTimeOffsetNotUpdatedBtn = document.getElementById('apply-time-offset-not-updated');
    const applyTimezoneOffsetAllBtn = document.getElementById('apply-timezone-offset-all');
    const applyTimezoneOffsetTaggedBtn = document.getElementById('apply-timezone-offset-tagged');
    const retrieveLocationAllBtn = document.getElementById('retrieve-location-all');
    const retrieveLocationTaggedBtn = document.getElementById('retrieve-location-tagged');
    const mapProviderSelect = document.getElementById('map-provider');
    const elevationServiceSelect = document.getElementById('elevation-service');
    const exportFolderInput = document.getElementById('export-folder-input');
    const saveExportFolderBtn = document.getElementById('save-export-folder');
    const autoSaveConfigCheckbox = document.getElementById('auto-save-config');
    const saveConfigBtn = document.getElementById('save-config');
    const saveConfigAsBtn = document.getElementById('save-config-as');
    
    applyFormatBtn.addEventListener('click', applyFilenameFormat);
    previewNamesBtn.addEventListener('click', previewFilenameFormat);
    applyTitleBtn.addEventListener('click', applyPhotoTitle);
    applyTitleTaggedBtn.addEventListener('click', applyPhotoTitleTagged);
    clearTitleBtn.addEventListener('click', clearPhotoTitles);
    applyTimeOffsetAllBtn.addEventListener('click', applyTimeOffsetAll);
    applyTimeOffsetTaggedBtn.addEventListener('click', applyTimeOffsetTagged);
    applyTimeOffsetNotUpdatedBtn.addEventListener('click', applyTimeOffsetNotUpdated);
    applyTimezoneOffsetAllBtn.addEventListener('click', applyTimezoneOffsetAll);
    applyTimezoneOffsetTaggedBtn.addEventListener('click', applyTimezoneOffsetTagged);
    retrieveLocationAllBtn.addEventListener('click', retrieveLocationAll);
    retrieveLocationTaggedBtn.addEventListener('click', retrieveLocationTagged);
    
    // Export folder - save on button click
    saveExportFolderBtn.addEventListener('click', async () => {
        await saveSettings();
        alert('Export folder saved successfully!');
    });
    
    // Save settings when changed
    mapProviderSelect.addEventListener('change', saveSettings);
    elevationServiceSelect.addEventListener('change', saveSettings);
    autoSaveConfigCheckbox.addEventListener('change', saveSettings);
    
    // Config file buttons
    saveConfigBtn.addEventListener('click', saveConfigFile);
    saveConfigAsBtn.addEventListener('click', saveConfigFileAs);
    
    // Load current format and config info from backend
    loadFilenameFormat();
    loadConfigInfo();
}

async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        const settings = await response.json();
        
        // Apply settings to UI
        const mapProviderSelect = document.getElementById('map-provider');
        const elevationServiceSelect = document.getElementById('elevation-service');
        const filenameFormat = document.getElementById('filename-format');
        const recursiveCheckbox = document.getElementById('recursive-checkbox');
        const sortSelect = document.getElementById('sort-select');
        const folderPathInput = document.getElementById('folder-path-input');
        const thumbnailSizeSlider = document.getElementById('thumbnail-size');
        const sizeValue = document.getElementById('size-value');
        
        if (mapProviderSelect && settings.map_provider) {
            mapProviderSelect.value = settings.map_provider;
            state.mapProvider = settings.map_provider;
            state.gpxMapProvider = settings.map_provider; // Sync GPX map provider
        }
        
        if (elevationServiceSelect && settings.elevation_service) {
            elevationServiceSelect.value = settings.elevation_service;
        }
        
        if (filenameFormat && settings.filename_format) {
            filenameFormat.value = settings.filename_format;
        }
        
        if (recursiveCheckbox && settings.include_subfolders !== undefined) {
            recursiveCheckbox.checked = settings.include_subfolders;
        }
        
        if (sortSelect && settings.sort_by) {
            sortSelect.value = settings.sort_by;
            state.sortBy = settings.sort_by;
        }
        
        if (folderPathInput && settings.folder_path) {
            folderPathInput.value = settings.folder_path;
        }
        
        const exportFolderInput = document.getElementById('export-folder-input');
        if (exportFolderInput && settings.export_folder) {
            exportFolderInput.value = settings.export_folder;
        }
        
        if (thumbnailSizeSlider && settings.thumbnail_size) {
            thumbnailSizeSlider.value = settings.thumbnail_size;
            state.thumbnailSize = settings.thumbnail_size;
            if (sizeValue) {
                sizeValue.textContent = `${settings.thumbnail_size}px`;
            }
        }
        
        // Auto-save config checkbox
        const autoSaveCheckbox = document.getElementById('auto-save-config');
        if (autoSaveCheckbox && settings.auto_save_config !== undefined) {
            autoSaveCheckbox.checked = settings.auto_save_config;
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

async function saveSettings() {
    try {
        const settings = {
            map_provider: document.getElementById('map-provider').value,
            elevation_service: document.getElementById('elevation-service').value,
            filename_format: document.getElementById('filename-format').value,
            include_subfolders: document.getElementById('recursive-checkbox').checked,
            sort_by: document.getElementById('sort-select').value,
            thumbnail_size: parseInt(document.getElementById('thumbnail-size').value),
            folder_path: document.getElementById('folder-path-input').value,
            export_folder: document.getElementById('export-folder-input').value,
            auto_save_config: document.getElementById('auto-save-config').checked
        };
        
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        
        const result = await response.json();
        
        if (!result.success) {
            console.error('Failed to save settings');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
    }
}

async function loadConfigInfo() {
    try {
        const response = await fetch('/api/config/info');
        const info = await response.json();
        
        const configFilePath = document.getElementById('config-file-path');
        const saveConfigBtn = document.getElementById('save-config');
        
        if (info.has_config_file) {
            configFilePath.textContent = info.config_file_path;
            saveConfigBtn.disabled = false;
        } else {
            configFilePath.textContent = 'None';
            saveConfigBtn.disabled = true;
        }
        
        // Download button is always enabled (doesn't need config file)
    } catch (error) {
        console.error('Error loading config info:', error);
    }
}

async function saveConfigFile() {
    try {
        const response = await fetch('/api/config/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Configuration saved to ${result.file_path}`);
        } else {
            alert(`Failed to save config: ${result.detail}`);
        }
    } catch (error) {
        console.error('Error saving config file:', error);
        alert('Error saving configuration file');
    }
}

async function saveConfigFileAs() {
    try {
        // Trigger download - browser will show its native save dialog
        window.location.href = '/api/config/download';
    } catch (error) {
        console.error('Error downloading config file:', error);
        alert('Error downloading configuration file');
    }
}

async function loadFilenameFormat() {
    try {
        const response = await fetch('/api/filename-format');
        const result = await response.json();
        
        if (result.success) {
            document.getElementById('filename-format').value = result.format;
        }
    } catch (error) {
        console.error('Error loading filename format:', error);
        // Keep default value from HTML if error
    }
}

async function previewFilenameFormat() {
    const format = document.getElementById('filename-format').value.trim();
    
    if (!format) {
        alert('Please enter a filename format.');
        return;
    }
    
    try {
        const response = await fetch('/api/preview-rename', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ format })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayPreviewResults(result.previews);
        } else {
            alert('Error previewing filenames: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error previewing filenames:', error);
        alert('Error previewing filenames: ' + error.message);
    }
}

async function applyFilenameFormat() {
    const format = document.getElementById('filename-format').value.trim();
    
    if (!format) {
        alert('Please enter a filename format.');
        return;
    }
    
    if (!confirm('This will update the new_name column for all photos. Continue?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/apply-rename-format', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ format })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Successfully updated ${result.count} photo names.`);
            // Save the format to settings
            saveSettings();
            // Reload photos if in thumbnails view
            if (state.photos && state.photos.length > 0) {
                await loadPhotos();
            }
        } else {
            alert('Error applying format: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error applying filename format:', error);
        alert('Error applying filename format: ' + error.message);
    }
}

async function applyPhotoTitle() {
    const title = document.getElementById('photo-title').value.trim();
    
    if (!title) {
        alert('Please enter a title.');
        return;
    }
    
    if (!confirm(`This will set the new_title to "${title}" for all photos. Continue?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/apply-photo-title', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Successfully set title for ${result.count} photos.`);
            // Reload photos if in thumbnails view
            if (state.photos && state.photos.length > 0) {
                await loadPhotos();
            }
        } else {
            alert('Error applying title: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error applying title:', error);
        alert('Error applying title: ' + error.message);
    }
}

async function applyPhotoTitleTagged() {
    const title = document.getElementById('photo-title').value.trim();
    
    if (!title) {
        alert('Please enter a title.');
        return;
    }
    
    if (!confirm(`This will set the new_title to "${title}" for tagged photos only. Continue?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/apply-photo-title-tagged', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Successfully set title for ${result.count} tagged photos.`);
            // Reload photos if in thumbnails view
            if (state.photos && state.photos.length > 0) {
                await loadPhotos();
            }
        } else {
            alert('Error applying title: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error applying title to tagged photos:', error);
        alert('Error applying title: ' + error.message);
    }
}

async function clearPhotoTitles() {
    if (!confirm('This will clear the new_title for all photos. Continue?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/clear-photo-titles', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Successfully cleared titles for ${result.count} photos.`);
            document.getElementById('photo-title').value = '';
            // Reload photos if in thumbnails view
            if (state.photos && state.photos.length > 0) {
                await loadPhotos();
            }
        } else {
            alert('Error clearing titles: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error clearing titles:', error);
        alert('Error clearing titles: ' + error.message);
    }
}

async function applyTimeOffsetAll() {
    const offset = document.getElementById('time-offset').value.trim();
    
    if (!offset) {
        alert('Please enter a time offset (e.g., +01:30:00 or -00:15:30).');
        return;
    }
    
    // Validate format: +/-HH:MM:SS
    const regex = /^([+-])(\d{2}):(\d{2}):(\d{2})$/;
    if (!offset.match(regex)) {
        alert('Invalid format. Please use ±HH:MM:SS (e.g., +01:30:00 or -00:15:30).');
        return;
    }
    
    if (!confirm(`This will apply time offset "${offset}" to all photos. Continue?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/apply-time-offset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ offset, mode: 'all' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Successfully applied time offset to ${result.count} photos.`);
            // Reload photos if in thumbnails view
            if (state.photos && state.photos.length > 0) {
                await loadPhotos();
            }
        } else {
            alert('Error applying time offset: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error applying time offset:', error);
        alert('Error applying time offset: ' + error.message);
    }
}

async function applyTimeOffsetTagged() {
    const offset = document.getElementById('time-offset').value.trim();
    
    if (!offset) {
        alert('Please enter a time offset (e.g., +01:30:00 or -00:15:30).');
        return;
    }
    
    // Validate format: +/-HH:MM:SS
    const regex = /^([+-])(\d{2}):(\d{2}):(\d{2})$/;
    if (!offset.match(regex)) {
        alert('Invalid format. Please use ±HH:MM:SS (e.g., +01:30:00 or -00:15:30).');
        return;
    }
    
    if (!confirm(`This will apply time offset "${offset}" to tagged photos only. Continue?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/apply-time-offset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ offset, mode: 'tagged' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Successfully applied time offset to ${result.count} tagged photos.`);
            // Reload photos if in thumbnails view
            if (state.photos && state.photos.length > 0) {
                await loadPhotos();
            }
        } else {
            alert('Error applying time offset: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error applying time offset:', error);
        alert('Error applying time offset: ' + error.message);
    }
}

async function applyTimeOffsetNotUpdated() {
    const offset = document.getElementById('time-offset').value.trim();
    
    if (!offset) {
        alert('Please enter a time offset (e.g., +01:30:00 or -00:15:30).');
        return;
    }
    
    // Validate format: +/-HH:MM:SS
    const regex = /^([+-])(\d{2}):(\d{2}):(\d{2})$/;
    if (!offset.match(regex)) {
        alert('Invalid format. Please use ±HH:MM:SS (e.g., +01:30:00 or -00:15:30).');
        return;
    }
    
    if (!confirm(`This will apply time offset "${offset}" to photos without new_time set. Continue?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/apply-time-offset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ offset, mode: 'not_updated' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Successfully applied time offset to ${result.count} not-updated photos.`);
            // Reload photos if in thumbnails view
            if (state.photos && state.photos.length > 0) {
                await loadPhotos();
            }
        } else {
            alert('Error applying time offset: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error applying time offset:', error);
        alert('Error applying time offset: ' + error.message);
    }
}

async function applyTimezoneOffsetAll() {
    const offset = document.getElementById('timezone-offset').value.trim();
    
    if (!offset) {
        alert('Please enter a timezone offset (e.g., +01:00 or -05:30).');
        return;
    }
    
    // Validate format: +/-HH:MM
    const regex = /^[+-]\d{2}:\d{2}$/;
    if (!offset.match(regex)) {
        alert('Invalid format. Please use ±HH:MM (e.g., +01:00 or -05:30).');
        return;
    }
    
    if (!confirm(`This will set timezone offset "${offset}" for all photos and calculate GPS timestamps. Continue?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/apply-timezone-offset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ offset, mode: 'all' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Successfully applied timezone offset to ${result.count} photos.`);
            // Reload photos if in thumbnails view
            if (state.photos && state.photos.length > 0) {
                await loadPhotos();
            }
        } else {
            alert('Error applying timezone offset: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error applying timezone offset:', error);
        alert('Error applying timezone offset: ' + error.message);
    }
}

async function applyTimezoneOffsetTagged() {
    const offset = document.getElementById('timezone-offset').value.trim();
    
    if (!offset) {
        alert('Please enter a timezone offset (e.g., +01:00 or -05:30).');
        return;
    }
    
    // Validate format: +/-HH:MM
    const regex = /^[+-]\d{2}:\d{2}$/;
    if (!offset.match(regex)) {
        alert('Invalid format. Please use ±HH:MM (e.g., +01:00 or -05:30).');
        return;
    }
    
    if (!confirm(`This will set timezone offset "${offset}" for tagged photos and calculate GPS timestamps. Continue?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/apply-timezone-offset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ offset, mode: 'tagged' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Successfully applied timezone offset to ${result.count} tagged photos.`);
            // Reload photos if in thumbnails view
            if (state.photos && state.photos.length > 0) {
                await loadPhotos();
            }
        } else {
            alert('Error applying timezone offset: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error applying timezone offset:', error);
        alert('Error applying timezone offset: ' + error.message);
    }
}

async function retrieveLocationAll() {
    if (!confirm('This will retrieve location information (City, Sub-location, State, Country) from GPS coordinates for all photos that have valid coordinates. This may take some time for large libraries. Continue?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/retrieve-location', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: 'all' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Successfully retrieved location information for ${result.count} photos.`);
            // Reload photos if in thumbnails view
            if (state.photos && state.photos.length > 0) {
                await loadPhotos();
            }
        } else {
            alert('Error retrieving location information: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error retrieving location:', error);
        alert('Error retrieving location: ' + error.message);
    }
}

async function retrieveLocationTagged() {
    if (!confirm('This will retrieve location information (City, Sub-location, State, Country) from GPS coordinates for tagged photos only. This may take some time. Continue?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/retrieve-location', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: 'tagged' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`Successfully retrieved location information for ${result.count} tagged photos.`);
            // Reload photos if in thumbnails view
            if (state.photos && state.photos.length > 0) {
                await loadPhotos();
            }
        } else {
            alert('Error retrieving location information: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error retrieving location:', error);
        alert('Error retrieving location: ' + error.message);
    }
}

function displayPreviewResults(previews) {
    const previewResults = document.getElementById('preview-results');
    const previewList = document.createElement('div');
    previewList.className = 'preview-list';
    
    previewResults.innerHTML = '<h4>Preview (first 20 photos):</h4>';
    
    previews.forEach(preview => {
        const item = document.createElement('div');
        item.className = 'preview-item';
        
        const oldName = document.createElement('span');
        oldName.className = 'preview-old';
        oldName.textContent = preview.old_name;
        
        const arrow = document.createElement('span');
        arrow.className = 'preview-arrow';
        arrow.textContent = '→';
        
        const newName = document.createElement('span');
        newName.className = 'preview-new';
        newName.textContent = preview.new_name;
        
        item.appendChild(oldName);
        item.appendChild(arrow);
        item.appendChild(newName);
        
        previewList.appendChild(item);
    });
    
    previewResults.appendChild(previewList);
    previewResults.classList.add('active');
}

// ==================== Large Photo View ====================

function initializeLargePhotoView() {
    const modal = document.getElementById('large-photo-modal');
    const closeBtn = modal.querySelector('.close-modal');
    const prevBtn = document.getElementById('prev-photo');
    const nextBtn = document.getElementById('next-photo');
    const tagCheckbox = document.getElementById('large-photo-tag');
    const deleteMarkerBtn = document.getElementById('delete-manual-marker');
    const copyFromPreviousBtn = document.getElementById('copy-from-previous');
    const setManualPositionBtn = document.getElementById('set-manual-position');
    const setPredefinedPositionBtn = document.getElementById('set-predefined-position');
    const editMetadataBtn = document.getElementById('edit-photo-metadata');

    closeBtn.addEventListener('click', closeLargePhotoView);
    prevBtn.addEventListener('click', () => navigatePhoto(-1));
    nextBtn.addEventListener('click', () => navigatePhoto(1));
    
    tagCheckbox.addEventListener('change', () => {
        if (state.selectedPhotoIndex !== null) {
            togglePhotoTag(state.selectedPhotoIndex, tagCheckbox.checked);
        }
    });

    deleteMarkerBtn.addEventListener('click', deleteManualMarker);
    copyFromPreviousBtn.addEventListener('click', copyFromPreviousPhoto);
    setManualPositionBtn.addEventListener('click', setManualPositionManually);
    setPredefinedPositionBtn.addEventListener('click', showPredefinedPositionsModal);
    editMetadataBtn.addEventListener('click', editPhotoMetadata);

    // Event delegation for copy field icons in the photo information table
    const exifInfo = document.getElementById('exif-info');
    exifInfo.addEventListener('click', (e) => {
        const copyIcon = e.target.closest('.copy-field-icon');
        if (copyIcon) {
            const fieldName = copyIcon.dataset.field;
            copyFieldFromPrevious(fieldName);
        }
    });

    // Add click handlers for EXIF and GPX marker labels
    const exifMarkerLabel = document.getElementById('exif-marker-label');
    const gpxMarkerLabel = document.getElementById('gpx-marker-label');
    if (exifMarkerLabel) {
        exifMarkerLabel.addEventListener('click', copyExifToManual);
    }
    if (gpxMarkerLabel) {
        gpxMarkerLabel.addEventListener('click', copyGpxToManual);
    }

    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeLargePhotoView();
        }
    });
}

async function openLargePhotoView(index) {
    state.selectedPhotoIndex = index;
    
    const modal = document.getElementById('large-photo-modal');
    modal.classList.add('active');
    
    await displayLargePhoto(index);
}

function closeLargePhotoView() {
    const modal = document.getElementById('large-photo-modal');
    modal.classList.remove('active');
}

async function displayLargePhoto(index) {
    try {
        // Get the photo from filtered state to access original_index
        const photo = state.filteredPhotos[index];
        const photoIndex = photo.original_index !== undefined ? photo.original_index : index;
        
        // Fetch photo details (includes GPX matching)
        const response = await fetch(`/api/photos/${photoIndex}`);
        const result = await response.json();
        
        if (!result.success) return;
        
        const photoData = result.photo;
        
        // Update image
        const img = document.getElementById('large-photo-img');
        img.src = `/api/photo-image/${photoIndex}?t=${Date.now()}`;
        
        // Update tag checkbox
        const tagCheckbox = document.getElementById('large-photo-tag');
        tagCheckbox.checked = photoData.tagged;
        
        // Update navigation buttons
        document.getElementById('prev-photo').disabled = (index === 0);
        document.getElementById('next-photo').disabled = (index === state.filteredPhotos.length - 1);
        
        // Update copy from previous button (disabled if first photo)
        document.getElementById('copy-from-previous').disabled = (index === 0);
        
        // Set manual position button is always enabled when a photo is displayed
        document.getElementById('set-manual-position').disabled = false;
        
        // Edit metadata button is always enabled when a photo is displayed
        document.getElementById('edit-photo-metadata').disabled = false;
        
        // Set predefined position button is enabled when positions are loaded
        fetch('/api/positions')
            .then(res => res.json())
            .then(result => {
                document.getElementById('set-predefined-position').disabled = !result.success || !result.positions || result.positions.length === 0;
            })
            .catch(() => {
                document.getElementById('set-predefined-position').disabled = true;
            });
        
        // Display EXIF info
        displayEXIFInfo(photoData);
        
        // Display map with markers
        displayPhotoMap(photoData, photoIndex);
        
    } catch (error) {
        console.error('Error displaying photo:', error);
    }
}

function displayEXIFInfo(photo) {
    const exifInfo = document.getElementById('exif-info');
    
    // Format coordinates
    const formatCoords = (lat, lon, alt = null) => {
        if (lat === -360 || lon === -360) return 'N/A';
        const coords = `${lat.toFixed(6)}, ${lon.toFixed(6)}`;
        if (alt !== null && alt !== undefined) {
            return `${coords} (${alt.toFixed(1)} m)`;
        }
        return coords;
    };
    
    // Format date/time to YYYY-MM-DD HH:MM:SS
    const formatDateTime = (dt) => {
        if (!dt || dt === 'N/A') return 'N/A';
        try {
            const date = new Date(dt);
            if (isNaN(date.getTime())) return 'N/A';
            
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            const seconds = String(date.getSeconds()).padStart(2, '0');
            
            return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
        } catch {
            return dt;
        }
    };
    
    // Calculate and format time difference
    const formatTimeDiff = (currentDt, newDt) => {
        if (!currentDt || !newDt || currentDt === 'N/A' || newDt === 'N/A') return '';
        try {
            const currentDate = new Date(currentDt);
            const newDate = new Date(newDt);
            
            if (isNaN(currentDate.getTime()) || isNaN(newDate.getTime())) return '';
            
            // Calculate difference in seconds
            const diffMs = newDate - currentDate;
            const diffSeconds = Math.floor(Math.abs(diffMs) / 1000);
            
            const hours = Math.floor(diffSeconds / 3600);
            const minutes = Math.floor((diffSeconds % 3600) / 60);
            const seconds = diffSeconds % 60;
            
            const sign = diffMs >= 0 ? '+' : '-';
            const hoursStr = String(hours).padStart(2, '0');
            const minutesStr = String(minutes).padStart(2, '0');
            const secondsStr = String(seconds).padStart(2, '0');
            
            return ` (${sign}${hoursStr}:${minutesStr}:${secondsStr})`;
        } catch {
            return '';
        }
    };
    
    // Combine GPS date and time stamps into datetime format
    const formatGPSDateTime = (datestamp, timestamp) => {
        if (!datestamp || !timestamp) return 'N/A';
        try {
            // Convert "YYYY:MM:DD" to "YYYY-MM-DD"
            const date = datestamp.replace(/:/g, '-');
            // Combine with timestamp which is already "HH:MM:SS"
            return `${date} ${timestamp}`;
        } catch {
            return 'N/A';
        }
    };
    
    const rows = [
        {
            label: 'Filename',
            current: photo.filename,
            new: photo.new_name || photo.filename,
            fieldName: null,
            hasCopy: false
        },
        {
            label: 'Image Title',
            current: photo.exif_image_title || 'N/A',
            new: photo.new_title !== null && photo.new_title !== undefined ? (photo.new_title || '(blank)') : 'N/A',
            fieldName: 'title',
            hasCopy: true
        },
        {
            label: 'File Creation Time',
            current: formatDateTime(photo.creation_time),
            new: formatDateTime(photo.creation_time),
            fieldName: null,
            hasCopy: false
        },
        {
            label: 'EXIF Capture Time',
            current: formatDateTime(photo.exif_capture_time),
            new: formatDateTime(photo.new_time) + formatTimeDiff(photo.exif_capture_time, photo.new_time),
            fieldName: 'capture_time',
            hasCopy: true
        },
        {
            label: 'GPS Date/Time Stamp',
            current: formatGPSDateTime(photo.exif_gps_datestamp, photo.exif_gps_timestamp),
            new: formatGPSDateTime(photo.new_gps_datestamp || photo.exif_gps_datestamp, photo.new_gps_timestamp || photo.exif_gps_timestamp),
            fieldName: null,
            hasCopy: false
        },
        {
            label: 'Offset Time',
            current: photo.exif_offset_time || 'N/A',
            new: photo.new_offset_time || (photo.exif_offset_time || 'N/A'),
            fieldName: 'offset_time',
            hasCopy: true
        },
        {
            label: 'City',
            current: photo.exif_city || 'N/A',
            new: photo.new_city || (photo.exif_city || 'N/A'),
            fieldName: 'city',
            hasCopy: true
        },
        {
            label: 'Sub-location',
            current: photo.exif_sublocation || 'N/A',
            new: photo.new_sublocation || (photo.exif_sublocation || 'N/A'),
            fieldName: 'sublocation',
            hasCopy: true
        },
        {
            label: 'State/Province',
            current: photo.exif_state || 'N/A',
            new: photo.new_state || (photo.exif_state || 'N/A'),
            fieldName: 'state',
            hasCopy: true
        },
        {
            label: 'Country',
            current: photo.exif_country || 'N/A',
            new: photo.new_country || (photo.exif_country || 'N/A'),
            fieldName: 'country',
            hasCopy: true
        },
        {
            label: 'EXIF Position',
            current: formatCoords(photo.exif_latitude, photo.exif_longitude, photo.exif_altitude),
            new: formatCoords(photo.final_latitude, photo.final_longitude, photo.final_altitude),
            fieldName: 'position',
            hasCopy: true
        }
    ];

    exifInfo.innerHTML = rows.map(row => `
        <tr>
            <td>${row.label}</td>
            <td>${row.current}</td>
            <td>${row.new}</td>
            <td>${row.hasCopy ? `<span class="copy-field-icon" data-field="${row.fieldName}" title="Copy from previous photo" style="cursor: pointer;">📋</span>` : ''}</td>
        </tr>
    `).join('');
}

function displayPhotoMap(photo, index) {
    const mapElement = document.getElementById('photo-map');
    
    if (state.mapProvider === 'google') {
        displayPhotoMapGoogle(photo, index, mapElement);
    } else {
        displayPhotoMapOSM(photo, index, mapElement);
    }
}

function displayPhotoMapGoogle(photo, index, mapElement) {
    // Store current index in state
    state.currentPhotoIndex = index;
    
    // Initialize map if not already done
    if (!state.photoMap) {
        state.photoMap = new google.maps.Map(mapElement, {
            center: { lat: 39.4699, lng: -0.3763 }, // Valencia
            zoom: 10
        });

        // Add click listener for manual marker placement - use state.currentPhotoIndex
        state.photoMap.addListener('click', (e) => {
            placeManualMarker(e.latLng, state.currentPhotoIndex);
        });
    }

    // Clear existing markers
    Object.values(state.photoMapMarkers).forEach(marker => {
        if (marker && marker.setMap) marker.setMap(null);
    });

    const bounds = new google.maps.LatLngBounds();
    let hasMarkers = false;

    // EXIF marker (red)
    if (photo.exif_latitude !== -360 && photo.exif_longitude !== -360) {
        state.photoMapMarkers.exif = new google.maps.Marker({
            position: { lat: photo.exif_latitude, lng: photo.exif_longitude },
            map: state.photoMap,
            title: 'EXIF Location',
            icon: {
                path: google.maps.SymbolPath.CIRCLE,
                fillColor: '#e74c3c',
                fillOpacity: 1,
                strokeColor: '#fff',
                strokeWeight: 2,
                scale: 8
            }
        });
        bounds.extend(state.photoMapMarkers.exif.getPosition());
        hasMarkers = true;
        
        let exifCoordsText = `${photo.exif_latitude.toFixed(6)}, ${photo.exif_longitude.toFixed(6)}`;
        if (photo.exif_altitude !== null && photo.exif_altitude !== undefined) {
            exifCoordsText += ` (${photo.exif_altitude.toFixed(1)} m)`;
        }
        document.getElementById('exif-coords').textContent = exifCoordsText;
        // Enable clickable class for EXIF marker
        document.getElementById('exif-marker-label').classList.add('clickable-marker');
    } else {
        document.getElementById('exif-coords').textContent = '--';
        // Disable clickable class for EXIF marker
        document.getElementById('exif-marker-label').classList.remove('clickable-marker');
    }

    // GPX marker (blue)
    if (photo.gpx_latitude !== -360 && photo.gpx_longitude !== -360) {
        state.photoMapMarkers.gpx = new google.maps.Marker({
            position: { lat: photo.gpx_latitude, lng: photo.gpx_longitude },
            map: state.photoMap,
            title: 'GPX Matched Location',
            icon: {
                path: google.maps.SymbolPath.CIRCLE,
                fillColor: '#3498db',
                fillOpacity: 1,
                strokeColor: '#fff',
                strokeWeight: 2,
                scale: 8
            }
        });
        bounds.extend(state.photoMapMarkers.gpx.getPosition());
        hasMarkers = true;
        
        let gpxCoordsText = `${photo.gpx_latitude.toFixed(6)}, ${photo.gpx_longitude.toFixed(6)}`;
        if (photo.gpx_altitude !== null && photo.gpx_altitude !== undefined) {
            gpxCoordsText += ` (${photo.gpx_altitude.toFixed(1)} m)`;
        }
        document.getElementById('gpx-coords').textContent = gpxCoordsText;
        // Enable clickable class for GPX marker
        document.getElementById('gpx-marker-label').classList.add('clickable-marker');
    } else {
        document.getElementById('gpx-coords').textContent = '--';
        // Disable clickable class for GPX marker
        document.getElementById('gpx-marker-label').classList.remove('clickable-marker');
    }

    // Manual marker (yellow)
    if (photo.manual_latitude !== -360 && photo.manual_longitude !== -360) {
        state.photoMapMarkers.manual = new google.maps.Marker({
            position: { lat: photo.manual_latitude, lng: photo.manual_longitude },
            map: state.photoMap,
            title: 'Manual Location',
            draggable: true,
            icon: {
                path: google.maps.SymbolPath.CIRCLE,
                fillColor: '#f1c40f',
                fillOpacity: 1,
                strokeColor: '#fff',
                strokeWeight: 2,
                scale: 10
            },
            zIndex: 1000  // On top of final marker
        });
        
        // Update on drag
        state.photoMapMarkers.manual.addListener('dragend', (e) => {
            updateManualLocation(e.latLng, index);
        });
        
        bounds.extend(state.photoMapMarkers.manual.getPosition());
        hasMarkers = true;
        
        let manualCoordsText = `${photo.manual_latitude.toFixed(6)}, ${photo.manual_longitude.toFixed(6)}`;
        if (photo.manual_altitude !== null && photo.manual_altitude !== undefined) {
            manualCoordsText += ` (${photo.manual_altitude.toFixed(1)} m)`;
        }
        document.getElementById('manual-coords').textContent = manualCoordsText;
        document.getElementById('delete-manual-marker').disabled = false;
    } else {
        document.getElementById('manual-coords').textContent = '--';
        document.getElementById('delete-manual-marker').disabled = true;
    }

    // Final marker (green, larger)
    if (photo.final_latitude !== -360 && photo.final_longitude !== -360) {
        state.photoMapMarkers.final = new google.maps.Marker({
            position: { lat: photo.final_latitude, lng: photo.final_longitude },
            map: state.photoMap,
            title: 'Final Location',
            icon: {
                path: google.maps.SymbolPath.CIRCLE,
                fillColor: '#2ecc71',
                fillOpacity: 0.6,  // More transparent
                strokeColor: '#fff',
                strokeWeight: 3,
                scale: 15  // Larger than manual marker (which is 10)
            },
            zIndex: 999  // Below manual marker
        });
        bounds.extend(state.photoMapMarkers.final.getPosition());
        hasMarkers = true;
        
        let finalCoordsText = `${photo.final_latitude.toFixed(6)}, ${photo.final_longitude.toFixed(6)}`;
        if (photo.final_altitude !== null && photo.final_altitude !== undefined) {
            finalCoordsText += ` (${photo.final_altitude.toFixed(1)} m)`;
        }
        document.getElementById('final-coords').textContent = finalCoordsText;
    } else {
        document.getElementById('final-coords').textContent = '--';
    }

    // Center map on markers without changing zoom (only on first load)
    if (hasMarkers) {
        // Pan to center of bounds without zooming
        state.photoMap.panTo(bounds.getCenter());
    } else if (!state.photoMap.getZoom() || state.photoMap.getZoom() === 0) {
        // Only set default view if map hasn't been initialized
        state.photoMap.setCenter({ lat: 39.4699, lng: -0.3763 });
        state.photoMap.setZoom(10);
    }
}

function displayPhotoMapOSM(photo, index, mapElement) {
    // Store current index in state
    state.currentPhotoIndex = index;
    
    // Initialize map if not already done
    if (!state.photoMap) {
        state.photoMap = L.map(mapElement).setView([39.4699, -0.3763], 10);
        
        // Add tile layer based on provider
        if (state.mapProvider === 'esri') {
            // ESRI World Imagery
            L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
                maxZoom: 19
            }).addTo(state.photoMap);
        } else {
            // OpenStreetMap
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                maxZoom: 19
            }).addTo(state.photoMap);
        }
        
        // Add click listener for manual marker placement - use state.currentPhotoIndex
        state.photoMap.on('click', (e) => {
            placeManualMarker(e.latlng, state.currentPhotoIndex);
        });
    }
    
    // Always invalidate size when displaying to ensure proper rendering
    state.photoMap.invalidateSize();

    // Clear existing markers
    Object.values(state.photoMapMarkers).forEach(marker => {
        if (marker && marker.remove) marker.remove();
    });

    const bounds = [];

    // EXIF marker (red)
    if (photo.exif_latitude !== -360 && photo.exif_longitude !== -360) {
        state.photoMapMarkers.exif = L.circleMarker(
            [photo.exif_latitude, photo.exif_longitude],
            {
                radius: 8,
                fillColor: '#e74c3c',
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 1
            }
        ).bindTooltip('EXIF Location').addTo(state.photoMap);
        
        bounds.push([photo.exif_latitude, photo.exif_longitude]);
        
        let exifCoordsText = `${photo.exif_latitude.toFixed(6)}, ${photo.exif_longitude.toFixed(6)}`;
        if (photo.exif_altitude !== null && photo.exif_altitude !== undefined) {
            exifCoordsText += ` (${photo.exif_altitude.toFixed(1)} m)`;
        }
        document.getElementById('exif-coords').textContent = exifCoordsText;
        // Enable clickable class for EXIF marker
        document.getElementById('exif-marker-label').classList.add('clickable-marker');
    } else {
        document.getElementById('exif-coords').textContent = '--';
        // Disable clickable class for EXIF marker
        document.getElementById('exif-marker-label').classList.remove('clickable-marker');
    }

    // GPX marker (blue)
    if (photo.gpx_latitude !== -360 && photo.gpx_longitude !== -360) {
        state.photoMapMarkers.gpx = L.circleMarker(
            [photo.gpx_latitude, photo.gpx_longitude],
            {
                radius: 8,
                fillColor: '#3498db',
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 1
            }
        ).bindTooltip('GPX Matched Location').addTo(state.photoMap);
        
        bounds.push([photo.gpx_latitude, photo.gpx_longitude]);
        
        let gpxCoordsText = `${photo.gpx_latitude.toFixed(6)}, ${photo.gpx_longitude.toFixed(6)}`;
        if (photo.gpx_altitude !== null && photo.gpx_altitude !== undefined) {
            gpxCoordsText += ` (${photo.gpx_altitude.toFixed(1)} m)`;
        }
        document.getElementById('gpx-coords').textContent = gpxCoordsText;
        // Enable clickable class for GPX marker
        document.getElementById('gpx-marker-label').classList.add('clickable-marker');
    } else {
        document.getElementById('gpx-coords').textContent = '--';
        // Disable clickable class for GPX marker
        document.getElementById('gpx-marker-label').classList.remove('clickable-marker');
    }

    // Manual marker (yellow, draggable)
    if (photo.manual_latitude !== -360 && photo.manual_longitude !== -360) {
        state.photoMapMarkers.manual = L.marker(
            [photo.manual_latitude, photo.manual_longitude],
            {
                draggable: true,
                icon: L.divIcon({
                    className: 'manual-marker',
                    html: '<div style="background-color: #f1c40f; width: 20px; height: 20px; border-radius: 50%; border: 2px solid #fff;"></div>',
                    iconSize: [20, 20],
                    iconAnchor: [10, 10]
                })
            }
        ).bindTooltip('Manual Location').addTo(state.photoMap);
        
        // Update on drag
        state.photoMapMarkers.manual.on('dragend', (e) => {
            updateManualLocation(e.target.getLatLng(), index);
        });
        
        bounds.push([photo.manual_latitude, photo.manual_longitude]);
        
        let manualCoordsText = `${photo.manual_latitude.toFixed(6)}, ${photo.manual_longitude.toFixed(6)}`;
        if (photo.manual_altitude !== null && photo.manual_altitude !== undefined) {
            manualCoordsText += ` (${photo.manual_altitude.toFixed(1)} m)`;
        }
        document.getElementById('manual-coords').textContent = manualCoordsText;
        document.getElementById('delete-manual-marker').disabled = false;
    } else {
        document.getElementById('manual-coords').textContent = '--';
        document.getElementById('delete-manual-marker').disabled = true;
    }

    // Final marker (green, larger)
    if (photo.final_latitude !== -360 && photo.final_longitude !== -360) {
        state.photoMapMarkers.final = L.circleMarker(
            [photo.final_latitude, photo.final_longitude],
            {
                radius: 15,  // Larger than manual marker
                fillColor: '#2ecc71',
                color: '#fff',
                weight: 3,
                opacity: 1,
                fillOpacity: 0.6,  // More transparent to show manual marker on top
                pane: 'markerPane'  // Ensure it's in the right pane
            }
        ).bindTooltip('Final Location').addTo(state.photoMap);
        
        bounds.push([photo.final_latitude, photo.final_longitude]);
        
        let finalCoordsText = `${photo.final_latitude.toFixed(6)}, ${photo.final_longitude.toFixed(6)}`;
        if (photo.final_altitude !== null && photo.final_altitude !== undefined) {
            finalCoordsText += ` (${photo.final_altitude.toFixed(1)} m)`;
        }
        document.getElementById('final-coords').textContent = finalCoordsText;
    } else {
        document.getElementById('final-coords').textContent = '--';
    }

    // Center map on markers without changing zoom (only on first load)
    if (bounds.length > 0) {
        // Calculate center of bounds and pan without zooming
        const latSum = bounds.reduce((sum, b) => sum + b[0], 0);
        const lngSum = bounds.reduce((sum, b) => sum + b[1], 0);
        const center = [latSum / bounds.length, lngSum / bounds.length];
        state.photoMap.panTo(center);
    } else if (!state.photoMap.getZoom() || state.photoMap.getZoom() === 0) {
        // Only set default view if map hasn't been initialized
        state.photoMap.setView([39.4699, -0.3763], 10);
    }
}

async function fetchElevation(lat, lng) {
    try {
        const elevationService = document.getElementById('elevation-service').value;
        
        // Skip elevation fetching if service is set to "none"
        if (elevationService === 'none') {
            return null;
        }
        
        const response = await fetch('/api/elevation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                latitude: lat,
                longitude: lng,
                service: elevationService
            })
        });
        
        const result = await response.json();
        
        if (result.success && result.elevation !== null) {
            return result.elevation;
        }
        
        return null;
    } catch (error) {
        console.error('Error fetching elevation:', error);
        return null;
    }
}

async function placeManualMarker(latLng, index, altitude = null) {
    // Handle both Google Maps and Leaflet LatLng objects
    const lat = latLng.lat !== undefined ? (typeof latLng.lat === 'function' ? latLng.lat() : latLng.lat) : latLng.latitude;
    const lng = latLng.lng !== undefined ? (typeof latLng.lng === 'function' ? latLng.lng() : latLng.lng) : latLng.longitude;
    
    // Fetch elevation if not provided
    if (altitude === null) {
        altitude = await fetchElevation(lat, lng);
    }
    
    // Update manual location and wait for backend response
    await updateManualLocation(latLng, index, altitude);
    
    // After updating, refresh the map display with the updated photo data from state
    // The updateManualLocation has already updated state.photos[index] with backend response
    if (state.photos[index]) {
        displayPhotoMap(state.photos[index], index);
    }
}

function updateFinalMarkerGoogle(photo) {
    // Remove old final marker
    if (state.photoMapMarkers.final && state.photoMapMarkers.final.setMap) {
        state.photoMapMarkers.final.setMap(null);
    }
    
    // Add final marker if coordinates are valid
    if (photo && photo.final_latitude !== -360 && photo.final_longitude !== -360) {
        state.photoMapMarkers.final = new google.maps.Marker({
            position: { lat: photo.final_latitude, lng: photo.final_longitude },
            map: state.photoMap,
            title: 'Final Location',
            icon: {
                path: google.maps.SymbolPath.CIRCLE,
                fillColor: '#2ecc71',
                fillOpacity: 0.8,
                strokeColor: '#fff',
                strokeWeight: 2,
                scale: 12
            },
            zIndex: 1000
        });
    }
}

function updateFinalMarkerOSM(photo) {
    // Remove old final marker
    if (state.photoMapMarkers.final && state.photoMapMarkers.final.remove) {
        state.photoMapMarkers.final.remove();
    }
    
    // Add final marker if coordinates are valid
    if (photo && photo.final_latitude !== -360 && photo.final_longitude !== -360) {
        state.photoMapMarkers.final = L.circleMarker(
            [photo.final_latitude, photo.final_longitude],
            {
                radius: 10,
                fillColor: '#2ecc71',
                fillOpacity: 0.8,
                color: '#fff',
                weight: 2
            }
        ).bindTooltip('Final Location').addTo(state.photoMap);
    }
}

async function updateManualLocation(latLng, index, altitude = null) {
    try {
        // Handle both Google Maps and Leaflet LatLng objects
        const lat = latLng.lat !== undefined ? (typeof latLng.lat === 'function' ? latLng.lat() : latLng.lat) : latLng.latitude;
        const lng = latLng.lng !== undefined ? (typeof latLng.lng === 'function' ? latLng.lng() : latLng.lng) : latLng.longitude;
        
        const requestBody = {
            latitude: lat,
            longitude: lng
        };
        
        // Include altitude if provided
        if (altitude !== null && altitude !== undefined) {
            requestBody.altitude = altitude;
        }
        
        const response = await fetch(`/api/photos/${index}/manual-location`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        const result = await response.json();
        
        // Update local state with complete photo data including final coordinates
        if (result.success && state.photos[index]) {
            Object.assign(state.photos[index], result.photo);
        }
        
        // Refresh the EXIF info table to show updated final position
        if (state.photos[index]) {
            displayEXIFInfo(state.photos[index]);
        }
        
    } catch (error) {
        console.error('Error updating manual location:', error);
    }
}

async function copyFromPreviousPhoto() {
    if (state.selectedPhotoIndex === null || state.selectedPhotoIndex === 0) return;
    
    const previousIndex = state.selectedPhotoIndex - 1;
    const previousPhoto = state.photos[previousIndex];
    
    if (!previousPhoto) return;
    
    // Check if previous photo has manual or final coordinates to copy
    const hasManual = previousPhoto.manual_latitude !== -360 && previousPhoto.manual_longitude !== -360;
    const hasFinal = previousPhoto.final_latitude !== -360 && previousPhoto.final_longitude !== -360;
    
    if (!hasManual && !hasFinal) {
        alert('Previous photo has no position to copy.');
        return;
    }
    
    try {
        // Copy manual coordinates if they exist, otherwise copy final coordinates
        const latToCopy = hasManual ? previousPhoto.manual_latitude : previousPhoto.final_latitude;
        const lngToCopy = hasManual ? previousPhoto.manual_longitude : previousPhoto.final_longitude;
        const altToCopy = hasManual ? previousPhoto.manual_altitude : previousPhoto.final_altitude;
        
        // Set manual marker on current photo using the copied coordinates
        if (state.mapProvider === 'google') {
            const latLng = new google.maps.LatLng(latToCopy, lngToCopy);
            await placeManualMarker(latLng, state.selectedPhotoIndex, altToCopy);
        } else {
            const latLng = { lat: latToCopy, lng: lngToCopy };
            await placeManualMarker(latLng, state.selectedPhotoIndex, altToCopy);
        }
    } catch (error) {
        console.error('Error copying from previous photo:', error);
    }
}

async function copyFieldFromPrevious(fieldName) {
    if (state.selectedPhotoIndex === null || state.selectedPhotoIndex === 0) {
        alert('Cannot copy from previous photo for the first photo.');
        return;
    }
    
    const previousIndex = state.selectedPhotoIndex - 1;
    const previousPhoto = state.photos[previousIndex];
    const currentPhoto = state.photos[state.selectedPhotoIndex];
    
    if (!previousPhoto || !currentPhoto) return;
    
    // Determine what value to copy based on field name
    let valueToCopy = null;
    let updateData = {};
    
    switch (fieldName) {
        case 'title':
            valueToCopy = previousPhoto.new_title !== null && previousPhoto.new_title !== undefined 
                ? previousPhoto.new_title 
                : previousPhoto.exif_image_title;
            updateData.new_title = valueToCopy || '';
            break;
            
        case 'capture_time':
            valueToCopy = previousPhoto.new_time || previousPhoto.exif_capture_time;
            if (!valueToCopy || valueToCopy === 'N/A') {
                alert('Previous photo has no capture time to copy.');
                return;
            }
            // Format datetime to YYYY-MM-DD HH:MM:SS
            try {
                const date = new Date(valueToCopy);
                if (isNaN(date.getTime())) {
                    alert('Invalid datetime format in previous photo.');
                    return;
                }
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                const hours = String(date.getHours()).padStart(2, '0');
                const minutes = String(date.getMinutes()).padStart(2, '0');
                const seconds = String(date.getSeconds()).padStart(2, '0');
                updateData.new_time = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
            } catch (error) {
                alert('Error formatting datetime from previous photo.');
                return;
            }
            break;
            
        case 'offset_time':
            valueToCopy = previousPhoto.new_offset_time || previousPhoto.exif_offset_time;
            updateData.new_offset_time = valueToCopy || '';
            break;
            
        case 'city':
            valueToCopy = previousPhoto.new_city || previousPhoto.exif_city;
            updateData.new_city = valueToCopy || '';
            break;
            
        case 'sublocation':
            valueToCopy = previousPhoto.new_sublocation || previousPhoto.exif_sublocation;
            updateData.new_sublocation = valueToCopy || '';
            break;
            
        case 'state':
            valueToCopy = previousPhoto.new_state || previousPhoto.exif_state;
            updateData.new_state = valueToCopy || '';
            break;
            
        case 'country':
            valueToCopy = previousPhoto.new_country || previousPhoto.exif_country;
            updateData.new_country = valueToCopy || '';
            break;
            
        case 'position':
            // Use the existing copyFromPreviousPhoto function for position
            await copyFromPreviousPhoto();
            return;
            
        default:
            console.error('Unknown field name:', fieldName);
            return;
    }
    
    try {
        const response = await fetch(`/api/photos/${state.selectedPhotoIndex}/metadata`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Update the photo in state
            Object.keys(updateData).forEach(key => {
                currentPhoto[key] = updateData[key] || null;
            });
            
            // If we updated capture time, also update GPS stamps
            if (updateData.new_time) {
                currentPhoto.new_gps_datestamp = result.photo?.new_gps_datestamp || null;
                currentPhoto.new_gps_timestamp = result.photo?.new_gps_timestamp || null;
            }
            
            // Refresh the display
            await displayLargePhoto(state.selectedPhotoIndex);
        } else {
            alert('Error copying field: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error copying field:', error);
        alert('Error copying field: ' + error.message);
    }
}

async function setManualPositionManually() {
    if (state.selectedPhotoIndex === null) return;
    
    const input = prompt('Enter position as: latitude, longitude (altitude)\nAltitude is optional.\n\nExample: 43.4452, -2.7840 (125)');
    
    if (!input) return; // User cancelled
    
    // Parse input - handle both formats: "lat, lng" and "lat, lng (alt)"
    const regex = /^\s*([-+]?\d+\.?\d*)\s*,\s*([-+]?\d+\.?\d*)\s*(?:\(\s*([-+]?\d+\.?\d*)\s*\))?\s*$/;
    const match = input.match(regex);
    
    if (!match) {
        alert('Invalid format. Please use: latitude, longitude (altitude)\nExample: 43.4452, -2.7840 (125)');
        return;
    }
    
    const lat = parseFloat(match[1]);
    const lng = parseFloat(match[2]);
    const alt = match[3] ? parseFloat(match[3]) : null;
    
    // Validate coordinates
    if (lat < -90 || lat > 90) {
        alert('Latitude must be between -90 and 90');
        return;
    }
    
    if (lng < -180 || lng > 180) {
        alert('Longitude must be between -180 and 180');
        return;
    }
    
    try {
        // Place manual marker with parsed coordinates
        if (state.mapProvider === 'google') {
            const latLng = new google.maps.LatLng(lat, lng);
            await placeManualMarker(latLng, state.selectedPhotoIndex, alt);
        } else {
            const latLng = { lat: lat, lng: lng };
            await placeManualMarker(latLng, state.selectedPhotoIndex, alt);
        }
    } catch (error) {
        console.error('Error setting manual position:', error);
        alert('Error setting position: ' + error.message);
    }
}

async function copyExifToManual() {
    if (state.selectedPhotoIndex === null) return;
    
    const photo = state.photos[state.selectedPhotoIndex];
    
    // Check if EXIF coordinates exist
    if (!photo || photo.exif_latitude === -360 || photo.exif_longitude === -360) {
        alert('No EXIF coordinates available for this photo.');
        return;
    }
    
    try {
        // Create latLng object and call placeManualMarker with EXIF coordinates and altitude
        const latLng = { lat: photo.exif_latitude, lng: photo.exif_longitude };
        const altitude = photo.exif_altitude !== null && photo.exif_altitude !== undefined ? photo.exif_altitude : null;
        
        await placeManualMarker(latLng, state.selectedPhotoIndex, altitude);
        
    } catch (error) {
        console.error('Error copying EXIF position to manual:', error);
        alert('Error copying EXIF position: ' + error.message);
    }
}

async function copyGpxToManual() {
    if (state.selectedPhotoIndex === null) return;
    
    const photo = state.photos[state.selectedPhotoIndex];
    
    // Check if GPX coordinates exist
    if (!photo || photo.gpx_latitude === -360 || photo.gpx_longitude === -360) {
        alert('No GPX coordinates available for this photo.');
        return;
    }
    
    try {
        // Create latLng object and call placeManualMarker with GPX coordinates and altitude
        const latLng = { lat: photo.gpx_latitude, lng: photo.gpx_longitude };
        const altitude = photo.gpx_altitude !== null && photo.gpx_altitude !== undefined ? photo.gpx_altitude : null;
        
        await placeManualMarker(latLng, state.selectedPhotoIndex, altitude);
        
    } catch (error) {
        console.error('Error copying GPX position to manual:', error);
        alert('Error copying GPX position: ' + error.message);
    }
}

async function showPredefinedPositionsModal() {
    if (state.selectedPhotoIndex === null) return;
    
    try {
        // Fetch available positions
        const response = await fetch('/api/positions');
        const result = await response.json();
        
        if (!result.success || !result.positions || result.positions.length === 0) {
            alert('No predefined positions available. Load YAML files from the Positions View first.');
            return;
        }
        
        // Show modal
        const modal = document.getElementById('positions-modal');
        const positionsList = document.getElementById('positions-list');
        const closeBtn = document.getElementById('close-positions-modal');
        
        // Clear previous content
        positionsList.innerHTML = '';
        
        // Create position items
        result.positions.forEach((pos, index) => {
            const item = document.createElement('div');
            item.className = 'position-selection-item';
            
            const name = document.createElement('div');
            name.className = 'position-name';
            name.textContent = pos.name;
            
            const coords = document.createElement('div');
            coords.className = 'position-coords';
            let coordsText = `${pos.latitude.toFixed(6)}, ${pos.longitude.toFixed(6)}`;
            if (pos.altitude !== null && pos.altitude !== undefined) {
                coordsText += ` (${pos.altitude.toFixed(1)} m)`;
            }
            coords.textContent = coordsText;
            
            const source = document.createElement('div');
            source.className = 'position-source';
            source.textContent = `from ${pos.source_file}`;
            
            item.appendChild(name);
            item.appendChild(coords);
            item.appendChild(source);
            
            // Click handler
            item.addEventListener('click', async () => {
                modal.classList.remove('active');
                
                // Place manual marker with selected position
                if (state.mapProvider === 'google') {
                    const latLng = new google.maps.LatLng(pos.latitude, pos.longitude);
                    await placeManualMarker(latLng, state.selectedPhotoIndex, pos.altitude);
                } else {
                    const latLng = { lat: pos.latitude, lng: pos.longitude };
                    await placeManualMarker(latLng, state.selectedPhotoIndex, pos.altitude);
                }
            });
            
            positionsList.appendChild(item);
        });
        
        // Show modal
        modal.classList.add('active');
        
        // Close button handler
        closeBtn.onclick = () => {
            modal.classList.remove('active');
        };
        
        // Close on background click
        modal.onclick = (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        };
    } catch (error) {
        console.error('Error selecting predefined position:', error);
        alert('Error selecting predefined position: ' + error.message);
    }
}

async function deleteManualMarker() {
    if (state.selectedPhotoIndex === null) return;
    
    try {
        const response = await fetch(`/api/photos/${state.selectedPhotoIndex}/manual-location`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        // Update local state with complete photo data including updated final coordinates
        if (result.success && state.photos[state.selectedPhotoIndex]) {
            Object.assign(state.photos[state.selectedPhotoIndex], result.photo);
        }
        
        // Remove manual marker from map without changing view
        if (state.photoMapMarkers.manual) {
            if (state.mapProvider === 'google' && state.photoMapMarkers.manual.setMap) {
                state.photoMapMarkers.manual.setMap(null);
            } else if (state.photoMapMarkers.manual.remove) {
                state.photoMapMarkers.manual.remove();
            }
            state.photoMapMarkers.manual = null;
        }
        
        // Update coordinates display
        document.getElementById('manual-coords').textContent = '--';
        document.getElementById('delete-manual-marker').disabled = true;
        
        // Update final marker and coordinates
        if (state.mapProvider === 'google') {
            updateFinalMarkerGoogle(state.photos[state.selectedPhotoIndex]);
        } else {
            updateFinalMarkerOSM(state.photos[state.selectedPhotoIndex]);
        }
        
        // Update final coordinates display with altitude
        if (result.photo && result.photo.final_latitude !== -360 && result.photo.final_longitude !== -360) {
            let finalCoordsText = `${result.photo.final_latitude.toFixed(6)}, ${result.photo.final_longitude.toFixed(6)}`;
            if (result.photo.final_altitude !== null && result.photo.final_altitude !== undefined) {
                finalCoordsText += ` (${result.photo.final_altitude.toFixed(1)} m)`;
            }
            document.getElementById('final-coords').textContent = finalCoordsText;
        } else {
            document.getElementById('final-coords').textContent = '--';
        }
        
        // Update GPX coordinates display with altitude (in case it wasn't showing before)
        if (result.photo && result.photo.gpx_latitude !== -360 && result.photo.gpx_longitude !== -360) {
            let gpxCoordsText = `${result.photo.gpx_latitude.toFixed(6)}, ${result.photo.gpx_longitude.toFixed(6)}`;
            if (result.photo.gpx_altitude !== null && result.photo.gpx_altitude !== undefined) {
                gpxCoordsText += ` (${result.photo.gpx_altitude.toFixed(1)} m)`;
            }
            document.getElementById('gpx-coords').textContent = gpxCoordsText;
        }
        
        // Refresh the EXIF info table to show updated final position
        if (state.photos[state.selectedPhotoIndex]) {
            displayEXIFInfo(state.photos[state.selectedPhotoIndex]);
        }
        
    } catch (error) {
        console.error('Error deleting manual marker:', error);
    }
}

function navigatePhoto(direction) {
    if (state.selectedPhotoIndex === null) return;
    
    const newIndex = state.selectedPhotoIndex + direction;
    
    if (newIndex >= 0 && newIndex < state.photos.length) {
        state.selectedPhotoIndex = newIndex;
        displayLargePhoto(newIndex);
    }
}

async function editPhotoMetadata() {
    if (state.selectedPhotoIndex === null) return;
    
    const photo = state.photos[state.selectedPhotoIndex];
    const photoIndex = photo.original_index !== undefined ? photo.original_index : state.selectedPhotoIndex;
    
    // Format current values for display
    const currentTime = photo.new_time || photo.exif_capture_time;
    const currentTitle = photo.new_title || photo.exif_image_title || '';
    
    // Display current time in YYYY-MM-DD HH:MM:SS format
    let displayTime = '';
    if (currentTime) {
        try {
            const dt = new Date(currentTime);
            const year = dt.getFullYear();
            const month = String(dt.getMonth() + 1).padStart(2, '0');
            const day = String(dt.getDate()).padStart(2, '0');
            const hours = String(dt.getHours()).padStart(2, '0');
            const minutes = String(dt.getMinutes()).padStart(2, '0');
            const seconds = String(dt.getSeconds()).padStart(2, '0');
            displayTime = `Current: ${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
        } catch (e) {
            console.error('Error formatting display time:', e);
        }
    }
    
    // Format datetime for input (YYYY-MM-DD HH:MM:SS format)
    let formattedTime = '';
    if (currentTime) {
        try {
            const dt = new Date(currentTime);
            // Format as YYYY-MM-DD HH:MM:SS
            formattedTime = dt.getFullYear() + '-' + 
                String(dt.getMonth() + 1).padStart(2, '0') + '-' +
                String(dt.getDate()).padStart(2, '0') + ' ' +
                String(dt.getHours()).padStart(2, '0') + ':' +
                String(dt.getMinutes()).padStart(2, '0') + ':' +
                String(dt.getSeconds()).padStart(2, '0');
        } catch (e) {
            console.error('Error formatting time:', e);
        }
    }
    
    // Format current offset time
    const currentOffset = photo.new_offset_time || photo.exif_offset_time || '';
    const displayOffset = currentOffset ? `Current: ${currentOffset}` : '';
    
    // Format current location fields
    const currentCity = photo.new_city || photo.exif_city || '';
    const currentSublocation = photo.new_sublocation || photo.exif_sublocation || '';
    const currentState = photo.new_state || photo.exif_state || '';
    const currentCountry = photo.new_country || photo.exif_country || '';
    const displayCity = (photo.exif_city || photo.new_city) ? `Current: ${photo.new_city || photo.exif_city}` : '';
    const displaySublocation = (photo.exif_sublocation || photo.new_sublocation) ? `Current: ${photo.new_sublocation || photo.exif_sublocation}` : '';
    const displayState = (photo.exif_state || photo.new_state) ? `Current: ${photo.new_state || photo.exif_state}` : '';
    const displayCountry = (photo.exif_country || photo.new_country) ? `Current: ${photo.new_country || photo.exif_country}` : '';
    
    // Set values in modal
    document.getElementById('current-time-display').textContent = displayTime;
    document.getElementById('current-offset-display').textContent = displayOffset;
    document.getElementById('current-city-display').textContent = displayCity;
    document.getElementById('current-sublocation-display').textContent = displaySublocation;
    document.getElementById('current-state-display').textContent = displayState;
    document.getElementById('current-country-display').textContent = displayCountry;
    document.getElementById('edit-photo-title-input').value = currentTitle;
    document.getElementById('edit-photo-time-input').value = formattedTime;
    document.getElementById('edit-offset-time-input').value = currentOffset;
    document.getElementById('edit-city-input').value = currentCity;
    document.getElementById('edit-sublocation-input').value = currentSublocation;
    document.getElementById('edit-state-input').value = currentState;
    document.getElementById('edit-country-input').value = currentCountry;
    
    // Store current photo index for later use
    state.editingPhotoIndex = photoIndex;
    state.editingOriginalTitle = currentTitle;
    state.editingOriginalTime = currentTime;
    state.editingOriginalOffset = currentOffset;
    state.editingOriginalCity = currentCity;
    state.editingOriginalSublocation = currentSublocation;
    state.editingOriginalState = currentState;
    state.editingOriginalCountry = currentCountry;
    
    // Show modal
    const modal = document.getElementById('edit-metadata-modal');
    modal.classList.add('active');
}

function initializeEditMetadataModal() {
    const modal = document.getElementById('edit-metadata-modal');
    const closeBtn = document.getElementById('close-edit-metadata-modal');
    const closeModalBtn = document.getElementById('close-metadata-modal-btn');
    const applyTitleBtn = document.getElementById('apply-title-btn');
    const applyTimeBtn = document.getElementById('apply-time-btn');
    const applyOffsetBtn = document.getElementById('apply-offset-btn');
    const retrieveLocationBtn = document.getElementById('retrieve-location-btn');
    const applyLocationBtn = document.getElementById('apply-location-btn');
    
    closeBtn.addEventListener('click', () => {
        modal.classList.remove('active');
    });
    
    closeModalBtn.addEventListener('click', () => {
        modal.classList.remove('active');
    });
    
    applyTitleBtn.addEventListener('click', async () => {
        await applyTitleChange();
    });
    
    applyTimeBtn.addEventListener('click', async () => {
        await applyTimeChange();
    });
    
    applyOffsetBtn.addEventListener('click', async () => {
        await applyOffsetChange();
    });
    
    retrieveLocationBtn.addEventListener('click', async () => {
        await retrieveSinglePhotoLocation();
    });
    
    applyLocationBtn.addEventListener('click', async () => {
        await applyLocationChanges();
    });
    
    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
}

async function applyTitleChange() {
    const newTitle = document.getElementById('edit-photo-title-input').value;
    
    // Only update if changed
    if (newTitle === state.editingOriginalTitle) {
        return;
    }
    
    try {
        const response = await fetch(`/api/photos/${state.editingPhotoIndex}/metadata`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_title: newTitle })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Title updated successfully!');
            state.editingOriginalTitle = newTitle;
            
            // Update the photo in state directly
            if (state.photos[state.selectedPhotoIndex]) {
                state.photos[state.selectedPhotoIndex].new_title = newTitle || null;
            }
            
            // Refresh the display
            await displayLargePhoto(state.selectedPhotoIndex);
        } else {
            alert('Error updating title: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error updating title:', error);
        alert('Error updating title: ' + error.message);
    }
}

async function applyTimeChange() {
    const newTimeValue = document.getElementById('edit-photo-time-input').value.trim();
    
    // Format original time for comparison (YYYY-MM-DD HH:MM:SS)
    let originalTimeFormatted = '';
    if (state.editingOriginalTime) {
        const dt = new Date(state.editingOriginalTime);
        originalTimeFormatted = dt.getFullYear() + '-' + 
            String(dt.getMonth() + 1).padStart(2, '0') + '-' +
            String(dt.getDate()).padStart(2, '0') + ' ' +
            String(dt.getHours()).padStart(2, '0') + ':' +
            String(dt.getMinutes()).padStart(2, '0') + ':' +
            String(dt.getSeconds()).padStart(2, '0');
    }
    
    // Only update if changed
    if (newTimeValue === originalTimeFormatted) {
        return;
    }
    
    let updateData = {};
    
    if (newTimeValue === '') {
        updateData.new_time = '';  // Clear time
    } else {
        // Parse YYYY-MM-DD HH:MM:SS format
        const regex = /^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})$/;
        const match = newTimeValue.match(regex);
        
        if (!match) {
            alert('Invalid time format. Please use: YYYY-MM-DD HH:MM:SS\\nExample: 2026-01-21 23:24:50');
            return;
        }
        
        const [_, year, month, day, hours, minutes, seconds] = match;
        const dt = new Date(year, month - 1, day, hours, minutes, seconds);
        
        if (isNaN(dt.getTime())) {
            alert('Invalid date/time values');
            return;
        }
        
        // Send in YYYY-MM-DD HH:MM:SS format (not ISO)
        updateData.new_time = newTimeValue;
    }
    
    try {
        const response = await fetch(`/api/photos/${state.editingPhotoIndex}/metadata`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Time updated successfully!');
            state.editingOriginalTime = updateData.new_time ? new Date(updateData.new_time).toISOString() : null;
            
            // Update the photo in state directly
            if (state.photos[state.selectedPhotoIndex]) {
                state.photos[state.selectedPhotoIndex].new_time = updateData.new_time || null;
            }
            
            // Refresh the display
            await displayLargePhoto(state.selectedPhotoIndex);
        } else {
            alert('Error updating time: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error updating time:', error);
        alert('Error updating time: ' + error.message);
    }
}

async function applyOffsetChange() {
    const newOffsetValue = document.getElementById('edit-offset-time-input').value.trim();
    
    // Only update if changed
    if (newOffsetValue === state.editingOriginalOffset) {
        return;
    }
    
    let updateData = {};
    
    if (newOffsetValue === '') {
        updateData.new_offset_time = '';  // Clear offset
    } else {
        // Validate offset format: +HH:MM or -HH:MM
        const regex = /^[+-]\d{2}:\d{2}$/;
        
        if (!regex.test(newOffsetValue)) {
            alert('Invalid offset format. Please use: +HH:MM or -HH:MM\\nExample: +02:00, -05:00');
            return;
        }
        
        updateData.new_offset_time = newOffsetValue;
    }
    
    try {
        const response = await fetch(`/api/photos/${state.editingPhotoIndex}/metadata`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Offset time updated successfully!');
            state.editingOriginalOffset = updateData.new_offset_time || '';
            
            // Update the photo in state directly
            if (state.photos[state.selectedPhotoIndex]) {
                state.photos[state.selectedPhotoIndex].new_offset_time = updateData.new_offset_time || null;
            }
            
            // Refresh the display
            await displayLargePhoto(state.selectedPhotoIndex);
        } else {
            alert('Error updating offset time: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error updating offset time:', error);
        alert('Error updating offset time: ' + error.message);
    }
}

async function retrieveSinglePhotoLocation() {
    if (state.editingPhotoIndex === null) return;
    
    try {
        const response = await fetch(`/api/photos/${state.editingPhotoIndex}/retrieve-location`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success && result.location) {
            // Update input fields with retrieved location
            const location = result.location;
            document.getElementById('edit-city-input').value = location.city || '';
            document.getElementById('edit-sublocation-input').value = location.sublocation || '';
            document.getElementById('edit-state-input').value = location.state || '';
            document.getElementById('edit-country-input').value = location.country || '';
            
            alert('Location retrieved successfully!');
        } else {
            alert('Could not retrieve location: ' + (result.detail || 'No valid GPS coordinates or geocoding failed'));
        }
    } catch (error) {
        console.error('Error retrieving location:', error);
        alert('Error retrieving location: ' + error.message);
    }
}

async function applyLocationChanges() {
    const newCity = document.getElementById('edit-city-input').value.trim();
    const newSublocation = document.getElementById('edit-sublocation-input').value.trim();
    const newState = document.getElementById('edit-state-input').value.trim();
    const newCountry = document.getElementById('edit-country-input').value.trim();
    
    // Check if any location field changed
    if (newCity === state.editingOriginalCity &&
        newSublocation === state.editingOriginalSublocation &&
        newState === state.editingOriginalState &&
        newCountry === state.editingOriginalCountry) {
        return;  // No changes
    }
    
    try {
        const response = await fetch(`/api/photos/${state.editingPhotoIndex}/metadata`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                new_city: newCity || '',
                new_sublocation: newSublocation || '',
                new_state: newState || '',
                new_country: newCountry || ''
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Location updated successfully!');
            state.editingOriginalCity = newCity;
            state.editingOriginalSublocation = newSublocation;
            state.editingOriginalState = newState;
            state.editingOriginalCountry = newCountry;
            
            // Update the photo in state
            if (state.photos[state.selectedPhotoIndex]) {
                state.photos[state.selectedPhotoIndex].new_city = newCity || null;
                state.photos[state.selectedPhotoIndex].new_sublocation = newSublocation || null;
                state.photos[state.selectedPhotoIndex].new_state = newState || null;
                state.photos[state.selectedPhotoIndex].new_country = newCountry || null;
            }
            
            // Refresh the display
            await displayLargePhoto(state.selectedPhotoIndex);
        } else {
            alert('Error updating location: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error updating location:', error);
        alert('Error updating location: ' + error.message);
    }
}

// ==================== Keyboard Shortcuts ====================

function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ignore keyboard shortcuts if user is typing in an input/textarea
        const activeElement = document.activeElement;
        const isTyping = activeElement && (
            activeElement.tagName === 'INPUT' || 
            activeElement.tagName === 'TEXTAREA' ||
            activeElement.isContentEditable
        );
        
        // Space - open large photo view (only if not typing)
        if (e.code === 'Space' && state.selectedPhotoIndex !== null && !isTyping) {
            const modal = document.getElementById('large-photo-modal');
            if (!modal.classList.contains('active')) {
                e.preventDefault();
                openLargePhotoView(state.selectedPhotoIndex);
            }
        }
        
        // Escape - close large photo view
        if (e.code === 'Escape') {
            const modal = document.getElementById('large-photo-modal');
            if (modal.classList.contains('active')) {
                closeLargePhotoView();
            }
        }
        
        // Arrow keys in large photo view
        const modal = document.getElementById('large-photo-modal');
        if (modal.classList.contains('active')) {
            if (e.code === 'ArrowLeft') {
                navigatePhoto(-1);
            } else if (e.code === 'ArrowRight') {
                navigatePhoto(1);
            }
        }
    });
}
