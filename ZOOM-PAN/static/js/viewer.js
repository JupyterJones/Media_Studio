// ZoomPan Studio Frontend Controller
document.addEventListener('DOMContentLoaded', () => {
  const canvas = document.getElementById('image-canvas');
  const ctx = canvas.getContext('2d');
  const container = document.getElementById('canvas-container');

  // Application State
  let img = new Image();
  let imageFilename = 'sample.jpg';
  let imageWidth = 1920;
  let imageHeight = 1080;
  let isImageLoaded = false;

  // Viewport Transform
  let transform = {
    scale: 1.0,
    panX: 0,
    panY: 0
  };

  // Points & Keyframes
  let points = [];
  let activePointId = null;
  let showOverlay = true;
  let isPlaying = false;
  let animFrameId = null;

  // Dragging state
  let isDragging = false;
  let startMouseX = 0;
  let startMouseY = 0;
  let startPanX = 0;
  let startPanY = 0;

  // Modal Helpers
  function openModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('show');
  }

  function closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('show');
  }

  window.openModal = openModal;
  window.closeModal = closeModal;

  // DOM Element References
  const hudPxX = document.getElementById('hud-px-x');
  const hudPxY = document.getElementById('hud-px-y');
  const hudZoomScale = document.getElementById('hud-zoom-scale');
  const imgDimInfo = document.getElementById('img-dim-info');

  const inspectorCard = document.getElementById('inspector-card');
  const activePointBadge = document.getElementById('active-point-badge');
  const pointLabelInput = document.getElementById('point-label-input');
  const pointPxXInput = document.getElementById('point-px-x');
  const pointPxYInput = document.getElementById('point-px-y');
  const pointZoomSlider = document.getElementById('point-zoom-slider');
  const pointZoomNum = document.getElementById('point-zoom-num');
  const zoomValDisplay = document.getElementById('zoom-val-display');
  const pointHoldSecInput = document.getElementById('point-hold-sec');
  const pointTransSecInput = document.getElementById('point-trans-sec');
  const btnFocusPoint = document.getElementById('btn-focus-point');
  const btnDeletePoint = document.getElementById('btn-delete-point');

  const pointsListContainer = document.getElementById('points-list-container');
  const pointCountLabel = document.getElementById('point-count-label');

  // Initialize Canvas Size to full container bounds
  function resizeCanvas() {
    const rect = container.getBoundingClientRect();
    const w = Math.floor(rect.width || container.clientWidth || 800);
    const h = Math.floor(rect.height || container.clientHeight || 600);
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
    render();
  }

  // Observe container size changes
  const resizeObserver = new ResizeObserver(() => {
    resizeCanvas();
  });
  resizeObserver.observe(container);

  window.addEventListener('resize', resizeCanvas);
  setTimeout(resizeCanvas, 50);
  setTimeout(resizeCanvas, 300);


  // Load default sample image
  function loadInitialImage(src, filename = 'sample.jpg', width = 1920, height = 1080, preservePoints = false) {
    const newImg = new Image();
    imageFilename = filename;
    newImg.onload = () => {
      img = newImg;
      isImageLoaded = true;
      imageWidth = img.naturalWidth || width;
      imageHeight = img.naturalHeight || height;
      if (imgDimInfo) imgDimInfo.textContent = `${imageWidth} x ${imageHeight} px`;
      resizeCanvas();
      resetView();
      
      // Default keyframe points if none exist and not preserving loaded JSON points
      if (points.length === 0 && !preservePoints && filename === 'sample.jpg') {
        addPoint(Math.round(imageWidth * 0.3), Math.round(imageHeight * 0.4), "Camera Point 1", 3.0);
        addPoint(Math.round(imageWidth * 0.5), Math.round(imageHeight * 0.5), "Camera Point 2", 2.5);
        addPoint(Math.round(imageWidth * 0.7), Math.round(imageHeight * 0.3), "Camera Point 3", 3.0);
      }
    };
    newImg.onerror = (e) => {
      console.error('Error loading image:', src, e);
    };
    newImg.src = src;
    if (newImg.complete && newImg.naturalWidth) {
      newImg.onload();
    }
  }


  // Reset Viewport to fit canvas
  function resetView() {
    if (!isImageLoaded) return;
    const scaleX = canvas.width / imageWidth;
    const scaleY = canvas.height / imageHeight;
    transform.scale = Math.min(scaleX, scaleY) * 0.95;
    transform.panX = (canvas.width - imageWidth * transform.scale) / 2;
    transform.panY = (canvas.height - imageHeight * transform.scale) / 2;
    updateHud();
    render();
  }

  // Set Viewport to 100% 1:1 Actual Image Resolution
  function setActualSize() {
    if (!isImageLoaded) return;
    transform.scale = 1.0;
    transform.panX = (canvas.width - imageWidth) / 2;
    transform.panY = (canvas.height - imageHeight) / 2;
    updateHud();
    render();
  }

  // Coordinate Conversion Helpers
  function screenToImage(screenX, screenY) {
    const rect = canvas.getBoundingClientRect();
    const x = screenX - rect.left;
    const y = screenY - rect.top;
    const imgX = Math.round((x - transform.panX) / transform.scale);
    const imgY = Math.round((y - transform.panY) / transform.scale);
    return { x: imgX, y: imgY };
  }

  function imageToScreen(imgX, imgY) {
    return {
      x: imgX * transform.scale + transform.panX,
      y: imgY * transform.scale + transform.panY
    };
  }

  function wrapTextCanvas(text, maxChars = 26) {
    const lines = [];
    text.split('\n').forEach(paragraph => {
      const words = paragraph.split(' ');
      let currLine = [];
      let currLen = 0;
      words.forEach(w => {
        if (currLen + w.length + 1 > maxChars && currLine.length > 0) {
          lines.push(currLine.join(' '));
          currLine = [w];
          currLen = w.length;
        } else {
          currLine.push(w);
          currLen += w.length + (currLen > 0 ? 1 : 0);
        }
      });
      if (currLine.length > 0) lines.push(currLine.join(' '));
    });
    return lines.length > 0 ? lines : [text];
  }

  function drawComicBubbleOnCanvas(ctx, screenPos, text, style) {
    if (!text) return;
    ctx.save();
    
    const lines = wrapTextCanvas(text, 26);
    const charCount = text.length;

    // Dynamic Font Sizing
    let fontSize = 13;
    let fontWeight = '600';
    if (style === 'sfx') {
      fontSize = charCount <= 8 ? 18 : 14;
      fontWeight = '800';
    } else if (charCount <= 10) {
      fontSize = 15;
    } else if (charCount <= 50) {
      fontSize = 13;
    } else if (charCount <= 120) {
      fontSize = 12;
    } else {
      fontSize = 11;
    }

    ctx.font = `${fontWeight} ${fontSize}px Inter, sans-serif`;
    
    let maxW = 60;
    lines.forEach(l => {
      const w = ctx.measureText(l).width;
      if (w > maxW) maxW = w;
    });

    const lineH = Math.round(fontSize * 1.3);
    const padX = 16, padY = 12;
    const boxW = maxW + padX * 2;
    const boxH = lines.length * lineH + padY * 2;
    
    const boxX = Math.max(10, Math.min(screenPos.x - boxW / 2, canvas.width - boxW - 10));
    const boxY = Math.max(10, screenPos.y - boxH - 20);

    if (style === 'speech' || style === 'speech_left') {
      const tailX = boxX + 20;
      ctx.beginPath();
      ctx.moveTo(tailX - 8, boxY + boxH);
      ctx.lineTo(tailX + 8, boxY + boxH);
      ctx.lineTo(screenPos.x, screenPos.y);
      ctx.closePath();
      ctx.fillStyle = '#ffffff';
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#000000';
      ctx.stroke();

      ctx.beginPath();
      ctx.roundRect(boxX, boxY, boxW, boxH, 8);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#000000';
      ctx.stroke();
      ctx.fillStyle = '#000000';

    } else if (style === 'speech_right') {
      const tailX = boxX + boxW - 20;
      ctx.beginPath();
      ctx.moveTo(tailX - 8, boxY + boxH);
      ctx.lineTo(tailX + 8, boxY + boxH);
      ctx.lineTo(screenPos.x, screenPos.y);
      ctx.closePath();
      ctx.fillStyle = '#ffffff';
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#000000';
      ctx.stroke();

      ctx.beginPath();
      ctx.roundRect(boxX, boxY, boxW, boxH, 8);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#000000';
      ctx.stroke();
      ctx.fillStyle = '#000000';

    } else if (style === 'thought' || style === 'thought_left') {
      const tX = boxX + 20;
      ctx.beginPath();
      ctx.arc(screenPos.x * 0.4 + tX * 0.6, screenPos.y * 0.4 + (boxY + boxH) * 0.6, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
      ctx.strokeStyle = '#000000';
      ctx.stroke();

      ctx.beginPath();
      ctx.roundRect(boxX, boxY, boxW, boxH, 16);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#000000';
      ctx.stroke();
      ctx.fillStyle = '#000000';

    } else if (style === 'thought_right') {
      const tX = boxX + boxW - 20;
      ctx.beginPath();
      ctx.arc(screenPos.x * 0.4 + tX * 0.6, screenPos.y * 0.4 + (boxY + boxH) * 0.6, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
      ctx.strokeStyle = '#000000';
      ctx.stroke();

      ctx.beginPath();
      ctx.roundRect(boxX, boxY, boxW, boxH, 16);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#000000';
      ctx.stroke();
      ctx.fillStyle = '#000000';

    } else if (style === 'idea') {
      ctx.beginPath();
      ctx.roundRect(boxX, boxY, boxW, boxH, 10);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
      ctx.lineWidth = 3;
      ctx.strokeStyle = '#f59e0b';
      ctx.stroke();
      
      // Lightbulb header badge
      ctx.beginPath();
      ctx.arc(boxX + boxW / 2, boxY - 6, 8, 0, Math.PI * 2);
      ctx.fillStyle = '#f59e0b';
      ctx.fill();
      ctx.strokeStyle = '#000000';
      ctx.stroke();
      ctx.fillStyle = '#000000';

    } else if (style === 'caption') {

      ctx.beginPath();
      ctx.rect(boxX, boxY, boxW, boxH);
      ctx.fillStyle = '#fff066';
      ctx.fill();
      ctx.lineWidth = 3;
      ctx.strokeStyle = '#000000';
      ctx.stroke();
      ctx.fillStyle = '#000000';

    } else if (style === 'sfx') {
      ctx.beginPath();
      ctx.roundRect(boxX, boxY, boxW, boxH, 6);
      ctx.fillStyle = '#ef4444';
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#ffffff';
      ctx.stroke();
      ctx.fillStyle = '#ffffff';

    } else if (style === 'manga') {
      ctx.beginPath();
      ctx.rect(boxX, boxY, boxW, boxH);
      ctx.fillStyle = '#0a0a0a';
      ctx.fill();
      ctx.lineWidth = 3;
      ctx.strokeStyle = '#ffffff';
      ctx.stroke();
      ctx.fillStyle = '#ffffff';

    } else if (style === 'noir') {
      ctx.beginPath();
      ctx.rect(boxX, boxY, boxW, boxH);
      ctx.fillStyle = '#f4ecc2';
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#2d2013';
      ctx.stroke();
      ctx.fillStyle = '#2d2013';

    } else if (style === 'hero') {
      ctx.beginPath();
      ctx.roundRect(boxX, boxY, boxW, boxH, 6);
      ctx.fillStyle = '#1e3a8a';
      ctx.fill();
      ctx.lineWidth = 3;
      ctx.strokeStyle = '#f59e0b';
      ctx.stroke();
      ctx.fillStyle = '#ffffff';

    } else {
      ctx.beginPath();
      ctx.roundRect(boxX, boxY, boxW, boxH, 8);
      ctx.fillStyle = '#0f1319';
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#00e5ff';
      ctx.stroke();
      ctx.fillStyle = '#ffffff';
    }


    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    lines.forEach((l, idx) => {
      ctx.fillText(l, boxX + boxW / 2, boxY + padY + idx * lineH);
    });

    ctx.restore();
  }


  // Canvas Main Render Loop
  function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (isImageLoaded) {
      // Draw base image
      ctx.drawImage(
        img,
        transform.panX, transform.panY,
        imageWidth * transform.scale, imageHeight * transform.scale
      );
    }

    // Draw Overlay Comic Bubbles
    if (showOverlay && isImageLoaded) {
      points.forEach((p, idx) => {
        const screenPos = imageToScreen(p.x, p.y);
        const isActive = p.id === activePointId;

        // Subtle focus ring ONLY for active editing caption
        if (isActive) {
          ctx.beginPath();
          ctx.arc(screenPos.x, screenPos.y, 6, 0, Math.PI * 2);
          ctx.fillStyle = '#00e5ff';
          ctx.fill();
          ctx.lineWidth = 2;
          ctx.strokeStyle = '#ffffff';
          ctx.stroke();
        }

        // Render Comic Speech Bubble / Caption Box
        if (p.label) {
          drawComicBubbleOnCanvas(ctx, screenPos, p.label, p.bubble_style || 'speech');
        }
      });
    }
  }



  // Update HUD Display
  function updateHud() {
    hudZoomScale.textContent = `${transform.scale.toFixed(2)}x`;
  }

  // Mouse & Touch Pan / Zoom Event Handlers
  canvas.addEventListener('mousedown', (e) => {
    if (isPlaying) return;
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Check if clicked an existing point pin
    let clickedPoint = null;
    points.forEach(p => {
      const screenPos = imageToScreen(p.x, p.y);
      const dist = Math.hypot(clickX - screenPos.x, clickY - screenPos.y);
      if (dist <= 18) {
        clickedPoint = p;
      }
    });

    if (clickedPoint) {
      selectPoint(clickedPoint.id);
    } else {
      // Start Drag-Pan
      isDragging = true;
      startMouseX = e.clientX;
      startMouseY = e.clientY;
      startPanX = transform.panX;
      startPanY = transform.panY;
    }
  });

  canvas.addEventListener('mousemove', (e) => {
    const coords = screenToImage(e.clientX, e.clientY);
    hudPxX.textContent = Math.max(0, Math.min(coords.x, imageWidth));
    hudPxY.textContent = Math.max(0, Math.min(coords.y, imageHeight));

    if (isDragging) {
      const dx = e.clientX - startMouseX;
      const dy = e.clientY - startMouseY;
      transform.panX = startPanX + dx;
      transform.panY = startPanY + dy;
      render();
    }
  });

  window.addEventListener('mouseup', () => {
    isDragging = false;
  });

  // Touch Handlers for Mobile Phones
  let touchStartDist = 0;
  canvas.addEventListener('touchstart', (e) => {
    if (e.touches.length === 1) {
      isDragging = true;
      startMouseX = e.touches[0].clientX;
      startMouseY = e.touches[0].clientY;
      startPanX = transform.panX;
      startPanY = transform.panY;
    } else if (e.touches.length === 2) {
      isDragging = false;
      touchStartDist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
    }
  }, { passive: true });

  canvas.addEventListener('touchmove', (e) => {
    if (e.touches.length === 1 && isDragging) {
      const dx = e.touches[0].clientX - startMouseX;
      const dy = e.touches[0].clientY - startMouseY;
      transform.panX = startPanX + dx;
      transform.panY = startPanY + dy;
      render();
    } else if (e.touches.length === 2 && touchStartDist > 0) {
      const currentDist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
      const factor = currentDist / touchStartDist;
      touchStartDist = currentDist;
      transform.scale = Math.max(0.1, Math.min(25.0, transform.scale * factor));
      updateHud();
      render();
    }
  }, { passive: true });

  canvas.addEventListener('touchend', (e) => {
    if (isDragging && e.changedTouches.length === 1) {
      const touch = e.changedTouches[0];
      const dragDist = Math.hypot(touch.clientX - startMouseX, touch.clientY - startMouseY);
      if (dragDist < 6 && !isPlaying) {
        const coords = screenToImage(touch.clientX, touch.clientY);
        if (coords.x >= 0 && coords.x <= imageWidth && coords.y >= 0 && coords.y <= imageHeight) {
          let nearPin = false;
          const rect = canvas.getBoundingClientRect();
          const clickX = touch.clientX - rect.left;
          const clickY = touch.clientY - rect.top;
          points.forEach(p => {
            const screenPos = imageToScreen(p.x, p.y);
            if (Math.hypot(clickX - screenPos.x, clickY - screenPos.y) <= 24) {
              nearPin = true;
              selectPoint(p.id);
            }
          });
          if (!nearPin) {
            addPoint(coords.x, coords.y);
          }
        }
      }
    }
    isDragging = false;
    touchStartDist = 0;
  });

  // Click to Add Point
  canvas.addEventListener('click', (e) => {
    if (isPlaying) return;
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Check if clicked near an existing pin
    let nearPin = false;
    points.forEach(p => {
      const screenPos = imageToScreen(p.x, p.y);
      if (Math.hypot(clickX - screenPos.x, clickY - screenPos.y) <= 18) {
        nearPin = true;
      }
    });

    // If click was a static click (not a drag) and not on an existing pin, add point!
    const dragDist = Math.hypot(e.clientX - startMouseX, e.clientY - startMouseY);
    if (!nearPin && dragDist < 4) {
      const coords = screenToImage(e.clientX, e.clientY);
      if (coords.x >= 0 && coords.x <= imageWidth && coords.y >= 0 && coords.y <= imageHeight) {
        addPoint(coords.x, coords.y);
      }
    }
  });

  // Wheel Zoom
  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    if (isPlaying) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
    const newScale = Math.max(0.1, Math.min(25.0, transform.scale * zoomFactor));

    // Zoom centered on cursor
    transform.panX = mouseX - (mouseX - transform.panX) * (newScale / transform.scale);
    transform.panY = mouseY - (mouseY - transform.panY) * (newScale / transform.scale);
    transform.scale = newScale;

    updateHud();
    render();
  }, { passive: false });

  // Add Point / Caption Function
  function addPoint(x, y, label = null, zoom = 1.25) {
    const id = 'pt_' + Date.now() + '_' + Math.floor(Math.random()*1000);
    const newPoint = {
      id: id,
      x: Math.round(x),
      y: Math.round(y),
      label: label || `Caption ${points.length + 1}`,
      bubble_style: 'speech_left',
      zoom_enabled: true,
      zoom: zoom,
      hold_duration: 1.5,
      transition_duration: 2.0
    };
    points.push(newPoint);
    selectPoint(id);
    updatePointsList();
    render();
  }



  // Select Active Point
  function selectPoint(id) {
    activePointId = id;
    const p = points.find(pt => pt.id === id);
    const pointBubbleStyle = document.getElementById('point-bubble-style');
    const pointZoomEnabled = document.getElementById('point-zoom-enabled');
    const pointLabelInput = document.getElementById('point-label-input');

    if (p) {
      activePointBadge.textContent = `#${points.indexOf(p) + 1} ${p.label || 'Caption'}`;
      pointLabelInput.disabled = false;
      pointLabelInput.removeAttribute('disabled');
      pointLabelInput.value = p.label || '';
      pointBubbleStyle.disabled = false;
      pointBubbleStyle.removeAttribute('disabled');
      pointBubbleStyle.value = p.bubble_style || 'speech';
      pointZoomEnabled.disabled = false;
      pointZoomEnabled.removeAttribute('disabled');
      const isZoomed = p.zoom_enabled !== false;
      pointZoomEnabled.checked = isZoomed;

      pointPxXInput.disabled = false;
      pointPxXInput.removeAttribute('disabled');
      pointPxXInput.value = p.x;
      pointPxYInput.disabled = false;
      pointPxYInput.removeAttribute('disabled');
      pointPxYInput.value = p.y;
      
      pointZoomSlider.disabled = !isZoomed;
      pointZoomNum.disabled = !isZoomed;
      document.getElementById('zoom-controls-wrap').style.opacity = isZoomed ? '1' : '0.35';

      pointZoomSlider.value = p.zoom;
      pointZoomNum.value = p.zoom;
      zoomValDisplay.textContent = `${p.zoom.toFixed(1)}x`;
      pointHoldSecInput.disabled = false;
      pointHoldSecInput.removeAttribute('disabled');
      pointHoldSecInput.value = p.hold_duration;
      pointTransSecInput.disabled = false;
      pointTransSecInput.removeAttribute('disabled');
      pointTransSecInput.value = p.transition_duration;
      btnFocusPoint.disabled = false;
      btnFocusPoint.removeAttribute('disabled');
      btnDeletePoint.disabled = false;
      btnDeletePoint.removeAttribute('disabled');
    } else {

      activePointBadge.textContent = 'No Caption Selected';
      pointLabelInput.value = '';
      pointLabelInput.disabled = true;
      pointLabelInput.setAttribute('disabled', 'true');
      pointBubbleStyle.disabled = true;
      pointZoomEnabled.disabled = true;
      pointPxXInput.disabled = true;
      pointPxYInput.disabled = true;
      pointZoomSlider.disabled = true;
      pointZoomNum.disabled = true;
      pointHoldSecInput.disabled = true;
      pointTransSecInput.disabled = true;
      btnFocusPoint.disabled = true;
      btnDeletePoint.disabled = true;
    }
    updatePointsList();
    render();
  }



  // Update Points UI List
  function updatePointsList() {
    pointsListContainer.innerHTML = '';
    pointCountLabel.textContent = `${points.length} Point${points.length === 1 ? '' : 's'}`;

    points.forEach((p, idx) => {
      const item = document.createElement('div');
      item.className = `point-item ${p.id === activePointId ? 'active' : ''}`;
      item.innerHTML = `
        <div class="point-badge">${idx + 1}</div>
        <div class="point-info">
          <span class="point-name">${p.label}</span>
          <span class="point-coords">X: ${p.x}px, Y: ${p.y}px | Zoom: ${p.zoom}x</span>
        </div>
        <div class="point-actions">
          <button class="btn btn-sm" title="Focus view" onclick="event.stopPropagation(); focusOnPoint('${p.id}')">🎯</button>
          <button class="btn btn-sm btn-danger" title="Delete" onclick="event.stopPropagation(); deletePoint('${p.id}')">✕</button>
        </div>
      `;
      item.addEventListener('click', () => selectPoint(p.id));
      pointsListContainer.appendChild(item);
    });
  }

  // Focus View Animated Transition to a Point
  window.focusOnPoint = function(id) {
    const p = points.find(pt => pt.id === id);
    if (!p) return;

    selectPoint(id);
    
    // NO CHECK OR ZOOM <= 1.0: Stay at full overview view
    if (p.zoom_enabled === false || p.zoom <= 1.0) {
      resetView();
    } else {
      const fitScale = Math.min(canvas.width / imageWidth, canvas.height / imageHeight) * 0.95;
      const targetScale = fitScale * p.zoom;
      
      const tZoom = Math.min(1.0, Math.max(0.0, (p.zoom - 1.0) / 0.8));
      const effX = (imageWidth / 2.0) + (p.x - (imageWidth / 2.0)) * tZoom;
      const effY = (imageHeight / 2.0) + (p.y - (imageHeight / 2.0)) * tZoom;

      const targetPanX = canvas.width / 2 - effX * targetScale;
      const targetPanY = canvas.height / 2 - effY * targetScale;

      animateViewport(targetPanX, targetPanY, targetScale, 600);
    }
  };


  window.deletePoint = function(id) {
    points = points.filter(p => p.id !== id);
    if (activePointId === id) {
      selectPoint(points.length > 0 ? points[0].id : null);
    } else {
      updatePointsList();
      render();
    }
  };

  function animateViewport(targetPanX, targetPanY, targetScale, durationMs = 800) {
    const startPanX = transform.panX;
    const startPanY = transform.panY;
    const startScale = transform.scale;
    const startTime = performance.now();

    function step(now) {
      const elapsed = now - startTime;
      const progress = Math.min(1.0, elapsed / durationMs);
      const ease = progress * progress * (3 - 2 * progress); // smoothstep

      transform.panX = startPanX + (targetPanX - startPanX) * ease;
      transform.panY = startPanY + (targetPanY - startPanY) * ease;
      transform.scale = startScale + (targetScale - startScale) * ease;

      updateHud();
      render();

      if (progress < 1.0) {
        requestAnimationFrame(step);
      }
    }
    requestAnimationFrame(step);
  }

  // Form Inputs Listener for Active Point
  pointLabelInput.addEventListener('focus', () => {
    if (!activePointId && points.length > 0) {
      selectPoint(points[0].id);
    }
  });

  pointLabelInput.addEventListener('input', (e) => {
    const p = points.find(pt => pt.id === activePointId);
    if (p) {
      p.label = e.target.value;
      updatePointsList();
      render();
    }
  });


  document.getElementById('point-bubble-style').addEventListener('change', (e) => {
    const p = points.find(pt => pt.id === activePointId);
    if (p) {
      p.bubble_style = e.target.value;
      updatePointsList();
      render();
    }
  });

  document.getElementById('point-zoom-enabled').addEventListener('change', (e) => {
    const p = points.find(pt => pt.id === activePointId);
    if (p) {
      p.zoom_enabled = e.target.checked;
      pointZoomSlider.disabled = !e.target.checked;
      pointZoomNum.disabled = !e.target.checked;
      document.getElementById('zoom-controls-wrap').style.opacity = e.target.checked ? '1' : '0.35';
      updatePointsList();
      render();
    }
  });



  pointPxXInput.addEventListener('change', (e) => {
    const p = points.find(pt => pt.id === activePointId);
    if (p) {
      p.x = parseInt(e.target.value) || 0;
      updatePointsList();
      render();
    }
  });

  pointPxYInput.addEventListener('change', (e) => {
    const p = points.find(pt => pt.id === activePointId);
    if (p) {
      p.y = parseInt(e.target.value) || 0;
      updatePointsList();
      render();
    }
  });

  const syncZoom = (val) => {
    const p = points.find(pt => pt.id === activePointId);
    if (p) {
      p.zoom = parseFloat(val);
      pointZoomSlider.value = p.zoom;
      pointZoomNum.value = p.zoom;
      zoomValDisplay.textContent = `${p.zoom.toFixed(1)}x`;
      updatePointsList();
      render();
    }
  };

  pointZoomSlider.addEventListener('input', (e) => syncZoom(e.target.value));
  pointZoomNum.addEventListener('change', (e) => syncZoom(e.target.value));

  pointHoldSecInput.addEventListener('change', (e) => {
    const p = points.find(pt => pt.id === activePointId);
    if (p) p.hold_duration = parseFloat(e.target.value) || 1.5;
  });

  pointTransSecInput.addEventListener('change', (e) => {
    const p = points.find(pt => pt.id === activePointId);
    if (p) p.transition_duration = parseFloat(e.target.value) || 2.0;
  });

  btnFocusPoint.addEventListener('click', () => {
    if (activePointId) window.focusOnPoint(activePointId);
  });

  btnDeletePoint.addEventListener('click', () => {
    if (activePointId) window.deletePoint(activePointId);
  });

  // HUD Buttons
  document.getElementById('hud-zoom-in').addEventListener('click', () => {
    transform.scale *= 1.25;
    updateHud();
    render();
  });

  document.getElementById('hud-zoom-out').addEventListener('click', () => {
    transform.scale /= 1.25;
    updateHud();
    render();
  });

  document.getElementById('hud-actual-size').addEventListener('click', setActualSize);

  document.getElementById('hud-reset-view').addEventListener('click', resetView);

  document.getElementById('hud-toggle-points').addEventListener('click', () => {
    showOverlay = !showOverlay;
    render();
  });

  const sidebar = document.querySelector('.sidebar');
  document.getElementById('hud-toggle-sidebar').addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
    setTimeout(() => {
      resizeCanvas();
    }, 300);
  });


  // Image File Upload
  const imageFileInput = document.getElementById('image-file-input');
  if (imageFileInput) {
    imageFileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('image', file);

      fetch('/api/upload', {
        method: 'POST',
        body: formData
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          points = [];
          activePointId = null;
          selectPoint(null);
          sessionStorage.setItem('zoompan_active_url', data.url);
          sessionStorage.setItem('zoompan_active_image', data.filename);
          loadInitialImage(data.url, data.filename, data.width, data.height);
        } else {
          alert('Upload Error: ' + (data.error || 'Unknown error'));
        }
        e.target.value = '';
      })
      .catch(err => {
        alert('Failed to upload image: ' + err);
        e.target.value = '';
      });
    });
  }

  // Save JSON Project / Pattern
  document.getElementById('btn-save-json').addEventListener('click', () => {
    if (points.length === 0) {
      alert('Please add at least one point before saving JSON!');
      return;
    }
    const projectName = prompt('Enter a name for this JSON zoom pattern file:', 'zoom_pattern');
    if (!projectName) return;

    // Attach proportional ratios so pattern can be reused on any image resolution
    const pointsWithRatios = points.map(p => ({
      ...p,
      x_ratio: Number((p.x / imageWidth).toFixed(6)),
      y_ratio: Number((p.y / imageHeight).toFixed(6))
    }));

    const payload = {
      project_name: projectName,
      filename: imageFilename,
      image_width: imageWidth,
      image_height: imageHeight,
      points: pointsWithRatios
    };

    fetch('/api/save_json', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert(`Pattern saved successfully as ${data.project_filename}!`);
      } else {
        alert('Save Error: ' + data.error);
      }
    });
  });

  // Load JSON Modal & Fetch
  const btnLoadJson = document.getElementById('btn-load-json');
  if (btnLoadJson) {
    btnLoadJson.addEventListener('click', (e) => {
      if (e) e.preventDefault();
      openModal('modal-load-json');

      fetch('/api/list_json')
        .then(res => res.json())
        .then(data => {
          const select = document.getElementById('select-project-file');
          if (!select) return;
          select.innerHTML = '';
          if (data.projects && data.projects.length > 0) {
            data.projects.forEach(file => {
              const opt = document.createElement('option');
              opt.value = file;
              opt.textContent = file;
              select.appendChild(opt);
            });
          } else {
            select.innerHTML = '<option value="">No saved projects found</option>';
          }
        })
        .catch(err => console.error('Error fetching projects list:', err));
    });
  }

  function applyLoadedJsonData(data) {
    if (!data.points || data.points.length === 0) {
      alert('No keyframe points found in this JSON file!');
      return;
    }

    const keepCurrentImage = document.getElementById('chk-keep-current-image') ? 
      document.getElementById('chk-keep-current-image').checked : false;

    const targetImg = data.filename || data.image_filename;
    const targetUrl = data.url || (targetImg ? `/static/uploads/${targetImg}` : null);

    const applyPoints = () => {
      const origW = data.image_width || imageWidth || 1920;
      const origH = data.image_height || imageHeight || 1080;

      points = data.points.map((p, idx) => {
        const xRatio = p.x_ratio !== undefined ? p.x_ratio : (p.x / origW);
        const yRatio = p.y_ratio !== undefined ? p.y_ratio : (p.y / origH);

        return {
          ...p,
          id: p.id || ('pt_' + Date.now() + '_' + idx),
          x: Math.round(xRatio * imageWidth),
          y: Math.round(yRatio * imageHeight),
          transition_duration: p.transition_duration || 2.0,
          hold_duration: p.hold_duration || 1.0
        };
      });

      if (data.audio_filename) {
        if (window.fetchAndPopulateAudioTracks) window.fetchAndPopulateAudioTracks();
        setTimeout(() => {
          const audioSelect = document.getElementById('export-audio-track');
          if (audioSelect) audioSelect.value = data.audio_filename;
        }, 150);
      }

      selectPoint(points.length > 0 ? points[0].id : null);
      closeModal('modal-load-json');
      render();
      updatePointsList();
    };

    if (targetImg && targetUrl && !keepCurrentImage) {
      imageFilename = targetImg;
      sessionStorage.setItem('zoompan_active_url', targetUrl);
      sessionStorage.setItem('zoompan_active_image', targetImg);
      loadInitialImage(targetUrl, targetImg, data.image_width || 1920, data.image_height || 1080, true);
      setTimeout(applyPoints, 100);
    } else {
      applyPoints();
    }
  }

  // Local JSON File Upload Listener
  const localJsonInput = document.getElementById('local-json-file-input');
  if (localJsonInput) {
    localJsonInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (evt) => {
        try {
          const data = JSON.parse(evt.target.result);
          applyLoadedJsonData(data);
        } catch (err) {
          alert('Invalid JSON file format: ' + err);
        }
        e.target.value = '';
      };
      reader.readAsText(file);
    });
  }

  document.getElementById('btn-confirm-load-json').addEventListener('click', () => {
    const filename = document.getElementById('select-project-file').value;
    if (!filename) {
      alert('Please select a project from the list or choose a local .json file above.');
      return;
    }

    fetch(`/api/load_json/${filename}`)
      .then(res => res.json())
      .then(data => {
        applyLoadedJsonData(data);
      })
      .catch(err => alert('Failed to load server project: ' + err));
  });


  // Live Browser Sequence Playback
  const btnPreviewRun = document.getElementById('btn-preview-run');
  if (btnPreviewRun) {
    btnPreviewRun.addEventListener('click', () => {
      if (isPlaying) {
        isPlaying = false;
        if (animFrameId) cancelAnimationFrame(animFrameId);
        btnPreviewRun.textContent = '▶️ Live Play';
        return;
      }
      if (points.length === 0) {
        alert('Add some points first!');
        return;
      }

      isPlaying = true;
      btnPreviewRun.textContent = '⏹️ Stop Play';

      let currentIdx = 0;

      function playNext() {
        if (!isPlaying) return;
        if (currentIdx >= points.length) {
          // Reset to initial full view when finished
          resetView();
          isPlaying = false;
          btnPreviewRun.textContent = '▶️ Live Play';
          return;
        }

        const p = points[currentIdx];
        selectPoint(p.id);
        window.focusOnPoint(p.id);

        // Wait hold duration + transition before advancing
        const totalTimeMs = (p.transition_duration + p.hold_duration) * 1000;
        currentIdx++;
        setTimeout(() => {
          if (isPlaying) playNext();
        }, totalTimeMs);
      }

      playNext();
    });
  }
  // Populate Audio Tracks dropdown
  function loadAudioTracks() {
    const audioSelect = document.getElementById('export-audio-track');
    const btnRefresh = document.getElementById('btn-refresh-audio');
    if (!audioSelect) return;

    if (btnRefresh) btnRefresh.textContent = '⏳ Loading...';

    fetch('/api/list_audio?t=' + Date.now())
      .then(res => res.json())
      .then(data => {
        if (data.audio_files && Array.isArray(data.audio_files)) {
          const currentVal = audioSelect.value;
          const fragment = document.createDocumentFragment();
          
          const defaultOpt = document.createElement('option');
          defaultOpt.value = 'none';
          defaultOpt.textContent = '-- None (No Audio) --';
          if (!currentVal || currentVal === 'none') defaultOpt.selected = true;
          fragment.appendChild(defaultOpt);

          data.audio_files.forEach(f => {
            const opt = document.createElement('option');
            opt.value = f;
            opt.textContent = f;
            if (f === currentVal) opt.selected = true;
            fragment.appendChild(opt);
          });

          audioSelect.innerHTML = '';
          audioSelect.appendChild(fragment);

          if (btnRefresh) {
            btnRefresh.textContent = `🔄 Refresh (${data.audio_files.length})`;
            setTimeout(() => { btnRefresh.textContent = '🔄 Refresh'; }, 3000);
          }
        }
      })
      .catch(err => {
        console.error('Error loading audio files:', err);
        if (btnRefresh) btnRefresh.textContent = '❌ Error';
      });
  }

  window.loadAudioTracks = loadAudioTracks;
  loadAudioTracks();

  const btnRefreshAudio = document.getElementById('btn-refresh-audio');
  if (btnRefreshAudio) {
    btnRefreshAudio.addEventListener('click', (e) => {
      if (e) e.preventDefault();
      loadAudioTracks();
    });
  }

  // Auto-Sync Camera Moves to Selected Audio Duration
  async function autoSyncAudio() {
    const audioSelect = document.getElementById('export-audio-track');
    const selectedAudio = audioSelect ? audioSelect.value : 'none';
    if (!selectedAudio || selectedAudio === 'none') {
      alert('Please select an Audio Track from the dropdown first!');
      return;
    }
    if (points.length === 0) {
      alert('Please click on the canvas to add at least 1 keyframe point first!');
      return;
    }

    try {
      const res = await fetch(`/api/audio_info/${encodeURIComponent(selectedAudio)}`);
      const data = await res.json();
      if (!data.success || !data.duration_seconds) {
        alert('Could not fetch audio duration: ' + (data.error || 'Unknown error'));
        return;
      }

      const audioDuration = data.duration_seconds;
      const N = points.length;
      const timePerPoint = audioDuration / N;
      const transTime = Math.max(0.5, Math.round((timePerPoint * 0.55) * 10) / 10);
      const holdTime = Math.max(0.2, Math.round((timePerPoint * 0.45) * 10) / 10);

      points.forEach(p => {
        p.transition_duration = transTime;
        p.hold_duration = holdTime;
      });

      if (activePointId !== null) {
        const activeP = points.find(p => p.id === activePointId);
        if (activeP) {
          const transEl = document.getElementById('point-trans-sec');
          const holdEl = document.getElementById('point-hold-sec');
          if (transEl) transEl.value = activeP.transition_duration;
          if (holdEl) holdEl.value = activeP.hold_duration;
        }
      }

      updatePointsList();
      const totalCalcTime = points.reduce((sum, p) => sum + p.transition_duration + p.hold_duration, 0).toFixed(1);
      alert(`⚡ Auto-Synced ${N} keyframes to audio duration (${audioDuration}s).\nEach point: ${transTime}s transition + ${holdTime}s hold (Total: ${totalCalcTime}s).`);

    } catch (err) {
      console.error(err);
      alert('Failed to auto-sync audio duration.');
    }
  }

  window.autoSyncAudio = autoSyncAudio;

  const autoSyncBtn = document.getElementById('btn-auto-sync-audio');
  if (autoSyncBtn) {
    autoSyncBtn.addEventListener('click', autoSyncAudio);
  }

  // One-Click Project ZIP Export
  const btnExportZip = document.getElementById('btn-export-zip');
  if (btnExportZip) {
    btnExportZip.addEventListener('click', triggerProjectZipExport);
  }

  function triggerProjectZipExport() {
    if (points.length === 0) {
      alert('Please add keyframe points before exporting a project ZIP backup!');
      return;
    }

    const defaultName = (imageFilename || 'project').split('.')[0] + '_backup';
    const projectName = prompt('Enter a name for this project backup ZIP:', defaultName);
    if (!projectName) return;

    const audioSelect = document.getElementById('export-audio-track');
    const selectedAudio = audioSelect ? audioSelect.value : 'none';

    const payload = {
      project_name: projectName,
      filename: imageFilename,
      points: points,
      audio_filename: selectedAudio,
      video_filename: window.lastRenderedVideoFilename || null
    };

    fetch('/api/export_project_zip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
      if (data.success && data.zip_url) {
        const a = document.createElement('a');
        a.href = data.zip_url;
        a.download = data.zip_filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        alert(`📦 Project Backup ZIP created successfully!\nDownloaded: ${data.zip_filename}`);
      } else {
        alert('ZIP Export Error: ' + (data.error || 'Unknown error'));
      }
    })
    .catch(err => {
      console.error(err);
      alert('Error exporting project ZIP backup.');
    });
  }

  let isExporting = false;

  function triggerExport() {
    if (isExporting) return;
    if (points.length === 0) {
      alert('Please add points before exporting an MP4 video!');
      return;
    }
    isExporting = true;

    const exportBtn = document.getElementById('btn-trigger-mp4-export');
    if (exportBtn) {
      exportBtn.disabled = true;
      exportBtn.innerHTML = '<span class="spinner"></span> Rendering MP4 Video...';
    }

    const audioSelect = document.getElementById('export-audio-track');
    const selectedAudio = audioSelect ? audioSelect.value : 'none';

    const payload = {
      filename: imageFilename,
      points: points,
      resolution: document.getElementById('export-resolution') ? document.getElementById('export-resolution').value : '1080p',
      fps: document.getElementById('export-fps') ? document.getElementById('export-fps').value : 30,
      render_labels: document.getElementById('export-render-labels') ? document.getElementById('export-render-labels').checked : true,
      audio_filename: selectedAudio
    };

    fetch('/api/generate_mp4', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(async res => {
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Server Error (${res.status}): ${text.slice(0, 150)}`);
      }
      return res.json();
    })
    .then(data => {
      if (exportBtn) {
        exportBtn.disabled = false;
        exportBtn.textContent = 'Render & Download MP4 Video';
      }

      if (data.success) {
        window.lastRenderedVideoFilename = data.filename;
        const player = document.getElementById('video-preview-player');
        if (player) {
          player.src = data.video_url + '?t=' + Date.now();
          player.addEventListener('loadedmetadata', () => {
            player.currentTime = 0.01;
          }, { once: true });
          player.load();
          const playPromise = player.play();
          if (playPromise !== undefined) {
            playPromise.catch(e => {
              console.log('Autoplay deferred for user click:', e);
            });
          }
        }

        const downloadBtn = document.getElementById('btn-download-video-file');
        if (downloadBtn) {
          downloadBtn.href = data.video_url;
          downloadBtn.download = data.filename;
        }

        const statsEl = document.getElementById('video-info-stats');
        if (statsEl) {
          statsEl.textContent = `Duration: ${data.duration_seconds}s | Frames: ${data.total_frames}`;
        }

        openModal('modal-video-export');
      } else {
        alert('Video Generation Error: ' + data.error);
      }
    })
    .catch(err => {
      if (exportBtn) {
        exportBtn.disabled = false;
        exportBtn.textContent = 'Render & Download MP4 Video';
      }
      alert('Failed to generate video: ' + err);
    })
    .finally(() => {
      isExporting = false;
    });
  }

  window.triggerExport = triggerExport;

  const exportBtn1 = document.getElementById('btn-trigger-mp4-export');
  if (exportBtn1) exportBtn1.addEventListener('click', triggerExport);
  const exportBtn2 = document.getElementById('btn-export-mp4');
  if (exportBtn2) exportBtn2.addEventListener('click', triggerExport);

  // Modal Helpers
  window.openModal = function(id) {
    document.getElementById(id).classList.add('show');
  };

  window.closeModal = function(id) {
    document.getElementById(id).classList.remove('show');
  };

  // Load Initial Image (check query param or sessionStorage)
  const urlParams = new URLSearchParams(window.location.search);
  const targetImage = urlParams.get('image');
  const savedUrl = sessionStorage.getItem('zoompan_active_url');
  const savedImage = sessionStorage.getItem('zoompan_active_image');

  if (targetImage) {
    loadInitialImage('/static/uploads/' + targetImage, targetImage);
  } else if (savedUrl && savedImage) {
    loadInitialImage(savedUrl, savedImage);
  }
});
