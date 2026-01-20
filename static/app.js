/**
 * Geotag Application - Main JavaScript
 */

// Global State
const state = {
    currentView: 'thumbnails',
    currentFolder: '',
    photos: [],
    gpxTracks: [],
    selectedPhotoIndex: null,
    filterType: 'all',
    sortBy: 'time',
    thumbnailSize: 200,
    gpxMap: null,
    photoMap: null,
    photoMapMarkers: {
        exif: null,
        gpx: null,
        manual: null
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeMenu();
    initializeViews();
    initializeThumbnailsView();
    initializeGPXView();
    initializeLargePhotoView();
    initializeKeyboardShortcuts();
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
        
        // Initialize map if switching to GPX view
        if (viewName === 'gpx' && !state.gpxMap) {
            initializeGPXMap();
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
    const sortSelect = document.getElementById('sort-select');
    const filterSelect = document.getElementById('filter-select');
    const thumbnailSizeSlider = document.getElementById('thumbnail-size');
    const sizeValue = document.getElementById('size-value');

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
    });

    // Filter select
    filterSelect.addEventListener('change', () => {
        state.filterType = filterSelect.value;
        loadPhotos();
    });

    // Thumbnail size slider
    thumbnailSizeSlider.addEventListener('input', (e) => {
        state.thumbnailSize = parseInt(e.target.value);
        sizeValue.textContent = `${state.thumbnailSize}px`;
        updateThumbnailSizes();
    });
}

async function scanFolder(folderPath, recursive) {
    try {
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
            
            displayPhotos();
        } else {
            alert('Error scanning folder: ' + result.detail);
        }
    } catch (error) {
        console.error('Error scanning folder:', error);
        alert('Error scanning folder. Make sure the server is running.');
    }
}

async function loadPhotos() {
    try {
        const response = await fetch(`/api/photos?filter_type=${state.filterType}`);
        const result = await response.json();
        
        if (result.success) {
            state.photos = result.data;
            displayPhotos();
        }
    } catch (error) {
        console.error('Error loading photos:', error);
    }
}

function displayPhotos() {
    displayPhotoList();
    displayPhotoGrid();
}

function displayPhotoList() {
    const photoList = document.getElementById('photo-list');
    if (!photoList) {
        console.error('photo-list element not found!');
        return;
    }
    photoList.innerHTML = '';

    state.photos.forEach((photo, index) => {
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

    state.photos.forEach((photo, index) => {
        const item = document.createElement('div');
        item.className = 'photo-grid-item';
        item.dataset.index = index;
        item.style.width = `${state.thumbnailSize}px`;
        item.style.height = `${state.thumbnailSize}px`;

        const img = document.createElement('img');
        // Add timestamp to prevent caching issues when sort order changes
        img.src = `/api/photo-thumbnail/${index}?size=${state.thumbnailSize}&t=${Date.now()}`;
        img.alt = photo.filename;
        img.title = photo.filename; // Tooltip with filename
        img.loading = 'lazy';

        const checkboxOverlay = document.createElement('div');
        checkboxOverlay.className = 'checkbox-overlay';
        
        const label = document.createElement('label');
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = photo.tagged;
        checkbox.addEventListener('change', (e) => {
            e.stopPropagation();
            togglePhotoTag(index, checkbox.checked);
        });
        
        label.appendChild(checkbox);
        label.appendChild(document.createTextNode(' Tag'));
        checkboxOverlay.appendChild(label);

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
        
        // Update local state
        state.photos[index].tagged = tagged;
    } catch (error) {
        console.error('Error toggling tag:', error);
    }
}

// ==================== GPX View ====================

function initializeGPXView() {
    const gpxUpload = document.getElementById('gpx-upload');
    
    gpxUpload.addEventListener('change', handleGPXUpload);
}

function initializeGPXMap() {
    const mapElement = document.getElementById('gpx-map');
    
    // Default center: Valencia, Spain
    state.gpxMap = new google.maps.Map(mapElement, {
        center: { lat: 39.4699, lng: -0.3763 },
        zoom: 10,
        mapTypeId: 'terrain'
    });
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
            state.gpxTracks = result.tracks;
            displayGPXTracks();
            
            const statusEl = document.getElementById('gpx-status');
            statusEl.textContent = `${result.files_loaded} GPX file(s) loaded`;
        }
    } catch (error) {
        console.error('Error loading GPX:', error);
        alert('Error loading GPX files.');
    }
}

function displayGPXTracks() {
    if (!state.gpxMap) {
        initializeGPXMap();
    }

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

    // Display track info
    displayGPXInfo();
}

function displayGPXInfo() {
    const gpxInfo = document.getElementById('gpx-info');
    gpxInfo.innerHTML = '<h3>Loaded Tracks</h3>';

    const list = document.createElement('ul');
    state.gpxTracks.forEach(track => {
        const item = document.createElement('li');
        item.textContent = `${track.name} (${track.points.length} points)`;
        list.appendChild(item);
    });

    gpxInfo.appendChild(list);
}

// ==================== Large Photo View ====================

function initializeLargePhotoView() {
    const modal = document.getElementById('large-photo-modal');
    const closeBtn = modal.querySelector('.close-modal');
    const prevBtn = document.getElementById('prev-photo');
    const nextBtn = document.getElementById('next-photo');
    const tagCheckbox = document.getElementById('large-photo-tag');
    const deleteMarkerBtn = document.getElementById('delete-manual-marker');

    closeBtn.addEventListener('click', closeLargePhotoView);
    prevBtn.addEventListener('click', () => navigatePhoto(-1));
    nextBtn.addEventListener('click', () => navigatePhoto(1));
    
    tagCheckbox.addEventListener('change', () => {
        if (state.selectedPhotoIndex !== null) {
            togglePhotoTag(state.selectedPhotoIndex, tagCheckbox.checked);
        }
    });

    deleteMarkerBtn.addEventListener('click', deleteManualMarker);

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
        // Fetch photo details (includes GPX matching)
        const response = await fetch(`/api/photos/${index}`);
        const result = await response.json();
        
        if (!result.success) return;
        
        const photo = result.photo;
        
        // Update image
        const img = document.getElementById('large-photo-img');
        img.src = `/api/photo-image/${index}`;
        
        // Update tag checkbox
        const tagCheckbox = document.getElementById('large-photo-tag');
        tagCheckbox.checked = photo.tagged;
        
        // Update navigation buttons
        document.getElementById('prev-photo').disabled = (index === 0);
        document.getElementById('next-photo').disabled = (index === state.photos.length - 1);
        
        // Display EXIF info
        displayEXIFInfo(photo);
        
        // Display map with markers
        displayPhotoMap(photo, index);
        
    } catch (error) {
        console.error('Error displaying photo:', error);
    }
}

function displayEXIFInfo(photo) {
    const exifInfo = document.getElementById('exif-info');
    
    const info = [
        { label: 'Filename', value: photo.filename },
        { label: 'Capture Time', value: photo.exif_capture_time || 'N/A' },
        { label: 'EXIF Latitude', value: photo.exif_latitude !== -360 ? photo.exif_latitude.toFixed(6) : 'N/A' },
        { label: 'EXIF Longitude', value: photo.exif_longitude !== -360 ? photo.exif_longitude.toFixed(6) : 'N/A' },
        { label: 'GPX Latitude', value: photo.gpx_latitude !== -360 ? photo.gpx_latitude.toFixed(6) : 'N/A' },
        { label: 'GPX Longitude', value: photo.gpx_longitude !== -360 ? photo.gpx_longitude.toFixed(6) : 'N/A' },
        { label: 'Manual Latitude', value: photo.manual_latitude !== -360 ? photo.manual_latitude.toFixed(6) : 'N/A' },
        { label: 'Manual Longitude', value: photo.manual_longitude !== -360 ? photo.manual_longitude.toFixed(6) : 'N/A' }
    ];

    exifInfo.innerHTML = info.map(item => `
        <div class="exif-info-item">
            <div class="exif-info-label">${item.label}:</div>
            <div class="exif-info-value">${item.value}</div>
        </div>
    `).join('');
}

function displayPhotoMap(photo, index) {
    const mapElement = document.getElementById('photo-map');
    
    // Initialize map if not already done
    if (!state.photoMap) {
        state.photoMap = new google.maps.Map(mapElement, {
            center: { lat: 39.4699, lng: -0.3763 }, // Valencia
            zoom: 10
        });

        // Add click listener for manual marker placement
        state.photoMap.addListener('click', (e) => {
            placeManualMarker(e.latLng, index);
        });
    }

    // Clear existing markers
    Object.values(state.photoMapMarkers).forEach(marker => {
        if (marker) marker.setMap(null);
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
        
        document.getElementById('exif-coords').textContent = 
            `${photo.exif_latitude.toFixed(6)}, ${photo.exif_longitude.toFixed(6)}`;
    } else {
        document.getElementById('exif-coords').textContent = '--';
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
        
        document.getElementById('gpx-coords').textContent = 
            `${photo.gpx_latitude.toFixed(6)}, ${photo.gpx_longitude.toFixed(6)}`;
    } else {
        document.getElementById('gpx-coords').textContent = '--';
    }

    // Manual marker (green)
    if (photo.manual_latitude !== -360 && photo.manual_longitude !== -360) {
        state.photoMapMarkers.manual = new google.maps.Marker({
            position: { lat: photo.manual_latitude, lng: photo.manual_longitude },
            map: state.photoMap,
            title: 'Manual Location',
            draggable: true,
            icon: {
                path: google.maps.SymbolPath.CIRCLE,
                fillColor: '#2ecc71',
                fillOpacity: 1,
                strokeColor: '#fff',
                strokeWeight: 2,
                scale: 10
            }
        });
        
        // Update on drag
        state.photoMapMarkers.manual.addListener('dragend', (e) => {
            updateManualLocation(e.latLng, index);
        });
        
        bounds.extend(state.photoMapMarkers.manual.getPosition());
        hasMarkers = true;
        
        document.getElementById('manual-coords').textContent = 
            `${photo.manual_latitude.toFixed(6)}, ${photo.manual_longitude.toFixed(6)}`;
        document.getElementById('delete-manual-marker').disabled = false;
    } else {
        document.getElementById('manual-coords').textContent = '--';
        document.getElementById('delete-manual-marker').disabled = true;
    }

    // Center map
    if (hasMarkers) {
        state.photoMap.fitBounds(bounds);
    } else if (state.gpxTracks.length > 0) {
        // Center on GPX tracks
        const gpxBounds = new google.maps.LatLngBounds();
        state.gpxTracks.forEach(track => {
            if (track.bounds) {
                gpxBounds.extend({ lat: track.bounds.north, lng: track.bounds.east });
                gpxBounds.extend({ lat: track.bounds.south, lng: track.bounds.west });
            }
        });
        state.photoMap.fitBounds(gpxBounds);
    } else {
        // Default to Valencia
        state.photoMap.setCenter({ lat: 39.4699, lng: -0.3763 });
        state.photoMap.setZoom(10);
    }
}

async function placeManualMarker(latLng, index) {
    await updateManualLocation(latLng, index);
    
    // Refresh the display
    const response = await fetch(`/api/photos/${index}`);
    const result = await response.json();
    if (result.success) {
        displayPhotoMap(result.photo, index);
    }
}

async function updateManualLocation(latLng, index) {
    try {
        await fetch(`/api/photos/${index}/manual-location`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                latitude: latLng.lat(),
                longitude: latLng.lng()
            })
        });
        
        // Update local state
        if (state.photos[index]) {
            state.photos[index].manual_latitude = latLng.lat();
            state.photos[index].manual_longitude = latLng.lng();
        }
        
        // Update coordinates display
        document.getElementById('manual-coords').textContent = 
            `${latLng.lat().toFixed(6)}, ${latLng.lng().toFixed(6)}`;
        document.getElementById('delete-manual-marker').disabled = false;
        
    } catch (error) {
        console.error('Error updating manual location:', error);
    }
}

async function deleteManualMarker() {
    if (state.selectedPhotoIndex === null) return;
    
    try {
        await fetch(`/api/photos/${state.selectedPhotoIndex}/manual-location`, {
            method: 'DELETE'
        });
        
        // Update local state
        if (state.photos[state.selectedPhotoIndex]) {
            state.photos[state.selectedPhotoIndex].manual_latitude = -360;
            state.photos[state.selectedPhotoIndex].manual_longitude = -360;
        }
        
        // Refresh display
        await displayLargePhoto(state.selectedPhotoIndex);
        
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

// ==================== Keyboard Shortcuts ====================

function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Space - open large photo view
        if (e.code === 'Space' && state.selectedPhotoIndex !== null) {
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
