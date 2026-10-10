/**
 * JAVASCRIPT EFFECTS STUDIO // Frontend UI Controller
 * Handles user interactions, preset synchronization, capture, and recording.
 */

document.addEventListener('DOMContentLoaded', async () => {
  const engine = new EffectsEngine('studioCanvas');

  // DOM Elements
  const mediaInput = document.getElementById('mediaInput');
  const dropzone = document.getElementById('dropzone');
  const mediaStatusText = document.getElementById('mediaStatusText');
  const resolutionDisplay = document.getElementById('resolutionDisplay');
  const fpsDisplay = document.getElementById('fpsDisplay');

  // Video Controls
  const videoControlsCard = document.getElementById('videoControlsCard');
  const btnPlayPause = document.getElementById('btnPlayPause');
  const videoSeekBar = document.getElementById('videoSeekBar');
  const videoTimeDisplay = document.getElementById('videoTimeDisplay');
  const btnMute = document.getElementById('btnMute');
  const btnLoop = document.getElementById('btnLoop');

  // Aspect Ratio & Sizing
  const aspectSelector = document.getElementById('aspectSelector');
  const fitModeSelector = document.getElementById('fitModeSelector');

  // Master FX & Grading
  const masterOpacitySlider = document.getElementById('masterOpacity');
  const masterOpacityVal = document.getElementById('masterOpacityVal');
  const blendModeSelector = document.getElementById('blendMode');
  const brightnessSlider = document.getElementById('brightness');
  const contrastSlider = document.getElementById('contrast');
  const saturationSlider = document.getElementById('saturation');
  const hueSlider = document.getElementById('hue');

  // Preset Selector
  const presetSelector = document.getElementById('presetSelector');
  const btnSavePreset = document.getElementById('btnSavePreset');
  const btnLoadPreset = document.getElementById('btnLoadPreset');
  const presetFileInput = document.getElementById('presetFileInput');

  // Capture & Recording
  const btnSnapshot = document.getElementById('btnSnapshot');
  const btnRecord = document.getElementById('btnRecord');
  const recDurationSelector = document.getElementById('recDuration');
  const recTimer = document.getElementById('recTimer');
  const recTimerText = document.getElementById('recTimerText');
  const exportsStatus = document.getElementById('exportsStatus');

  let defaultPresets = [];
  let recordInterval = null;
  let recordTimeout = null;

  // 1. Fetch Default Presets from JSON
  try {
    const res = await fetch('/static/effects/presets/default-presets.json');
    if (res.ok) {
      const data = await res.json();
      defaultPresets = data.presets || [];
      populatePresets(defaultPresets);
    }
  } catch (err) {
    console.warn('Could not load preset JSON:', err);
  }

  // 1b. Fetch and populate Sci-Fi Studio Videos
  try {
    const vRes = await fetch('/api/effects/videos');
    if (vRes.ok) {
      const vData = await vRes.json();
      if (vData.videos && vData.videos.length > 0) {
        populateVideoButtons(vData.videos);
        const defaultVid = vData.videos.find(v => v.filename === 'kepler.mp4') || vData.videos[0];
        if (defaultVid && !engine.mediaLoaded) {
          loadVideoMedia(defaultVid.url, defaultVid.filename);
        }
      }
    }
  } catch (err) {
    console.warn('Could not load studio videos:', err);
  }

  function populateVideoButtons(videos) {
    const container = document.getElementById('studioVideoBtns');
    if (!container) return;
    container.innerHTML = '';
    videos.forEach(v => {
      const btn = document.createElement('button');
      btn.className = 'btn-sample-video';
      btn.textContent = `🎬 ${v.filename}`;
      btn.title = `${v.size_mb} MB (${v.duration_sec}s)`;
      btn.style.cssText = 'background: rgba(0, 240, 255, 0.15); border: 1px solid #00f0ff; color: #fff; padding: 5px 10px; font-size: 0.75rem; border-radius: 4px; cursor: pointer; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; max-width: 100%;';
      btn.addEventListener('click', () => {
        loadVideoMedia(v.url, v.filename);
      });
      container.appendChild(btn);
    });
  }

  function loadVideoMedia(url, name) {
    engine.loadVideo(url).then(vid => {
      mediaStatusText.textContent = `VIDEO: ${name} (${vid.videoWidth}×${vid.videoHeight})`;
      videoControlsCard.style.display = 'block';
      btnPlayPause.textContent = '⏸';
      aspectSelector.value = 'auto_match';
      engine.autoMatchMediaSize = true;
      engine.matchMediaSize();
      updateResolutionDisplay();
    });
  }

  function populatePresets(presets) {
    presetSelector.innerHTML = '<option value="">-- Choose Preset --</option>';
    presets.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.name;
      presetSelector.appendChild(opt);
    });
  }

  // Preset Selection Change
  presetSelector.addEventListener('change', () => {
    const pId = presetSelector.value;
    const preset = defaultPresets.find(p => p.id === pId);
    if (preset) {
      engine.loadPreset(preset);
      syncUIFromEngine();
    }
  });

  // 2. Sync UI controls with Engine State
  function syncUIFromEngine() {
    masterOpacitySlider.value = Math.round(engine.masterOpacity * 100);
    masterOpacityVal.textContent = `${masterOpacitySlider.value}%`;
    blendModeSelector.value = engine.blendMode;

    brightnessSlider.value = engine.filters.brightness;
    document.getElementById('brightnessVal').textContent = `${engine.filters.brightness}%`;

    contrastSlider.value = engine.filters.contrast;
    document.getElementById('contrastVal').textContent = `${engine.filters.contrast}%`;

    saturationSlider.value = engine.filters.saturation;
    document.getElementById('saturationVal').textContent = `${engine.filters.saturation}%`;

    hueSlider.value = engine.filters.hue;
    document.getElementById('hueVal').textContent = `${engine.filters.hue}°`;

    // Sync each individual effect
    for (const [key, conf] of Object.entries(engine.effects)) {
      const itemEl = document.getElementById(`effect-${key}`);
      if (!itemEl) continue;

      const checkbox = itemEl.querySelector('.effect-checkbox');
      const opacitySlider = itemEl.querySelector('.effect-opacity');
      const opacityVal = itemEl.querySelector('.effect-opacity-val');
      const colorPicker = itemEl.querySelector('.color-picker');

      if (checkbox) checkbox.checked = conf.enabled;
      if (opacitySlider) opacitySlider.value = Math.round(conf.opacity * 100);
      if (opacityVal) opacityVal.textContent = `${opacitySlider.value}%`;
      if (colorPicker && conf.color) colorPicker.value = conf.color;

      itemEl.classList.toggle('active', conf.enabled);
    }
  }

  // 3. Bind Individual Effects Controls
  for (const key of Object.keys(engine.effects)) {
    const itemEl = document.getElementById(`effect-${key}`);
    if (!itemEl) continue;

    const checkbox = itemEl.querySelector('.effect-checkbox');
    const opacitySlider = itemEl.querySelector('.effect-opacity');
    const opacityVal = itemEl.querySelector('.effect-opacity-val');
    const colorPicker = itemEl.querySelector('.color-picker');

    if (checkbox) {
      checkbox.addEventListener('change', () => {
        engine.effects[key].enabled = checkbox.checked;
        itemEl.classList.toggle('active', checkbox.checked);
      });
    }

    if (opacitySlider) {
      opacitySlider.addEventListener('input', () => {
        const val = parseFloat(opacitySlider.value) / 100;
        engine.effects[key].opacity = val;
        if (opacityVal) opacityVal.textContent = `${opacitySlider.value}%`;
        // Auto-enable if opacity moved from zero
        if (val > 0 && !engine.effects[key].enabled) {
          engine.effects[key].enabled = true;
          if (checkbox) checkbox.checked = true;
          itemEl.classList.add('active');
        }
      });
    }

    if (colorPicker) {
      colorPicker.addEventListener('input', () => {
        engine.effects[key].color = colorPicker.value;
      });
    }
  }

  // 4. Master Controls
  masterOpacitySlider.addEventListener('input', () => {
    engine.masterOpacity = parseFloat(masterOpacitySlider.value) / 100;
    masterOpacityVal.textContent = `${masterOpacitySlider.value}%`;
  });

  blendModeSelector.addEventListener('change', () => {
    engine.blendMode = blendModeSelector.value;
  });

  brightnessSlider.addEventListener('input', () => {
    engine.filters.brightness = parseInt(brightnessSlider.value);
    document.getElementById('brightnessVal').textContent = `${brightnessSlider.value}%`;
  });

  contrastSlider.addEventListener('input', () => {
    engine.filters.contrast = parseInt(contrastSlider.value);
    document.getElementById('contrastVal').textContent = `${contrastSlider.value}%`;
  });

  saturationSlider.addEventListener('input', () => {
    engine.filters.saturation = parseInt(saturationSlider.value);
    document.getElementById('saturationVal').textContent = `${saturationSlider.value}%`;
  });

  hueSlider.addEventListener('input', () => {
    engine.filters.hue = parseInt(hueSlider.value);
    document.getElementById('hueVal').textContent = `${hueSlider.value}°`;
  });

  // Fit Mode (Contain = zero distortion, Cover, Fill)
  fitModeSelector.addEventListener('change', () => {
    engine.fitMode = fitModeSelector.value;
  });

  // Aspect Ratio Selection
  function updateResolutionDisplay() {
    if (engine.autoMatchMediaSize) {
      resolutionDisplay.textContent = `${engine.canvas.width} × ${engine.canvas.height} (1:1 Matched)`;
    } else {
      resolutionDisplay.textContent = `${engine.canvas.width} × ${engine.canvas.height}`;
    }
  }

  aspectSelector.addEventListener('change', () => {
    const choice = aspectSelector.value;
    switch (choice) {
      case 'auto_match':
        engine.autoMatchMediaSize = true;
        engine.matchMediaSize();
        break;
      case 'portrait_9_16':
        engine.autoMatchMediaSize = false;
        engine.setResolution(512, 768);
        break;
      case 'landscape_16_9':
        engine.autoMatchMediaSize = false;
        engine.setResolution(768, 512);
        break;
      case 'square_1_1':
        engine.autoMatchMediaSize = false;
        engine.setResolution(768, 768);
        break;
      case 'portrait_4_5':
        engine.autoMatchMediaSize = false;
        engine.setResolution(640, 800);
        break;
      case 'fhd_portrait':
        engine.autoMatchMediaSize = false;
        engine.setResolution(1080, 1920);
        break;
      case 'fhd_landscape':
        engine.autoMatchMediaSize = false;
        engine.setResolution(1920, 1080);
        break;
    }
    updateResolutionDisplay();
  });

  // Dedicated Snap Canvas to Media Size Button
  const btnMatchMedia = document.getElementById('btnMatchMedia');
  if (btnMatchMedia) {
    btnMatchMedia.addEventListener('click', () => {
      aspectSelector.value = 'auto_match';
      engine.autoMatchMediaSize = true;
      const dims = engine.matchMediaSize();
      if (dims) {
        updateResolutionDisplay();
      }
    });
  }

  // 5. Media Loading (Image & Video)
  function handleFile(file) {
    if (!file) return;
    const url = URL.createObjectURL(file);

    if (file.type.startsWith('image/')) {
      engine.loadImage(url).then((img) => {
        mediaStatusText.textContent = `IMG: ${file.name} (${img.naturalWidth}×${img.naturalHeight})`;
        videoControlsCard.style.display = 'none';
        updateResolutionDisplay();
      }).catch(err => alert('Failed to load image: ' + err));
    } else if (file.type.startsWith('video/')) {
      engine.loadVideo(url).then((vid) => {
        mediaStatusText.textContent = `VID: ${file.name} (${vid.videoWidth}×${vid.videoHeight})`;
        videoControlsCard.style.display = 'block';
        btnPlayPause.textContent = '⏸';
        updateResolutionDisplay();
      }).catch(err => alert('Failed to load video: ' + err));
    } else {
      alert('Unsupported file type. Please upload an image or MP4/WebM video.');
    }
  }

  mediaInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  });

  // Drag & Drop
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });
  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });
  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  });

  // Sample Buttons
  document.querySelectorAll('.btn-sample').forEach(btn => {
    btn.addEventListener('click', () => {
      const sampleType = btn.dataset.sample;
      let path = '';
      if (sampleType === 'avatar') path = '/static/effects/samples/sample-avatar.jpg';
      if (sampleType === 'sentinel') path = '/static/effects/samples/sample-sentinel.jpg';
      if (sampleType === 'crystals') path = '/static/effects/samples/sample-crystals.jpg';
      if (sampleType === 'video') path = '/static/effects/samples/sample-video.mp4';

      if (path.endsWith('.mp4')) {
        engine.loadVideo(path).then(vid => {
          mediaStatusText.textContent = `SAMPLE VIDEO (${vid.videoWidth}×${vid.videoHeight})`;
          videoControlsCard.style.display = 'block';
          btnPlayPause.textContent = '⏸';
          updateResolutionDisplay();
        });
      } else {
        engine.loadImage(path).then(img => {
          mediaStatusText.textContent = `SAMPLE IMAGE (${img.naturalWidth}×${img.naturalHeight})`;
          videoControlsCard.style.display = 'none';
          updateResolutionDisplay();
        });
      }
    });
  });

  // 6. Video Player Controls
  btnPlayPause.addEventListener('click', () => {
    if (!engine.videoElement) return;
    if (engine.videoElement.paused) {
      engine.videoElement.play();
      btnPlayPause.textContent = '⏸';
    } else {
      engine.videoElement.pause();
      btnPlayPause.textContent = '▶';
    }
  });

  btnMute.addEventListener('click', () => {
    if (!engine.videoElement) return;
    engine.videoElement.muted = !engine.videoElement.muted;
    btnMute.textContent = engine.videoElement.muted ? '🔇' : '🔊';
  });

  btnLoop.addEventListener('click', () => {
    if (!engine.videoElement) return;
    engine.videoElement.loop = !engine.videoElement.loop;
    btnLoop.style.borderColor = engine.videoElement.loop ? 'var(--cyan-primary)' : 'var(--border-dim)';
  });

  videoSeekBar.addEventListener('input', () => {
    if (!engine.videoElement || !engine.videoElement.duration) return;
    const seekTo = (videoSeekBar.value / 100) * engine.videoElement.duration;
    engine.videoElement.currentTime = seekTo;
  });

  // Real-time video seeker update loop
  setInterval(() => {
    if (engine.videoElement && engine.videoElement.duration) {
      const cur = engine.videoElement.currentTime;
      const dur = engine.videoElement.duration;
      videoSeekBar.value = Math.round((cur / dur) * 100);
      const curStr = formatTime(cur);
      const durStr = formatTime(dur);
      videoTimeDisplay.textContent = `${curStr} / ${durStr}`;
    }
    fpsDisplay.textContent = `${engine.fps} FPS`;
  }, 250);

  function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }

  // 7. Save & Load Custom Preset JSON
  btnSavePreset.addEventListener('click', () => {
    const name = prompt('Enter a name for this custom preset:', 'My Custom FX');
    if (!name) return;
    const preset = engine.exportPreset(name);
    const blob = new Blob([JSON.stringify(preset, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${name.toLowerCase().replace(/\s+/g, '_')}_preset.json`;
    a.click();
    URL.revokeObjectURL(url);
  });

  btnLoadPreset.addEventListener('click', () => {
    presetFileInput.click();
  });

  presetFileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const preset = JSON.parse(event.target.result);
          engine.loadPreset(preset);
          syncUIFromEngine();
          alert(`Preset '${preset.name || 'Custom'}' loaded successfully!`);
        } catch (err) {
          alert('Invalid preset JSON file.');
        }
      };
      reader.readAsText(e.target.files[0]);
    }
  });

  // 8. Capture Snapshot (PNG)
  btnSnapshot.addEventListener('click', async () => {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `snapshot_${timestamp}.png`;
    
    // Download via browser
    const blob = await engine.captureImage(filename);

    // Also auto-save to server exports folder
    if (blob) {
      saveExportToServer(blob, filename, 'image/png');
    }
  });

  // 9. Record Video (WebM / MP4)
  btnRecord.addEventListener('click', () => {
    if (!engine.isRecording) {
      // Start Recording
      const durationSec = parseInt(recDurationSelector.value);
      engine.startRecording();

      btnRecord.classList.add('recording');
      btnRecord.innerHTML = '<span>⏹</span> STOP RECORDING';
      recTimer.classList.add('active');

      const startTime = performance.now();
      recordInterval = setInterval(() => {
        const elapsed = (performance.now() - startTime) / 1000;
        recTimerText.textContent = `● REC ${elapsed.toFixed(1)}s`;
      }, 100);

      // Auto stop if duration is set (> 0)
      if (durationSec > 0) {
        recordTimeout = setTimeout(() => {
          if (engine.isRecording) {
            stopVideoRecording();
          }
        }, durationSec * 1000);
      }
    } else {
      // Manual Stop Recording
      stopVideoRecording();
    }
  });

  function stopVideoRecording() {
    clearInterval(recordInterval);
    clearTimeout(recordTimeout);
    engine.stopRecording();

    btnRecord.classList.remove('recording');
    btnRecord.innerHTML = '<span>⏺</span> RECORD VIDEO';
    recTimer.classList.remove('active');
  }

  // Handle Recording Completion
  engine.onRecordComplete = (blob, mimeType) => {
    const ext = mimeType.includes('mp4') ? 'mp4' : 'webm';
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `recording_${timestamp}.${ext}`;

    // Browser Download
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1500);

    // Save copy to Flask backend exports folder
    saveExportToServer(blob, filename, mimeType);
  };

  async function saveExportToServer(blob, filename, mimeType) {
    const formData = new FormData();
    formData.append('file', blob, filename);
    formData.append('mimeType', mimeType);

    try {
      exportsStatus.textContent = 'Saving export...';
      const res = await fetch('/api/save-export', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        exportsStatus.innerHTML = `Saved: <a href="${data.url}" target="_blank" style="color:var(--cyan-primary);">${filename}</a>`;
      }
    } catch (err) {
      console.warn('Failed to save to server exports:', err);
      exportsStatus.textContent = 'Downloaded locally.';
    }
  }

  // Initial UI state synchronization & sample load
  syncUIFromEngine();

  // Automatically load the first sample avatar so user has visual feedback right away!
  engine.loadImage('/static/effects/samples/sample-avatar.jpg').then(img => {
    mediaStatusText.textContent = `READY // Sample Avatar (${img.naturalWidth}×${img.naturalHeight})`;
    updateResolutionDisplay();
  }).catch(() => {
    updateResolutionDisplay();
  });
});
