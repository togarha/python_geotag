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
    const mapProviderSelect = document.getElementById('map-provider');
    const sortSelect = document.getElementById('sort-select');
    const filterSelect = document.getElementById('filter-select');
    const thumbnailSizeSlider = document.getElementById('thumbnail-size');
    const sizeValue = document.getElementById('size-value');

    // Map provider select
    mapProviderSelect.addEventListener('change', () => {
        state.mapProvider = mapProviderSelect.value;
        // Reset maps so they reinitialize with new provider
        state.photoMap = null;
        state.gpxMap = null;
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
        
        // Update local state
        state.photos[index].tagged = tagged;
        
        // Refresh the displays to show updated tag status
        displayPhotos();
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
        // Reinitialize map with new provider
        if (state.gpxTracks.length > 0) {
            // Clear old map
            const mapContainer = document.getElementById('gpx-map');
            mapContainer.innerHTML = '';
            state.gpxMap = null;
            // Redisplay tracks with new provider
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
        // OpenStreetMap (Leaflet)
        state.gpxMap = L.map(mapElement).setView([39.4699, -0.3763], 10);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }).addTo(state.gpxMap);
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
    // Initialize map if not already, or clear and reinitialize to remove old polylines
    if (!state.gpxMap) {
        initializeGPXMap();
    } else {
        // Clear existing map and reinitialize to remove old polylines
        if (state.gpxMapProvider === 'google') {
            state.gpxMap = null;
        } else {
            state.gpxMap.remove();
            state.gpxMap = null;
        }
        initializeGPXMap();
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

// ==================== Large Photo View ====================

function initializeLargePhotoView() {
    const modal = document.getElementById('large-photo-modal');
    const closeBtn = modal.querySelector('.close-modal');
    const prevBtn = document.getElementById('prev-photo');
    const nextBtn = document.getElementById('next-photo');
    const tagCheckbox = document.getElementById('large-photo-tag');
    const deleteMarkerBtn = document.getElementById('delete-manual-marker');
    const copyFromPreviousBtn = document.getElementById('copy-from-previous');

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
        // Get the photo from state to access original_index
        const photo = state.photos[index];
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
        document.getElementById('next-photo').disabled = (index === state.photos.length - 1);
        
        // Update copy from previous button (disabled if first photo)
        document.getElementById('copy-from-previous').disabled = (index === 0);
        
        // Update copy from previous button (disabled if first photo)
        document.getElementById('copy-from-previous').disabled = (index === 0);
        
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
    
    // Format date/time
    const formatDateTime = (dt) => {
        if (!dt || dt === 'N/A') return 'N/A';
        try {
            const date = new Date(dt);
            return date.toLocaleString();
        } catch {
            return dt;
        }
    };
    
    const rows = [
        {
            label: 'Filename',
            current: photo.filename,
            new: photo.new_name || photo.filename
        },
        {
            label: 'File Creation Time',
            current: formatDateTime(photo.creation_time),
            new: formatDateTime(photo.creation_time)
        },
        {
            label: 'EXIF Capture Time',
            current: formatDateTime(photo.exif_capture_time),
            new: formatDateTime(photo.exif_capture_time)
        },
        {
            label: 'EXIF Position',
            current: formatCoords(photo.exif_latitude, photo.exif_longitude, photo.exif_altitude),
            new: formatCoords(photo.final_latitude, photo.final_longitude, photo.final_altitude)
        }
    ];

    exifInfo.innerHTML = rows.map(row => `
        <tr>
            <td>${row.label}</td>
            <td>${row.current}</td>
            <td>${row.new}</td>
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
        
        let gpxCoordsText = `${photo.gpx_latitude.toFixed(6)}, ${photo.gpx_longitude.toFixed(6)}`;
        if (photo.gpx_altitude !== null && photo.gpx_altitude !== undefined) {
            gpxCoordsText += ` (${photo.gpx_altitude.toFixed(1)} m)`;
        }
        document.getElementById('gpx-coords').textContent = gpxCoordsText;
    } else {
        document.getElementById('gpx-coords').textContent = '--';
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
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }).addTo(state.photoMap);
        
        // Add click listener for manual marker placement - use state.currentPhotoIndex
        state.photoMap.on('click', (e) => {
            placeManualMarker(e.latlng, state.currentPhotoIndex);
        });
    }

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
    } else {
        document.getElementById('exif-coords').textContent = '--';
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
    } else {
        document.getElementById('gpx-coords').textContent = '--';
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
