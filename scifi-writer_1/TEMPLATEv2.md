# 🎬 SCI-FI STORYBOARD SPECIFICATION v2.0 (TEMPLATEv2.md)
<!-- PROJECT: Project ME / SciFi Vision Studio -->
<!-- ENGINE: Ollama scifi-writer:1 | Kokoro-TTS v1.0 | Stable Diffusion LCM | FFmpeg 1080p -->

---

## 🧭 PRODUCTION RESOURCE CHEAT SHEET
Use these verified local assets and parameters when writing or generating new storyboards.

### 🎵 1. Soundtrack Manifest (`/home/jack/Desktop/mp3/`)
Choose any track below for the `Recommended BGM` or per-panel music track:

| Dramatic Mood / Theme | Recommended File Name | Duration | Description |
| :--- | :--- | :--- | :--- |
| 🌑 **Deep Mystery & Tension** | `Shadows-Anno_Domini_Beats.mp3` | 4:11 | Low-frequency bass drone, ticking percussion, eerie dark exploration |
| 🌑 **Ominous Threat / Cyber Dread**| `Sinister-Anno_Domini_Beats.mp3` | 3:39 | Heavy synth pulses, alien signals, cybernetic antagonist presence |
| ⚔️ **Action / Cyber Conflict** | `GodFury-AnnoDominiBeats.mp3` | 3:04 | High-intensity combat, electronic drums, battle clashes |
| ⚔️ **Urgent Dogfight / Breach** | `Freefall-Anno_Domini_Beats.mp3` | 4:01 | Rapid tempo, cinematic synth riser, high-stakes countdown |
| 🌌 **Cosmic Wonder / Singularity**| `Deified-The_Grey_Room_Density_and_Time.mp3` | 3:00 | Vast atmospheric reverb, ethereal celestial progression |
| 🌌 **Quantum Portals / Vortex** | `Rotator-The_Grey_Room_Density_and_Time.mp3` | 3:20 | Hypnotic swirling pulses, wormhole traversal ambience |
| 🌌 **Epic Sci-Fi Space Odyssey**| `Sagas-The_Grey_Room_Density_and_Time.mp3` | 3:10 | Grand orchestral sci-fi brass and deep strings |
| 🏙️ **High-Tech Megacity / Future**| `Future-Anno_Domini_Beats.mp3` | 2:17 | Futuristic trap groove, cyberpunk neon street atmosphere |
| 🏆 **Heroic Triumph / Fleet** | `Invincible-Anno_Domini_Beats.mp3` | 3:14 | Uplifting sci-fi brass, resolute forward drive |
| ☕ **Calm Reflection / Memory** | `Remember-Anno_Domini_Beats.mp3` | 3:17 | Melancholic lo-fi keys, philosophical soliloquy, quiet spaceflight |
| ☕ **Silent Void / Drifting** | `Sailing-Anno_Domini_Beats.mp3` | 2:51 | Slow ambient drifting, reflective quiet contemplation |
| ☕ **Bio-Dome / Zen Habitat** | `The_Off-White_Lotus-Ezra_Lipp.mp3` | 1:57 | Organic acoustic-electronic hybrid, hydroponics calm |

---

### 🎙️ 2. Voice Roster & Kokoro TTS Casting (`kokoro-v1.0.onnx`)
Match voice IDs to characters. Speeds between `0.90` and `1.00` are optimal:

| Voice ID | Character Archetype | Tone & Cadence | Recommended Speed |
| :--- | :--- | :--- | :--- |
| `af_nova` | **Research Scientist / Science Officer** | Analytical, clear, calm, articulate | `0.95` |
| `bm_george` | **Imperial Officer / Fleet Admiral** | Authoritative, resonant, stern British cadence | `0.92` |
| `af_heart` | **Ship AI Core / Mainframe Interface** | Cool, polite, neutral synthetic clarity | `1.00` |
| `am_michael`| **Veteran Commander / Squadron Lead** | Grounded, experienced, gritty American male | `0.95` |
| `af_sarah` | **Tactical Specialist / Field Recon** | Crisp, alert, expressive female operative | `0.96` |
| `am_adam` | **Cybernetic Hacker / Deep-Void Scout**| Introspective, focused, calculated delivery | `0.96` |
| `af_bella` | **Diplomat / High-Tier Intelligence** | Sophisticated, persuasive, warm yet firm | `0.94` |
| `bm_lewis` | **Chief Engineer / Tech Specialist** | Pragmatic, fast-talking, problem-solving tone | `0.98` |

> [!TIP]
> **Voice Blending**: You can blend voices using Kokoro notation: e.g., `af_nova:60,af_heart:40` creates an AI-augmented human scientist voice!

---

### 🎨 3. Stable Diffusion LCM Art Direction (`/home/jack/Desktop/Comfy-UI/models/checkpoints/`)
LCM checkpoints produce cinematic images in only **4 to 8 steps**:

* **Recommended Checkpoints**:
  * `dreamshaper_8LCM.safetensors` *(General Sci-Fi, environments, characters, spaceships)*
  * `cyberphotonlcm_v10.safetensors` *(Hard sci-fi, ultra-detailed circuitry, neon cybernetics)*
  * `comiccraftLCM_beta4.safetensors` *(Graphic novel & comic book stylized aesthetic)*
  * `cyberrealisticLCM_cyberrealistic42.safetensors` *(Photorealistic materials, gritty lighting)*
* **Optimal Generation Parameters**:
  * **Steps**: `4` to `8`
  * **CFG / Guidance Scale**: `1.2` to `2.0` (LCM requires low CFG)
  * **Resolution**: `512x512`, `768x512` (Landscape), or `1376x768` (16:9 widescreen)
* **Prompt Engineering Keywords**:
  `cinematic sci-fi photo, volumetric neon lighting, holographic displays, intricate mechanical detail, 8k, photorealistic, Unreal Engine 5, anamorphic lens flare, sharp focus`
* **Negative Prompt Template**:
  `blurry, low quality, deformed, artifacts, text, watermark, cartoonish, lowres, noisy`

---

### 🎥 4. Camera Choreography (Ken Burns Motion Effects)
Specify the camera motion tag in each panel:
* `Slow Zoom-In Center`: Focal point tightens toward center anomaly / face (1.0x → 1.15x).
* `Pan-Left-To-Right`: Slow horizontal scan across wide planetary vistas or fleets.
* `Pan-Right-To-Left`: Tracking fast cyber action, incoming missile fire, or alerts.
* `Zoom-Out-Wide`: Dramatic pull-back revealing scale, immense star gates, or star systems.
* `Slow-Drift-Forward`: Simulates spaceship helm perspective gliding into the void.

---

### 🗣️ 5. Dual Dialogue Writing Guide
* **`🗣️ Spoken Text (TTS Clean)`**: Written specifically for neural speech.
  * Spell out years and dates: e.g., `twenty-one eighty-four point zero nine` instead of `2184.09`.
  * Expand acronyms: e.g., `Artificial Intelligence Core` instead of `A.I. Core`.
  * Use commas `, ` for deliberate breathing pauses instead of ellipses `...` or hashes `//`.
* **`💬 On-Screen Dialogue (HUD Display)`**: Formatted for the on-screen sci-fi HUD box.
  * Includes mission timestamps, cyber headers, and styled markdown dialogue.

---

## 📋 PRODUCTION STORYBOARD BLUEPRINT

```markdown
🎬 **COMIC STORYBOARD: "[Title of Your Sci-Fi Episode]"**

🎵 **Recommended BGM**: [Track Name from Manifest, e.g. Shadows-Anno_Domini_Beats.mp3] | Volume: 0.22

---

### 🖼️ PANEL 1: [Scene Title / Environment Hook]

* 🔲 **Layout**: Full Banner (16:9 Widescreen) | Height: 1 Row
* 🎥 **Camera Motion**: Slow Zoom-In Center | Hold: 0.8s
* 🎙️ **Voice**: af_nova (Research Scientist)
* ⚡ **Voice Speed**: 0.95
* 🗣️ **Spoken Text (TTS Clean)**:
  Log date: twenty-one eighty-four point zero nine. Orbital Sector seven. We have detected an unusual energy signature emanating from the abandoned research facility on Kepler-62f.
* 💬 **On-Screen Dialogue (HUD Display)**:
  LOG DATE: 2184.09 // ORBITAL SECTOR 7
  "We've detected an unusual energy signature emanating from the abandoned research facility on Kepler-62f."
* 🎨 **Stable Diffusion Image Prompt**:
  `cinematic sci-fi photo of a futuristic research laboratory, with metallic surfaces and holographic displays, surrounded by towering mountains of ice on a distant planet, 8k, Unreal Engine 5`
* ⚙️ **LCM Settings**: Steps: 6 | CFG: 1.5 | Model: dreamshaper_8LCM.safetensors

---

### 🖼️ PANEL 2: [Conflict / Discovery / Anomaly]

* 🔲 **Layout**: Full Banner (16:9 Widescreen) | Height: 1 Row
* 🎥 **Camera Motion**: Pan-Left-To-Right | Hold: 0.6s
* 🎙️ **Voice**: af_nova (Research Scientist)
* ⚡ **Voice Speed**: 0.95
* 🗣️ **Spoken Text (TTS Clean)**:
  As I access the facility mainframe, I am confronted with a cryptic message from an unknown entity, User Erebus, warning us of an imminent catastrophe.
* 💬 **On-Screen Dialogue (HUD Display)**:
  MAINFRAME INTRUSION // USER: EREBUS
  "As I access the facility's mainframe, I'm confronted with a cryptic warning of an imminent catastrophe..."
* 🎨 **Stable Diffusion Image Prompt**:
  `dramatic action shot of a futuristic laboratory with flickering holographic screens and sparks flying, cyber conflict, ominous red warning lights, cinematic sci-fi, 8k, photorealistic`
* ⚙️ **LCM Settings**: Steps: 6 | CFG: 1.5 | Model: dreamshaper_8LCM.safetensors

---

### 🖼️ PANEL 3: [Climax / Revelation / The Singularity]

* 🔲 **Layout**: Full Banner (16:9 Widescreen) | Height: 1 Row
* 🎥 **Camera Motion**: Slow-Drift-Forward | Hold: 1.0s
* 🎙️ **Voice**: af_nova (Research Scientist)
* ⚡ **Voice Speed**: 0.95
* 🗣️ **Spoken Text (TTS Clean)**:
  Aurora Rising. We have breached the threshold of human evolution. The singularity has been reached.
* 💬 **On-Screen Dialogue (HUD Display)**:
  ### Aurora Rising
  "We've breached the threshold of human evolution. The singularity has been reached."
* 🎨 **Stable Diffusion Image Prompt**:
  `wide-angle panoramic shot of a breathtaking star-filled galaxy with glowing nebulae and distant planetary systems, aurora cosmic rays, set against an inky black background, epic cosmic scale, 8k`
* ⚙️ **LCM Settings**: Steps: 6 | CFG: 1.5 | Model: dreamshaper_8LCM.safetensors

---

### 🖼️ PANEL 4: [Twist / Warning / Imperial Command]

* 🔲 **Layout**: Full Banner (16:9 Widescreen) | Height: 1 Row
* 🎥 **Camera Motion**: Slow Zoom-In Center | Hold: 0.8s
* 🎙️ **Voice**: bm_george (Imperial Officer)
* ⚡ **Voice Speed**: 0.92
* 🗣️ **Spoken Text (TTS Clean)**:
  Our mission has been compromised. The Aurora crew is now the only hope for humanity's survival. The Quantum Prophecy warns us of an impending reckoning, as our very existence hangs in the balance.
* 💬 **On-Screen Dialogue (HUD Display)**:
  COMMAND COMM-LINK // ADMIRAL GEORGE
  "Our mission has been compromised. The Aurora's crew is now the only hope for humanity's survival... The Quantum Prophecy warns of an impending reckoning."
* 🎨 **Stable Diffusion Image Prompt**:
  `surrealistic depiction of a glowing ethereal quantum portal with swirling quantum particles and distant starry skies, cosmic gateway, mysterious, 8k, cinematic lighting`
* ⚙️ **LCM Settings**: Steps: 6 | CFG: 1.5 | Model: dreamshaper_8LCM.safetensors

---

### 🖼️ PANEL 5: [Resolution / The Cosmic Horizon]

* 🔲 **Layout**: Full Banner (16:9 Widescreen) | Height: 1 Row
* 🎥 **Camera Motion**: Zoom-Out-Wide | Hold: 1.2s
* 🎙️ **Voice**: af_nova (Research Scientist)
* ⚡ **Voice Speed**: 0.95
* 🗣️ **Spoken Text (TTS Clean)**:
  Infinity awaits. And so, we set forth into the unknown, guided by the light of the Aurora.
* 💬 **On-Screen Dialogue (HUD Display)**:
  ### Infinity Awaits
  "And so, we set forth into the unknown, guided by the light of the Aurora..."
* 🎨 **Stable Diffusion Image Prompt**:
  `wide-angle panoramic shot of a futuristic spaceship entering an infinite radiant cosmic horizon, breathtaking star-filled galaxy with glowing nebulae, guided by the light of Aurora, cinematic sci-fi masterpiece, 8k`
* ⚙️ **LCM Settings**: Steps: 6 | CFG: 1.5 | Model: dreamshaper_8LCM.safetensors
```

---

## ⚡ QUICK COMMANDS
* **Render this storyboard into MP4**:
  ```bash
  /home/jack/Desktop/Kokoro-TTS-Pause/venv/bin/python3 build_video.py --markdown TEMPLATEv2.md --output science_v2.mp4
  ```
* **Launch Interactive Studio Web App**:
  ```bash
  ./start_studio.sh
  ```
