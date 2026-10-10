/**
 * JAVASCRIPT EFFECTS STUDIO // Canvas Visual FX & Media Recorder Engine
 * High-performance, multi-layered visual overlays for images and videos with zero distortion
 * and automatic 1:1 media size matching.
 */

class EffectsEngine {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) {
      throw new Error(`Canvas with ID '${canvasId}' not found.`);
    }
    this.ctx = this.canvas.getContext('2d');

    // Media State
    this.mediaType = null; // 'image' | 'video' | null
    this.imageElement = null;
    this.videoElement = null;
    this.mediaLoaded = false;
    this.fitMode = 'contain'; // 'contain' (no distortion) | 'cover' | 'fill'
    this.autoMatchMediaSize = true; // Automatically match natural media size by default!
    this.canvasResolution = { width: 768, height: 768 };
    this.customOverlayText = 'STAACOR HOLONET // LIVE FEED';

    // Animation & Clock
    this.isPlaying = true;
    this.time = 0;
    this.lastTimestamp = performance.now();
    this.animationFrameId = null;
    this.fps = 60;
    this.frameCount = 0;
    this.lastFpsUpdate = performance.now();

    // Master Grading & FX Settings
    this.masterOpacity = 1.0;
    this.blendMode = 'source-over';
    this.filters = {
      brightness: 100,
      contrast: 100,
      saturation: 100,
      hue: 0
    };

    // Effects Registry (Each has its own enabled flag & individual opacity slider)
    this.effects = {
      sparkles: { enabled: false, opacity: 0.85, color: '#ffdf00', density: 45 },
      bokeh: { enabled: false, opacity: 0.55, color: '#ff66cc', count: 25 },
      hearts: { enabled: false, opacity: 0.75, mode: 'hearts', speed: 1.0 },
      rain: { enabled: false, opacity: 0.7, speed: 1.2, count: 120 },
      snow: { enabled: false, opacity: 0.75, count: 80 },
      dust: { enabled: true, opacity: 0.7, color: '#00f0ff', count: 70 },
      beams: { enabled: false, opacity: 0.8, color: '#00f0ff' },
      hologram: { enabled: false, opacity: 0.8, color: '#00f0ff' },
      crystals: { enabled: false, opacity: 0.75, color: '#00f0ff' },
      crosshair: { enabled: false, opacity: 0.85, color: '#00ffa3' },
      suns: { enabled: false, opacity: 0.8 },
      vhs: { enabled: false, opacity: 0.9 },
      scanlines: { enabled: false, opacity: 0.45, glitch: 0.05 },
      thermal: { enabled: false, opacity: 0.65 },
      broadcast: { enabled: false, opacity: 0.85, text: 'LIVE BROADCAST' },
      vignette: { enabled: false, opacity: 0.5 },
      cybergrid: { enabled: false, opacity: 0.65, color: '#ff007f' }
    };

    // Particle Pools
    this.particlePools = {
      sparkles: [],
      bokeh: [],
      hearts: [],
      rain: [],
      snow: [],
      dust: []
    };

    this.initParticlePools();

    // Recording State
    this.mediaRecorder = null;
    this.recordedChunks = [];
    this.isRecording = false;
    this.recordStartTime = 0;
    this.onRecordProgress = null;
    this.onRecordComplete = null;

    // Default resolution
    this.setResolution(768, 768);
    this.start();
  }

  initParticlePools() {
    // Sparkles Pool
    this.particlePools.sparkles = [];
    for (let i = 0; i < 70; i++) {
      this.particlePools.sparkles.push({
        x: Math.random(),
        y: Math.random(),
        size: Math.random() * 12 + 6,
        rot: Math.random() * Math.PI,
        rotSpeed: (Math.random() - 0.5) * 0.05,
        twinkleSpeed: Math.random() * 0.08 + 0.03,
        twinkleOffset: Math.random() * Math.PI * 2,
        alpha: Math.random() * 0.8 + 0.2
      });
    }

    // Bokeh Pool
    this.particlePools.bokeh = [];
    for (let i = 0; i < 40; i++) {
      this.particlePools.bokeh.push({
        x: Math.random(),
        y: Math.random(),
        radius: Math.random() * 45 + 20,
        vx: (Math.random() - 0.5) * 0.0006,
        vy: (Math.random() - 0.5) * 0.0006 - 0.0002,
        pulseSpeed: Math.random() * 0.03 + 0.01,
        pulseOffset: Math.random() * Math.PI * 2,
        hueShift: Math.random() * 40 - 20
      });
    }

    // Hearts & Embers Pool
    this.particlePools.hearts = [];
    for (let i = 0; i < 50; i++) {
      this.particlePools.hearts.push({
        x: Math.random(),
        y: Math.random(),
        size: Math.random() * 16 + 8,
        vy: -(Math.random() * 0.0018 + 0.0008),
        wobbleSpeed: Math.random() * 0.06 + 0.02,
        wobbleOffset: Math.random() * Math.PI * 2,
        wobbleAmp: Math.random() * 0.002 + 0.001,
        rot: (Math.random() - 0.5) * 0.4
      });
    }

    // Rain Pool
    this.particlePools.rain = [];
    for (let i = 0; i < 150; i++) {
      this.particlePools.rain.push({
        x: Math.random() * 1.3 - 0.15,
        y: Math.random(),
        length: Math.random() * 25 + 15,
        vy: Math.random() * 0.025 + 0.02,
        vx: 0.003,
        alpha: Math.random() * 0.6 + 0.4
      });
    }

    // Snow Pool
    this.particlePools.snow = [];
    for (let i = 0; i < 100; i++) {
      this.particlePools.snow.push({
        x: Math.random(),
        y: Math.random(),
        radius: Math.random() * 3.5 + 1.2,
        vy: Math.random() * 0.0015 + 0.0006,
        driftSpeed: Math.random() * 0.03 + 0.01,
        driftOffset: Math.random() * Math.PI * 2,
        alpha: Math.random() * 0.7 + 0.3
      });
    }

    // Atmospheric Dust Pool (Staacor)
    this.particlePools.dust = [];
    for (let i = 0; i < 80; i++) {
      this.particlePools.dust.push({
        x: Math.random(),
        y: Math.random(),
        vx: (Math.random() - 0.5) * 0.0008,
        vy: (Math.random() - 0.5) * 0.0008 - 0.0003,
        size: Math.random() * 2.8 + 0.8,
        alpha: Math.random() * 0.7 + 0.3,
        pulseSpeed: Math.random() * 0.05 + 0.02
      });
    }
  }

  setResolution(width, height) {
    this.canvasResolution = { width: Math.round(width), height: Math.round(height) };
    this.canvas.width = Math.round(width);
    this.canvas.height = Math.round(height);
  }

  // Automatically match the exact natural dimensions of the loaded media (1:1 pixel match)
  matchMediaSize() {
    if (this.mediaType === 'image' && this.imageElement && this.imageElement.naturalWidth > 0) {
      const w = this.imageElement.naturalWidth;
      const h = this.imageElement.naturalHeight;
      this.setResolution(w, h);
      return { width: w, height: h };
    } else if (this.mediaType === 'video' && this.videoElement && this.videoElement.videoWidth > 0) {
      const w = this.videoElement.videoWidth;
      const h = this.videoElement.videoHeight;
      this.setResolution(w, h);
      return { width: w, height: h };
    }
    return null;
  }

  // Load Image File or URL
  loadImage(source) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        this.imageElement = img;
        this.videoElement = null;
        this.mediaType = 'image';
        this.mediaLoaded = true;
        if (this.autoMatchMediaSize && img.naturalWidth > 0) {
          this.setResolution(img.naturalWidth, img.naturalHeight);
        }
        resolve(img);
      };
      img.onerror = (err) => reject(err);
      img.src = source;
    });
  }

  // Load Video File or URL
  loadVideo(source) {
    return new Promise((resolve, reject) => {
      const video = document.createElement('video');
      video.crossOrigin = 'anonymous';
      video.loop = true;
      video.muted = true;
      video.playsInline = true;
      video.autoplay = true;

      video.onloadedmetadata = () => {
        this.videoElement = video;
        this.imageElement = null;
        this.mediaType = 'video';
        this.mediaLoaded = true;
        if (this.autoMatchMediaSize && video.videoWidth > 0) {
          this.setResolution(video.videoWidth, video.videoHeight);
        }
        video.play().then(() => resolve(video)).catch(() => resolve(video));
      };
      video.onerror = (err) => reject(err);
      video.src = source;
      video.load();
    });
  }

  // Load Preset
  loadPreset(presetData) {
    if (presetData.masterOpacity !== undefined) {
      this.masterOpacity = presetData.masterOpacity;
    }
    if (presetData.blendMode) {
      this.blendMode = presetData.blendMode;
    }
    if (presetData.filters) {
      this.filters = { ...this.filters, ...presetData.filters };
    }
    if (presetData.effects) {
      for (const [key, val] of Object.entries(presetData.effects)) {
        if (this.effects[key]) {
          this.effects[key] = { ...this.effects[key], ...val };
        }
      }
    }
  }

  // Export current settings as JSON
  exportPreset(name = 'Custom Preset') {
    return {
      name,
      masterOpacity: this.masterOpacity,
      blendMode: this.blendMode,
      filters: { ...this.filters },
      effects: JSON.parse(JSON.stringify(this.effects))
    };
  }

  start() {
    if (this.animationFrameId) return;
    this.isPlaying = true;
    const loop = (timestamp) => {
      const dt = (timestamp - this.lastTimestamp) / 1000;
      this.lastTimestamp = timestamp;

      // Update FPS counter
      this.frameCount++;
      if (timestamp - this.lastFpsUpdate >= 1000) {
        this.fps = Math.round((this.frameCount * 1000) / (timestamp - this.lastFpsUpdate));
        this.frameCount = 0;
        this.lastFpsUpdate = timestamp;
      }

      this.time += Math.min(dt, 0.1);
      this.render();

      this.animationFrameId = requestAnimationFrame(loop);
    };
    this.animationFrameId = requestAnimationFrame(loop);
  }

  stop() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    this.isPlaying = false;
  }

  // Primary Render Pipeline
  render() {
    const w = this.canvas.width;
    const h = this.canvas.height;
    const ctx = this.ctx;
    const scale = Math.max(0.6, Math.min(w, h) / 768);

    // 1. Clear background
    ctx.save();
    ctx.clearRect(0, 0, w, h);

    // Default dark cinematic background gradient
    const bgGrad = ctx.createLinearGradient(0, 0, 0, h);
    bgGrad.addColorStop(0, '#0a0e17');
    bgGrad.addColorStop(1, '#030509');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, w, h);

    // 2. Draw media layer (zero distortion containing / cover / 1:1 match)
    this.drawMediaLayer(ctx, w, h);

    // 3. Render Active Overlays (with individual opacities & blend mode)
    ctx.globalCompositeOperation = this.blendMode || 'source-over';

    // A. Phone-Style Ambient & Atmospheric Overlays
    if (this.effects.dust.enabled) this.renderAtmosphericDust(ctx, w, h, scale, this.effects.dust);
    if (this.effects.bokeh.enabled) this.renderBokeh(ctx, w, h, scale, this.effects.bokeh);
    if (this.effects.hearts.enabled) this.renderHeartsEmbers(ctx, w, h, scale, this.effects.hearts);
    if (this.effects.snow.enabled) this.renderSnow(ctx, w, h, scale, this.effects.snow);
    if (this.effects.rain.enabled) this.renderRain(ctx, w, h, scale, this.effects.rain);
    if (this.effects.sparkles.enabled) this.renderSparkles(ctx, w, h, scale, this.effects.sparkles);

    // B. Staacor Sci-Fi & Holographic FX
    if (this.effects.beams.enabled) this.renderSentinelBeams(ctx, w, h, scale, this.effects.beams);
    if (this.effects.hologram.enabled) this.renderHolographicRings(ctx, w, h, scale, this.effects.hologram);
    if (this.effects.crystals.enabled) this.renderCrystalShield(ctx, w, h, scale, this.effects.crystals);
    if (this.effects.suns.enabled) this.renderCelestialSuns(ctx, w, h, scale, this.effects.suns);
    if (this.effects.cybergrid.enabled) this.renderCyberGrid(ctx, w, h, scale, this.effects.cybergrid);

    // Switch back to source-over for HUD and Screen Overlays
    ctx.globalCompositeOperation = 'source-over';

    // C. Sensor, Screen & Camcorder Overlays
    if (this.effects.crosshair.enabled) this.renderCrosshairHUD(ctx, w, h, scale, this.effects.crosshair);
    if (this.effects.thermal.enabled) this.renderThermalMode(ctx, w, h, scale, this.effects.thermal);
    if (this.effects.scanlines.enabled) this.renderScanlines(ctx, w, h, scale, this.effects.scanlines);
    if (this.effects.vhs.enabled) this.renderRetroVHS(ctx, w, h, scale, this.effects.vhs);
    if (this.effects.broadcast.enabled) this.renderBroadcastHUD(ctx, w, h, scale, this.effects.broadcast);
    if (this.effects.vignette.enabled) this.renderVignette(ctx, w, h, scale, this.effects.vignette);

    ctx.restore();
  }

  // Media Drawing with strict zero-distortion aspect preservation
  drawMediaLayer(ctx, canvasW, canvasH) {
    let mediaObj = null;
    let naturalW = 0;
    let naturalH = 0;

    if (this.mediaType === 'image' && this.imageElement && this.imageElement.complete) {
      mediaObj = this.imageElement;
      naturalW = mediaObj.naturalWidth;
      naturalH = mediaObj.naturalHeight;
    } else if (this.mediaType === 'video' && this.videoElement && this.videoElement.readyState >= 2) {
      mediaObj = this.videoElement;
      naturalW = mediaObj.videoWidth;
      naturalH = mediaObj.videoHeight;
    }

    if (!mediaObj || naturalW <= 0 || naturalH <= 0) {
      // Render subtle grid test pattern if no media loaded
      ctx.save();
      ctx.strokeStyle = 'rgba(0, 240, 255, 0.08)';
      ctx.lineWidth = 1;
      const step = 40;
      for (let x = 0; x < canvasW; x += step) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvasH); ctx.stroke();
      }
      for (let y = 0; y < canvasH; y += step) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvasW, y); ctx.stroke();
      }
      ctx.font = '600 16px "Space Mono", monospace';
      ctx.fillStyle = 'rgba(0, 240, 255, 0.35)';
      ctx.textAlign = 'center';
      ctx.fillText('NO MEDIA LOADED // DROP IMAGE OR VIDEO HERE', canvasW / 2, canvasH / 2);
      ctx.restore();
      return;
    }

    // Apply color grading filters
    ctx.save();
    ctx.filter = `brightness(${this.filters.brightness}%) contrast(${this.filters.contrast}%) saturate(${this.filters.saturation}%) hue-rotate(${this.filters.hue}deg)`;

    // If canvas matches media dimensions exactly (1:1)
    if (canvasW === naturalW && canvasH === naturalH) {
      ctx.drawImage(mediaObj, 0, 0, canvasW, canvasH);
      ctx.restore();
      return;
    }

    const mediaAspect = naturalW / naturalH;
    const canvasAspect = canvasW / canvasH;

    let drawW, drawH, drawX, drawY;

    if (this.fitMode === 'fill') {
      // Stretch
      drawX = 0;
      drawY = 0;
      drawW = canvasW;
      drawH = canvasH;
    } else if (this.fitMode === 'cover') {
      // Crop fill center without distorting aspect
      if (mediaAspect > canvasAspect) {
        drawH = canvasH;
        drawW = canvasH * mediaAspect;
        drawX = (canvasW - drawW) / 2;
        drawY = 0;
      } else {
        drawW = canvasW;
        drawH = canvasW / mediaAspect;
        drawX = 0;
        drawY = (canvasH - drawH) / 2;
      }
    } else {
      // 'contain' (preserves every pixel without distortion)
      if (mediaAspect > canvasAspect) {
        drawW = canvasW;
        drawH = canvasW / mediaAspect;
        drawX = 0;
        drawY = (canvasH - drawH) / 2;
      } else {
        drawH = canvasH;
        drawW = canvasH * mediaAspect;
        drawX = (canvasW - drawW) / 2;
        drawY = 0;
      }
    }

    ctx.drawImage(mediaObj, drawX, drawY, drawW, drawH);
    ctx.restore();
  }

  // ==========================================
  // EFFECT RENDERERS (Each with Opacity Support & Scaled Dimensions)
  // ==========================================

  // 1. ✨ Sparkles & Glitter (Classic Mobile Phone Overlay)
  renderSparkles(ctx, w, h, scale, conf) {
    const opacity = conf.opacity * this.masterOpacity;
    if (opacity <= 0) return;

    ctx.save();
    ctx.globalAlpha = opacity;
    const color = conf.color || '#ffdf00';

    const particles = this.particlePools.sparkles.slice(0, conf.density || 45);
    for (const p of particles) {
      p.rot += p.rotSpeed;
      const twinkle = Math.sin(this.time * 6 + p.twinkleOffset);
      if (twinkle < -0.2) continue;

      const currentAlpha = Math.max(0, Math.min(1, p.alpha * (twinkle * 0.6 + 0.4)));
      const px = p.x * w;
      const py = p.y * h;
      const size = p.size * (0.7 + twinkle * 0.3) * scale;

      ctx.save();
      ctx.translate(px, py);
      ctx.rotate(p.rot);

      const grad = ctx.createRadialGradient(0, 0, 1, 0, 0, size * 1.5);
      grad.addColorStop(0, '#ffffff');
      grad.addColorStop(0.3, color);
      grad.addColorStop(1, 'rgba(255, 255, 255, 0)');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(0, 0, size * 1.5, 0, Math.PI * 2);
      ctx.fill();

      // 4-Point Star Glint Rays
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.6 * scale;
      ctx.beginPath();
      ctx.moveTo(-size * 1.8, 0);
      ctx.lineTo(size * 1.8, 0);
      ctx.moveTo(0, -size * 1.8);
      ctx.lineTo(0, size * 1.8);
      ctx.stroke();

      // Diamond core
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.moveTo(0, -size * 0.4);
      ctx.lineTo(size * 0.4, 0);
      ctx.lineTo(0, size * 0.4);
      ctx.lineTo(-size * 0.4, 0);
      ctx.closePath();
      ctx.fill();

      ctx.restore();
    }
    ctx.restore();
  }

  // 2. 🔮 Soft Dreamy Bokeh Orbs
  renderBokeh(ctx, w, h, scale, conf) {
    const opacity = conf.opacity * this.masterOpacity;
    if (opacity <= 0) return;

    ctx.save();
    ctx.globalAlpha = opacity;
    const baseColor = conf.color || '#ff88cc';

    for (const p of this.particlePools.bokeh) {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < -0.1) p.x = 1.1;
      if (p.x > 1.1) p.x = -0.1;
      if (p.y < -0.1) p.y = 1.1;
      if (p.y > 1.1) p.y = -0.1;

      const px = p.x * w;
      const py = p.y * h;
      const pulse = 0.8 + Math.sin(this.time * 2 + p.pulseOffset) * 0.2;
      const rad = p.radius * pulse * scale;

      const grad = ctx.createRadialGradient(px, py, rad * 0.1, px, py, rad);
      grad.addColorStop(0, baseColor);
      grad.addColorStop(0.7, `${baseColor}44`);
      grad.addColorStop(1, `${baseColor}00`);

      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(px, py, rad, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = `${baseColor}88`;
      ctx.lineWidth = 1.2 * scale;
      ctx.beginPath();
      ctx.arc(px, py, rad * 0.85, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.restore();
  }

  // 3. 💖 Floating Hearts / Warm Embers
  renderHeartsEmbers(ctx, w, h, scale, conf) {
    const opacity = conf.opacity * this.masterOpacity;
    if (opacity <= 0) return;

    ctx.save();
    ctx.globalAlpha = opacity;
    const isEmbers = conf.mode === 'embers';

    for (const p of this.particlePools.hearts) {
      p.y += p.vy * (conf.speed || 1.0);
      p.x += Math.sin(this.time * 4 + p.wobbleOffset) * p.wobbleAmp;

      if (p.y < -0.1) {
        p.y = 1.05;
        p.x = Math.random();
      }

      const px = p.x * w;
      const py = p.y * h;
      const s = p.size * scale;

      ctx.save();
      ctx.translate(px, py);
      ctx.rotate(p.rot);

      if (isEmbers) {
        const grad = ctx.createRadialGradient(0, 0, 1, 0, 0, s);
        grad.addColorStop(0, '#ffffff');
        grad.addColorStop(0.4, '#ff9900');
        grad.addColorStop(1, 'rgba(255, 50, 0, 0)');
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(0, 0, s, 0, Math.PI * 2);
        ctx.fill();
      } else {
        ctx.fillStyle = 'rgba(255, 90, 140, 0.85)';
        ctx.beginPath();
        ctx.moveTo(0, s * 0.3);
        ctx.bezierCurveTo(-s * 0.5, -s * 0.3, -s, s * 0.2, 0, s * 0.9);
        ctx.bezierCurveTo(s, s * 0.2, s * 0.5, -s * 0.3, 0, s * 0.3);
        ctx.closePath();
        ctx.fill();
      }

      ctx.restore();
    }
    ctx.restore();
  }

  // 4. 🌧️ Atmospheric Rainfall & Splashes
  renderRain(ctx, w, h, scale, conf) {
    const opacity = conf.opacity * this.masterOpacity;
    if (opacity <= 0) return;

    ctx.save();
    ctx.globalAlpha = opacity;
    ctx.strokeStyle = 'rgba(180, 225, 255, 0.65)';
    ctx.lineWidth = 1.2 * scale;

    const speed = conf.speed || 1.2;
    for (const p of this.particlePools.rain) {
      p.y += p.vy * speed;
      p.x += p.vx * speed;

      if (p.y > 1.0) {
        p.y = -0.05;
        p.x = Math.random() * 1.3 - 0.15;
      }

      const px = p.x * w;
      const py = p.y * h;
      const len = p.length * scale;

      ctx.beginPath();
      ctx.moveTo(px, py);
      ctx.lineTo(px + len * 0.15, py + len);
      ctx.stroke();

      if (p.y > 0.92) {
        ctx.strokeStyle = 'rgba(180, 225, 255, 0.3)';
        ctx.beginPath();
        ctx.ellipse(px, h * 0.98, 8 * scale, 3 * scale, 0, 0, Math.PI * 2);
        ctx.stroke();
      }
    }
    ctx.restore();
  }

  // 5. ❄️ Atmospheric Snow
  renderSnow(ctx, w, h, scale, conf) {
    const opacity = conf.opacity * this.masterOpacity;
    if (opacity <= 0) return;

    ctx.save();
    ctx.globalAlpha = opacity;
    ctx.fillStyle = '#ffffff';

    for (const p of this.particlePools.snow) {
      p.y += p.vy;
      p.x += Math.sin(this.time * 2 + p.driftOffset) * 0.0006;

      if (p.y > 1.05) {
        p.y = -0.05;
        p.x = Math.random();
      }

      const px = p.x * w;
      const py = p.y * h;
      const rad = p.radius * scale;

      ctx.beginPath();
      ctx.arc(px, py, rad, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }

  // 6. 🌌 Cosmic Dust & Embers (Staacor Engine)
  renderAtmosphericDust(ctx, w, h, scale, conf) {
    const opacity = conf.opacity * this.masterOpacity;
    if (opacity <= 0) return;

    ctx.save();
    ctx.globalAlpha = opacity;
    const color = conf.color || '#00f0ff';

    for (const p of this.particlePools.dust) {
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0) p.x = 1;
      if (p.x > 1) p.x = 0;
      if (p.y < 0) p.y = 1;
      if (p.y > 1) p.y = 0;

      const px = p.x * w;
      const py = p.y * h;

      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(px, py, p.size * scale, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }

  // 7. 🔦 Sweeping Volumetric Search Beams & Flares (Staacor Sentinel)
  renderSentinelBeams(ctx, w, h, scale, conf) {
    const opacity = conf.opacity * this.masterOpacity;
    if (opacity <= 0) return;

    ctx.save();
    ctx.globalAlpha = opacity;
    const cx = w * 0.5;
    const cy = h * 0.32;

    const eyeShiftX = Math.sin(this.time * 0.8) * (8 * scale);
    const eyeShiftY = Math.cos(this.time * 0.5) * (4 * scale);
    const eyeIntensity = 0.8 + Math.sin(this.time * 2) * 0.2;

    const leftEye = { x: cx - (22 * scale) + eyeShiftX * 0.5, y: cy - (20 * scale) + eyeShiftY * 0.5 };
    const rightEye = { x: cx + (22 * scale) + eyeShiftX * 0.5, y: cy - (20 * scale) + eyeShiftY * 0.5 };

    [leftEye, rightEye].forEach(eye => {
      const grad = ctx.createRadialGradient(eye.x, eye.y, 1, eye.x, eye.y, 50 * scale);
      grad.addColorStop(0, `rgba(0, 240, 255, ${0.9 * eyeIntensity})`);
      grad.addColorStop(0.3, `rgba(255, 183, 3, ${0.6 * eyeIntensity})`);
      grad.addColorStop(1, 'rgba(0, 240, 255, 0)');

      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(eye.x, eye.y, 50 * scale, 0, Math.PI * 2);
      ctx.fill();
    });

    const sweepAngle = Math.sin(this.time * 0.6) * 0.45;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(sweepAngle);

    const beamGrad = ctx.createLinearGradient(0, 0, 0, h * 0.75);
    beamGrad.addColorStop(0, 'rgba(0, 240, 255, 0.45)');
    beamGrad.addColorStop(0.5, 'rgba(0, 240, 255, 0.15)');
    beamGrad.addColorStop(1, 'rgba(0, 240, 255, 0)');

    ctx.fillStyle = beamGrad;
    ctx.beginPath();
    ctx.moveTo(-18 * scale, 0);
    ctx.lineTo(18 * scale, 0);
    ctx.lineTo(120 * scale, h * 0.75);
    ctx.lineTo(-120 * scale, h * 0.75);
    ctx.closePath();
    ctx.fill();
    ctx.restore();

    const pulseRadius = (30 + (this.time * 30) % 140) * scale;
    const pulseAlpha = Math.max(0, 1 - pulseRadius / (140 * scale));
    ctx.strokeStyle = `rgba(255, 183, 3, ${pulseAlpha * 0.75})`;
    ctx.lineWidth = 2 * scale;
    ctx.beginPath();
    ctx.arc(cx, cy + (50 * scale), pulseRadius, 0, Math.PI * 2);
    ctx.stroke();

    ctx.restore();
  }

  // 8. 🪐 Holographic 3D Orbit Rings & Glyphs (Staacor University)
  renderHolographicRings(ctx, w, h, scale, conf) {
    const opacity = conf.opacity * this.masterOpacity;
    if (opacity <= 0) return;

    ctx.save();
    ctx.globalAlpha = opacity;
    const cx = w * 0.7;
    const cy = h * 0.38;

    ctx.save();
    ctx.translate(cx, cy);

    for (let r = 1; r <= 3; r++) {
      const radiusX = r * 42 * scale;
      const radiusY = r * 18 * scale;
      const rot = this.time * 0.5 * (r % 2 === 0 ? -1 : 1);

      ctx.save();
      ctx.rotate(rot);
      ctx.strokeStyle = `rgba(0, 240, 255, ${0.45 / r + Math.sin(this.time * 3) * 0.15})`;
      ctx.lineWidth = 1.5 * scale;
      ctx.setLineDash([5 * scale, 5 * scale]);
      ctx.beginPath();
      ctx.ellipse(0, 0, radiusX, radiusY, 0, 0, Math.PI * 2);
      ctx.stroke();

      const px = Math.cos(this.time * (1.2 / r)) * radiusX;
      const py = Math.sin(this.time * (1.2 / r)) * radiusY;
      ctx.fillStyle = '#ffb703';
      ctx.beginPath();
      ctx.arc(px, py, 4.5 * scale, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    ctx.setLineDash([]);
    const fontSize = Math.max(10, Math.round(11 * scale));
    ctx.font = `${fontSize}px "Space Mono", monospace`;
    ctx.fillStyle = 'rgba(0, 240, 255, 0.85)';
    const equations = [
      `∇ × B = μ₀J + μ₀ε₀(∂E/∂t)`,
      `Ψ(r,t) = Ae^(i(k·r - ωt))`,
      `Quantum Coherence: 99.98%`
    ];

    equations.forEach((eq, idx) => {
      const yOffset = (-70 + idx * 18 + Math.sin(this.time + idx) * 3) * scale;
      ctx.fillText(eq, -130 * scale, yOffset);
    });

    ctx.restore();
    ctx.restore();
  }

  // 9. 💎 Bioluminescent Crystals & Shield (Staacor Cavern)
  renderCrystalShield(ctx, w, h, scale, conf) {
    const opacity = conf.opacity * this.masterOpacity;
    if (opacity <= 0) return;

    ctx.save();
    ctx.globalAlpha = opacity;

    const nodes = [
      { x: w * 0.2, y: h * 0.65, size: 75 * scale, color: 'rgba(0, 240, 255,' },
      { x: w * 0.78, y: h * 0.72, size: 90 * scale, color: 'rgba(191, 85, 236,' },
      { x: w * 0.5, y: h * 0.22, size: 65 * scale, color: 'rgba(0, 255, 163,' }
    ];

    nodes.forEach(node => {
      const pulse = 0.5 + Math.sin(this.time * 2.5 + node.x) * 0.35;
      const grad = ctx.createRadialGradient(node.x, node.y, 5 * scale, node.x, node.y, node.size);
      grad.addColorStop(0, `${node.color}${0.8 * pulse})`);
      grad.addColorStop(0.7, `${node.color}${0.2 * pulse})`);
      grad.addColorStop(1, `${node.color}0)`);

      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = `${node.color}${0.6 * pulse})`;
      ctx.lineWidth = 1.5 * scale;
      ctx.setLineDash([6 * scale, 4 * scale]);
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.size * 0.85, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);
    });

    ctx.restore();
  }

  // 10. 🎯 Reconnaissance Drone Crosshair & Telemetry (Staacor Kings)
  renderCrosshairHUD(ctx, w, h, scale, conf) {
    const opacity = conf.opacity * this.masterOpacity;
    if (opacity <= 0) return;

    ctx.save();
    ctx.globalAlpha = opacity;
    const color = conf.color || '#00ffa3';

    const droneX = w * (0.35 + Math.sin(this.time * 0.5) * 0.2);
    const droneY = h * 0.42;

    ctx.strokeStyle = color;
    ctx.lineWidth = 1.2 * scale;
    ctx.setLineDash([4 * scale, 4 * scale]);

    ctx.beginPath();
    ctx.moveTo(droneX - 45 * scale, droneY);
    ctx.lineTo(droneX + 45 * scale, droneY);
    ctx.moveTo(droneX, droneY - 45 * scale);
    ctx.lineTo(droneX, droneY + 45 * scale);
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(droneX, droneY, 32 * scale, 0, Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]);

    const fontSize = Math.max(9, Math.round(10 * scale));
    ctx.font = `${fontSize}px "Space Mono", monospace`;
    ctx.fillStyle = color;
    ctx.fillText(`TARGET LOCKED // DENSITY 98.4%`, droneX + 50 * scale, droneY - 12 * scale);
    ctx.fillText(`COORDINATES: [${droneX.toFixed(0)}, ${droneY.toFixed(0)}]`, droneX + 50 * scale, droneY + 8 * scale);

    ctx.restore();
  }

  // 11. ☀️ Twin Celestial Suns & Satellite Strike (Staacor Space)
  renderCelestialSuns(ctx, w, h, scale, conf) {
    const opacity = conf.opacity * this.masterOpacity;
    if (opacity <= 0) return;

    ctx.save();
    ctx.globalAlpha = opacity;

    const sun1 = { x: w * 0.18, y: h * 0.18, r: 35 * scale };
    const sun2 = { x: w * 0.28, y: h * 0.13, r: 26 * scale };

    [sun1, sun2].forEach(sun => {
      const pulse = 1 + Math.sin(this.time * 3 + sun.x) * 0.1;
      const grad = ctx.createRadialGradient(sun.x, sun.y, 4 * scale, sun.x, sun.y, sun.r * 2.5 * pulse);
      grad.addColorStop(0, '#ffffff');
      grad.addColorStop(0.3, '#ffb703');
      grad.addColorStop(0.7, 'rgba(255, 85, 0, 0.4)');
      grad.addColorStop(1, 'rgba(255, 50, 0, 0)');

      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(sun.x, sun.y, sun.r * 2.5 * pulse, 0, Math.PI * 2);
      ctx.fill();
    });

    const satX = w * 0.35;
    const satY = h * 0.55;
    const targetX = w * 0.65;
    const targetY = h * 0.72;

    const beamAlpha = 0.5 + Math.sin(this.time * 5) * 0.3;
    ctx.strokeStyle = `rgba(0, 240, 255, ${beamAlpha})`;
    ctx.lineWidth = 2 * scale;
    ctx.beginPath();
    ctx.moveTo(satX, satY);
    ctx.lineTo(targetX, targetY);
    ctx.stroke();

    ctx.restore();
  }

  // 12. 📼 Retro VHS Camcorder 1994 OSD
  renderRetroVHS(ctx, w, h, scale, conf) {
    const opacity = conf.opacity * this.masterOpacity;
    if (opacity <= 0) return;

    ctx.save();
    ctx.globalAlpha = opacity;

    const isBlink = Math.sin(this.time * 3) > 0;
    ctx.fillStyle = isBlink ? '#ff3344' : 'transparent';
    ctx.beginPath();
    ctx.arc(38 * scale, 42 * scale, 6 * scale, 0, Math.PI * 2);
    ctx.fill();

    const fontSize = Math.max(11, Math.round(13 * scale));
    ctx.font = `700 ${fontSize}px "Space Mono", monospace`;
    ctx.fillStyle = '#ffffff';
    ctx.fillText('REC', 52 * scale, 46 * scale);

    ctx.font = `600 ${Math.max(10, Math.round(12 * scale))}px "Space Mono", monospace`;
    ctx.fillText('SP  [|||| ]', w - (120 * scale), 46 * scale);

    const dateStr = `SEP 08 1994`;
    const sec = Math.floor(this.time) % 60;
    const min = Math.floor(this.time / 60) % 60;
    const hour = 12;
    const timeStr = `PM ${String(hour).padStart(2, '0')}:${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;

    ctx.font = `700 ${Math.max(12, Math.round(14 * scale))}px "Space Mono", monospace`;
    ctx.fillStyle = '#ffeb3b';
    ctx.fillText(dateStr, 34 * scale, h - (50 * scale));
    ctx.fillText(timeStr, 34 * scale, h - (30 * scale));

    if (Math.random() < 0.2) {
      ctx.fillStyle = 'rgba(255, 255, 255, 0.12)';
      const jitterY = (this.time * 120) % h;
      ctx.fillRect(0, jitterY, w, 12 * scale);
    }

    ctx.restore();
  }

  // 13. 📺 CRT Scanlines & Slice Glitch
  renderScanlines(ctx, w, h, scale, conf) {
    const opacity = conf.opacity * this.masterOpacity;
    if (opacity <= 0) return;

    ctx.save();
    ctx.globalAlpha = opacity;

    ctx.fillStyle = 'rgba(0, 0, 0, 0.35)';
    const lineStep = Math.max(3, Math.round(4 * scale));
    for (let y = 0; y < h; y += lineStep) {
      ctx.fillRect(0, y, w, 1.8 * scale);
    }

    if (Math.random() < (conf.glitch || 0.05)) {
      const glitchY = Math.random() * h;
      const glitchH = (Math.random() * 12 + 4) * scale;
      ctx.fillStyle = 'rgba(0, 240, 255, 0.25)';
      ctx.fillRect(0, glitchY, w, glitchH);

      ctx.fillStyle = 'rgba(255, 0, 100, 0.2)';
      ctx.fillRect(0, glitchY + 2, w, glitchH * 0.7);
    }
    ctx.restore();
  }

  // 14. 🌡️ Thermal / Night Vision Sensor Mode
  renderThermalMode(ctx, w, h, scale, conf) {
    const opacity = conf.opacity * this.masterOpacity;
    if (opacity <= 0) return;

    ctx.save();
    ctx.globalAlpha = opacity;

    ctx.fillStyle = 'rgba(255, 40, 0, 0.12)';
    ctx.fillRect(0, 0, w, h);

    const fontSize = Math.max(9, Math.round(11 * scale));
    ctx.font = `700 ${fontSize}px "Space Mono", monospace`;
    ctx.fillStyle = '#ff3366';
    ctx.fillText('THERMAL SENSOR ACTIVE // SPECTRUM: INFRARED', 34 * scale, h - (34 * scale));

    ctx.restore();
  }

  // 15. 📡 Live Broadcast HUD & Tactical Brackets (Staacor Style)
  renderBroadcastHUD(ctx, w, h, scale, conf) {
    const opacity = conf.opacity * this.masterOpacity;
    if (opacity <= 0) return;

    ctx.save();
    ctx.globalAlpha = opacity;

    const livePulse = Math.sin(this.time * 4) > 0;
    ctx.fillStyle = livePulse ? '#ff3366' : 'rgba(255, 51, 102, 0.4)';
    ctx.beginPath();
    ctx.arc(32 * scale, 32 * scale, 6 * scale, 0, Math.PI * 2);
    ctx.fill();

    const fontSize = Math.max(10, Math.round(12 * scale));
    ctx.font = `700 ${fontSize}px "Space Mono", monospace`;
    ctx.fillStyle = '#ffffff';
    ctx.fillText('LIVE HOLONET FEED', 46 * scale, 36 * scale);

    const text = conf.text || this.customOverlayText || 'STAACOR HOLONET // ARCHIVE';
    ctx.font = `700 ${Math.max(9, Math.round(11 * scale))}px "Space Mono", monospace`;
    ctx.fillStyle = '#00f0ff';
    ctx.textAlign = 'right';
    ctx.fillText(text, w - (30 * scale), 36 * scale);
    ctx.textAlign = 'left';

    ctx.strokeStyle = 'rgba(0, 240, 255, 0.5)';
    ctx.lineWidth = 1.5 * scale;
    const margin = 24 * scale;
    const len = 28 * scale;

    // Top-Left
    ctx.beginPath();
    ctx.moveTo(margin, margin + len);
    ctx.lineTo(margin, margin);
    ctx.lineTo(margin + len, margin);
    ctx.stroke();

    // Top-Right
    ctx.beginPath();
    ctx.moveTo(w - margin - len, margin);
    ctx.lineTo(w - margin, margin);
    ctx.lineTo(w - margin, margin + len);
    ctx.stroke();

    // Bottom-Left
    ctx.beginPath();
    ctx.moveTo(margin, h - margin - len);
    ctx.lineTo(margin, h - margin);
    ctx.lineTo(margin + len, h - margin);
    ctx.stroke();

    // Bottom-Right
    ctx.beginPath();
    ctx.moveTo(w - margin - len, h - margin);
    ctx.lineTo(w - margin, h - margin);
    ctx.lineTo(w - margin, h - margin - len);
    ctx.stroke();

    ctx.restore();
  }

  // 16. 🎬 Cinematic Vignette
  renderVignette(ctx, w, h, scale, conf) {
    const opacity = conf.opacity * this.masterOpacity;
    if (opacity <= 0) return;

    ctx.save();
    ctx.globalAlpha = opacity;

    const maxRad = Math.sqrt((w / 2) ** 2 + (h / 2) ** 2);
    const grad = ctx.createRadialGradient(w / 2, h / 2, maxRad * 0.4, w / 2, h / 2, maxRad);
    grad.addColorStop(0, 'rgba(0, 0, 0, 0)');
    grad.addColorStop(0.7, 'rgba(0, 0, 0, 0.4)');
    grad.addColorStop(1, 'rgba(0, 0, 0, 0.85)');

    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);
    ctx.restore();
  }

  // 17. 🌐 3D Perspective Cyber Synthwave Grid
  renderCyberGrid(ctx, w, h, scale, conf) {
    const opacity = conf.opacity * this.masterOpacity;
    if (opacity <= 0) return;

    ctx.save();
    ctx.globalAlpha = opacity;
    const color = conf.color || '#ff007f';
    const horizon = h * 0.65;

    ctx.strokeStyle = color;
    ctx.lineWidth = 1.2 * scale;

    const vpX = w * 0.5;
    const vpY = horizon;
    const count = 16;
    for (let i = -count; i <= count; i++) {
      const bottomX = vpX + (i * (w / count) * 1.5);
      ctx.beginPath();
      ctx.moveTo(vpX, vpY);
      ctx.lineTo(bottomX, h);
      ctx.stroke();
    }

    const speed = (this.time * 40) % 30;
    for (let y = 0; y <= h - horizon; y += 15 * scale) {
      const curveY = horizon + Math.pow(y / (h - horizon), 1.8) * (h - horizon) + speed * (y / (h - horizon));
      if (curveY <= h) {
        ctx.beginPath();
        ctx.moveTo(0, curveY);
        ctx.lineTo(w, curveY);
        ctx.stroke();
      }
    }

    ctx.restore();
  }

  // ==========================================
  // CAPTURE & RECORDING CAPABILITIES
  // ==========================================

  captureImage(filename = 'effects-studio-snapshot.png') {
    return new Promise((resolve) => {
      this.canvas.toBlob((blob) => {
        if (!blob) return;
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        resolve(blob);
      }, 'image/png');
    });
  }

  startRecording(mimeTypePreference = null) {
    if (this.isRecording) return;

    const stream = this.canvas.captureStream(30);

    if (this.mediaType === 'video' && this.videoElement) {
      try {
        if (this.videoElement.captureStream) {
          const vStream = this.videoElement.captureStream();
          const audioTracks = vStream.getAudioTracks();
          if (audioTracks.length > 0) {
            stream.addTrack(audioTracks[0]);
          }
        } else if (this.videoElement.mozCaptureStream) {
          const vStream = this.videoElement.mozCaptureStream();
          const audioTracks = vStream.getAudioTracks();
          if (audioTracks.length > 0) {
            stream.addTrack(audioTracks[0]);
          }
        }
      } catch (e) {
        console.warn('Could not capture audio track from source video:', e);
      }
    }

    let chosenMime = mimeTypePreference;
    if (!chosenMime) {
      const candidates = [
        'video/webm;codecs=vp9,opus',
        'video/webm;codecs=vp8,opus',
        'video/webm',
        'video/mp4'
      ];
      for (const m of candidates) {
        if (MediaRecorder.isTypeSupported(m)) {
          chosenMime = m;
          break;
        }
      }
    }

    try {
      this.mediaRecorder = new MediaRecorder(stream, chosenMime ? { mimeType: chosenMime } : undefined);
    } catch (e) {
      this.mediaRecorder = new MediaRecorder(stream);
    }

    this.recordedChunks = [];
    this.isRecording = true;
    this.recordStartTime = performance.now();

    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        this.recordedChunks.push(event.data);
      }
    };

    this.mediaRecorder.onstop = () => {
      this.isRecording = false;
      const mime = this.mediaRecorder.mimeType || 'video/webm';
      const blob = new Blob(this.recordedChunks, { type: mime });
      if (this.onRecordComplete) {
        this.onRecordComplete(blob, mime);
      }
    };

    this.mediaRecorder.start(100);
  }

  stopRecording() {
    if (!this.isRecording || !this.mediaRecorder) return;
    this.mediaRecorder.stop();
  }
}
