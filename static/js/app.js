// Initialize the Cesium Viewer
Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJjZmQ5ZThlMi05OTZjLTQyNzUtOWE4OS0zMDljMzY3YWMyNjQiLCJpZCI6MjMyNzg2LCJpYXQiOjE3MjI4NzYyNTF9._EaN2cJDoDrXjzQn1G5qUaWtYR--Y-YUM92-H6mYnkQ';
Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJjZmQ5ZThlMi05OTZjLTQyNzUtOWE4OS0zMDljMzY3YWMyNjQiLCJpZCI6MjMyNzg2LCJpYXQiOjE3MjI4NzYyNTF9._EaN2cJDoDrXjzQn1G5qUaWtYR--Y-YUM92-H6mYnkQ';
const viewer = new Cesium.Viewer('cesiumContainer', {
    shouldAnimate: true,
    terrainProvider: Cesium.createWorldTerrain(),
    imageryProviderViewModel: new Cesium.UrlTemplateImageryProvider({
        url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
    }),
    sceneMode: Cesium.SceneMode.SCENE3D,
    shadows: true
});

viewer.scene.globe.depthTestAgainstTerrain = true;

viewer.camera.setView({
    destination: Cesium.Cartesian3.fromDegrees(0.0, 0.0, 400000000) // Very far out initially
});

// Animation to zoom in towards Earth and rotate it rapidly
function animateToEarth() {
    const destination = Cesium.Cartesian3.fromDegrees(0.0, 0.0, 20000000); // Closer zoom

    // Animate the camera zoom in and rotate the Earth simultaneously
    viewer.camera.flyTo({
        destination: destination,
        duration: 5, // Quick zoom (adjust to suit your preference)
        complete: function() {
            // Stop rotating when the zoom is complete
            stopRotation();
        }
    });

    // Start rotating the Earth immediately while zooming
    rotateEarth();
}

// Rotate the Earth rapidly while the camera moves
let rotationInterval;
function rotateEarth() {
    const globe = viewer.scene.globe;
    const rotationSpeed = 0.1;  // Faster rotation speed
    const maxRotationDuration = 5000; // Duration of rotation before stopping (in ms)
    let rotationTime = 0;

    rotationInterval = setInterval(function() {
        // Rotate the globe around its axis while zooming
        viewer.scene.camera.rotateRight(rotationSpeed); // Rotate the Earth to the right

        rotationTime += 16; // Approximately 60fps (16ms per frame)

        // Stop the rotation after the specified duration
        if (rotationTime >= maxRotationDuration) {
            clearInterval(rotationInterval);
        }
    }, 16); // Execute every frame (16ms for ~60fps)
}

// Stop the rotation after the specified duration
function stopRotation() {
    clearInterval(rotationInterval); // Clear rotation interval to stop it
}

// Start the animation when the page loads
document.addEventListener('DOMContentLoaded', function() {
    animateToEarth();
});

const overlays = {};
const pins = {};

// Load Sentinel overlay on 3D terrain
// Load Sentinel overlay on 3D terrain
function loadSentinelOverlay(eventId, showBoth) {
    fetch(`/get_overlay/${eventId}`)
        .then(response => response.json())
        .then(data => {
            if (data.bounds) {
                const bounds = Cesium.Rectangle.fromDegrees(
                    data.bounds[0], data.bounds[1], data.bounds[2], data.bounds[3]
                );

                // Remove existing layers
                if (overlays[eventId]) {
                    overlays[eventId].forEach(layer => viewer.imageryLayers.remove(layer));
                }

                // Add after image as a textured overlay on 3D terrain
                const imageOverlayAfter = new Cesium.SingleTileImageryProvider({
                    url: data.after_image,
                    rectangle: bounds
                });

                const layerAfter = viewer.imageryLayers.addImageryProvider(imageOverlayAfter);

                if (showBoth) {
                    // Add before image overlay if required
                    const imageOverlayBefore = new Cesium.SingleTileImageryProvider({
                        url: data.before_image,
                        rectangle: bounds
                    });

                    viewer.imageryLayers.addImageryProvider(imageOverlayBefore);
                }

                overlays[eventId] = [layerAfter];

                // Fly to the location with smooth camera movement
                viewer.camera.flyTo({ destination: bounds });

                const center = Cesium.Rectangle.center(bounds);
                if (pins[eventId]) {
                    viewer.entities.remove(pins[eventId]);
                }
				
                // Determine the correct pin icon based on event type
                let pinImage = "/static/fire.png"; // Default pin
				//console(data.et)
                //if (data.et === "fire") {
                //    pinImage = "/static/fire.png";
                //} else if (data.et === "flood") {
                //    pinImage = "/static/flood.png";
                //}
				//console.log('Pin Image URL:', pinImage); // Log the pin image path

                // Add pin on the center of the event
                const pin = viewer.entities.add({
                    position: Cesium.Cartesian3.fromDegrees(
                        Cesium.Math.toDegrees(center.longitude), 
                        Cesium.Math.toDegrees(center.latitude)
                    ),
                    billboard: { 
                        image: pinImage,
                        width: 30,
                        height: 30
                    },
                    description: `<h3>Event Details</h3>
                                  <p><strong>Event ID:</strong> ${eventId}</p>
                                  <p><strong>Popup:</strong> ${data.popup}</p>`,
                    id: eventId // We use the eventId to link the click event to the overlay
                });

                pins[eventId] = pin;
            }
        })
        .catch(err => console.error('Error loading overlay:', err));
}



// Function to trigger Show Overlay
function showOverlay(eventId) {
    loadSentinelOverlay(eventId, false);
}

// Function to trigger AI Analysis
function performAIAnalysis(eventId) {
    window.open(`/ai_analysis/${eventId}`, '_blank');
}

function addEventDetails(event) {
    const eventItem = document.createElement('div');
    eventItem.className = 'event-item';
    eventItem.innerHTML = `
        <div>
            <strong>Code:</strong> ${event.code}<br>
            <strong>Date:</strong> ${event.eventTime}<br>
            <strong>Continent:</strong> ${event.continent}<br>
            <strong>Country:</strong> ${event.country}<br>
            <button class="btn btn-primary btn-sm" onclick="showOverlay('${event.id}')">Show Overlay</button>
            <button class="btn btn-success btn-sm" onclick="performAIAnalysis('${event.id}')">AI Analysis</button>
            <button class="btn btn-info btn-sm" onclick="openReportModal('${event.id}')">View Report</button>
        </div>
    `;
    document.getElementById('events').appendChild(eventItem);
}

function openReportModal(eventId) {
    fetch(`/get_overlay/${eventId}`)
        .then(response => response.json())
        .then(data => {
            if (data.reportLink) {
                document.getElementById('reportFrame').src = data.reportLink;
                $('#reportModal').modal('show');
            } else {
                alert('Report link not available.');
            }
        })
        .catch(() => alert('Failed to load report link.'));
}

function loadEvents() {
    fetch('/get_events')
        .then(response => response.json())
        .then(data => {
            if (data.events && Array.isArray(data.events)) {
                data.events.forEach(event => {
                    addEventDetails(event);
                });
            } else {
                console.error('Unexpected data format:', data);
            }
        })
        .catch(err => console.error('Error loading events:', err));
}

// Load events on page load
document.addEventListener('DOMContentLoaded', () => {
    loadEvents();
});

document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.getElementById('sidebar');
    const sidebarHeader = document.getElementById('sidebar-header');
    const sidebarContent = document.getElementById('sidebar-content');
    const minimizeBtn = document.getElementById('minimizeBtn');
    const searchBox = document.getElementById('searchBox');

    // Toggle functionality for accordion
    sidebarHeader.addEventListener('click', function () {
        if (sidebarContent.style.display === 'none' || sidebarContent.style.display === '') {
            sidebarContent.style.display = 'block';
            sidebar.classList.add('expanded');
            sidebar.classList.remove('collapsed');
        } else {
            sidebarContent.style.display = 'none';
            sidebar.classList.add('collapsed');
            sidebar.classList.remove('expanded');
        }
    });

    // Minimize functionality
    minimizeBtn.addEventListener('click', function () {
        if (sidebar.classList.contains('expanded')) {
            sidebar.classList.add('collapsed');
            sidebar.classList.remove('expanded');
            sidebarContent.style.display = 'none';
        } else {
            sidebar.classList.add('expanded');
            sidebar.classList.remove('collapsed');
            sidebarContent.style.display = 'block';
        }
    });

    // Drag functionality for the entire sidebar (not just the header)
    let isDragging = false;
    let offsetX, offsetY;

    sidebar.addEventListener('mousedown', function (e) {
        isDragging = true;
        offsetX = e.clientX - sidebar.getBoundingClientRect().left;
        offsetY = e.clientY - sidebar.getBoundingClientRect().top;
        sidebar.style.position = 'absolute';
    });

    document.addEventListener('mousemove', function (e) {
        if (isDragging) {
            window.requestAnimationFrame(function() {
                sidebar.style.left = `${e.clientX - offsetX}px`;
                sidebar.style.top = `${e.clientY - offsetY}px`;
            });
        }
    });

    document.addEventListener('mouseup', function () {
        isDragging = false;
    });

    // Search functionality
    searchBox.addEventListener('input', function () {
        const searchTerm = searchBox.value.toLowerCase();
        const eventItems = document.querySelectorAll('.event-item');
        eventItems.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(searchTerm) ? 'block' : 'none';
        });
    });
});

const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);

handler.setInputAction(function (movement) {
    const pickedObject = viewer.scene.pick(movement.position);

    if (Cesium.defined(pickedObject) && pickedObject.imagery) {
        console.log("Clicked on overlay image!");

        // Παίρνουμε το eventId από το layer αν το έχουμε αποθηκεύσει
        const eventId = pickedObject.imagery.layer.eventId || "default_event";
        
        // Καλούμε τη συνάρτηση που θέλουμε
        showOverlay(eventId);
    }
}, Cesium.ScreenSpaceEventType.LEFT_CLICK);
