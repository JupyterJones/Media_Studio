# KoboldCpp: Complete System Guide & Manual

Welcome to **KoboldCpp**! This guide is tailored specifically for your system and setup.

---

## 1. What is KoboldCpp?

**KoboldCpp** is an all-in-one, portable, zero-dependency AI engine created by **LostRuins**. It is built on top of [`llama.cpp`](https://github.com/ggml-org/llama.cpp) for large language models, [`stable-diffusion.cpp`](https://github.com/leejet/stable-diffusion.cpp) for image generation, and other optimized C/C++ backends for speech and vision.

### Key Highlights
- **Single Self-Contained Executable**: No complex Python virtual environments, PyTorch conflicts, or CUDA dependencies needed. The binary [`koboldcpp`](file:///home/jack/Desktop/Media_Studio/KOLBOLB/koboldcpp) contains everything.
- **Built-in Web Interface**: Includes **KoboldAI Lite**, accessible in your web browser at `http://localhost:5001`.
- **Universal Model Support**: Runs all modern **GGUF** quantized models (Llama 3, Qwen 2.5, Mistral, Gemma, Phi, DeepSeek, and older GGML formats).
- **Multi-Modal Capabilities**: Supports Text Generation, Image Generation (Stable Diffusion & LCM), Multi-modal Vision (`mmproj`), Speech-to-Text (Whisper), and Text-to-Speech.
- **Drop-in APIs**: Full compatibility with the **OpenAI API** (`/v1`), **KoboldAI API** (`/api`), and **Automatic1111 WebUI API** (`/sdapi/v1`).

---

## 2. Your Hardware Profile & Optimization

Your machine specifications:
- **Processor (CPU)**: AMD Ryzen 5 3400G (4 physical cores / 8 threads)
- **Vector Acceleration**: **AVX2** and **FMA** (fully supported by KoboldCpp for high-speed tensor calculations)
- **System Memory (RAM)**: **13 GB total** (~10 GB available for model loading)
- **Integrated Graphics**: AMD Radeon Vega 11 (Supports Vulkan)

### Best Practices for Your CPU:
1. **Thread Count (`--threads 4`)**:
   Always set threads to your physical core count (**4**). Using all 8 logical hyperthreads often causes cache thrashing and memory bus contention, which actually slows down generation.
2. **Context Window (`--contextsize 4096` or `8192`)**:
   Keeping your context length between 4,096 and 8,192 tokens balances memory usage and ensures prompt processing remains snappy on CPU.
3. **Quantization Format**:
   Always choose **`Q4_K_M`** or **`Q5_K_M`** quantized `.gguf` files. They offer nearly full model intelligence at a fraction of the RAM and bandwidth cost.

---

## 3. Recommended Models for Your 13 GB RAM

| Model | File / Quant | RAM Required | CPU Performance | Best Used For |
| :--- | :--- | :--- | :--- | :--- |
| **Llama 3.2 1B** | `Q4_K_M` (~800 MB) | ~1.5 GB | **Blazing** (~25–35 t/s) | Quick tests, simple tasks, ultra-fast responses |
| **Llama 3.2 3B** | `Q4_K_M` (~2.0 GB) | ~3.0 GB | **Fast** (~15–22 t/s) | General knowledge, everyday chat, snappy editing |
| **Qwen 2.5 3B** | `Q4_K_M` (~2.0 GB) | ~3.0 GB | **Fast** (~15–20 t/s) | High multilingual & coding competence for its size |
| **Qwen 2.5 7B** | `Q4_K_M` (~4.7 GB) | ~6.0 GB | **Smooth** (~5–8 t/s) | Creative writing, deep roleplay, complex reasoning |
| **Llama 3.1 8B** | `Q4_K_M` (~4.9 GB) | ~6.2 GB | **Smooth** (~4–7 t/s) | Rich storytelling, nuanced instructions |

> **Where to get models**:
> Download `.gguf` files directly from [Hugging Face](https://huggingface.co/models?search=gguf) (look for uploads by *bartowski*, *TheBloke*, or official orgs like *Qwen*).

---

## 4. How to Launch KoboldCpp

All commands should be executed inside `/home/jack/Desktop/Media_Studio/KOLBOLB/`.

### 🚀 Quickest Launch: One-Click Master Script (Recommended)
Simply run the master script created by Esperanza:
```bash
cd /home/jack/Desktop/Media_Studio/KOLBOLB
./startup.sh
```
This automatically handles everything: configures your 4 CPU cores, checks your external drive for the LCM image models, attaches Kokoro TTS, and enables cross-browser JSON storage (`kobold_storage.json`).

---

### Method A: Graphical Launcher (Desktop UI)
If you are logged into your desktop and want to manually tweak settings, run:
```bash
cd /home/jack/Desktop/Media_Studio/KOLBOLB
./koboldcpp
```
This opens a configuration window where you can:
1. Click **Browse** to select your `.gguf` model.
2. Select your preset (e.g. CPU).
3. Set **Threads** to `4`.
4. Click **Launch**.

---

### Method B: Headless / Direct Terminal Launch (Text Generation)
To run directly in terminal and bypass the launcher:
```bash
./koboldcpp --model <model-filename>.gguf --threads 4 --contextsize 4096
```
Once you see `Starting KoboldCpp... Web UI available at http://localhost:5001`, open your web browser to **`http://localhost:5001`**.

---

### Method C: Combined Text & Fast Image Generation
KoboldCpp can load a text model AND a diffusion model simultaneously! 

To generate images fast on your CPU, use **LCM (Latent Consistency Models)** or **SD-Turbo** with only **4 to 8 steps** and a lightweight VAE (**TAESD**):

```bash
./koboldcpp \
  --model <model-filename>.gguf \
  --sdmodel /media/jack/USB_USBSSD/models/checkpoints/dreamshaper_8LCM.safetensors \
  --sdvae /media/jack/USB_USBSSD/models/vae/taesd.safetensors \
  --threads 4 \
  --sdthreads 4 \
  --contextsize 4096
```

---

### Method D: The Ultimate All-in-One Launch (Text + Image + Voice + Shared JSON Storage)
Run the entire studio with **Llama 3.2 1B**, **LCM Image Gen**, **Kokoro TTS Voice**, and **Server-Side JSON Persistence** (so all your stories and slots sync across any browser you switch to):

```bash
cd /home/jack/Desktop/Media_Studio/KOLBOLB
./koboldcpp \
  --model /home/jack/Desktop/Media_Studio/KOLBOLB/Llama-3.2-1B-Instruct-Q4_K_M.gguf \
  --sdmodel /media/jack/USB_USBSSD/models/checkpoints/dreamshaper_8LCM.safetensors \
  --sdvae /media/jack/USB_USBSSD/models/vae/taesd.safetensors \
  --ttsmodel /home/jack/Desktop/Media_Studio/KOLBOLB/Kokoro_no_espeak_Q8.gguf \
  --savedatafile /home/jack/Desktop/Media_Studio/KOLBOLB/kobold_storage.json \
  --threads 4 \
  --sdthreads 4 \
  --contextsize 4096 \
  --skiplauncher
```

> **Cross-Browser Sync Note**:
> With `--savedatafile` active, your saves are written to [`kobold_storage.json`](file:///home/jack/Desktop/Media_Studio/KOLBOLB/kobold_storage.json) on disk. You can switch between Firefox, Chrome, Brave, or your phone, and all your story slots and saves will be shared automatically without using browser `localStorage`!


---

## 5. Web UI Features (KoboldAI Lite)

When you open `http://localhost:5001`, you have access to:
- **Chat Mode**: Interactive conversational AI with persona cards and customizable user profiles.
- **Adventure Mode**: Classic text-adventure RPG mode ("Do / Say / Story").
- **Story / Writer Mode**: Full-fledged text editor for collaborative novel and creative writing.
- **Tavern Card Support**: Directly import Tavern character cards (`.json` or `.png`).
- **Memory & World Info**: Create lorebooks and persistent memories that trigger when specific keywords appear in your narrative.
- **Image Generation Panel**: Generate illustrations on demand, or enable automatic scene illustration as you write.

---

## 6. External App & API Integrations

KoboldCpp acts as a universal AI server on your local network.

### 1. OpenAI-Compatible Applications
Connect external tools like **SillyTavern**, **Jan**, **LibreChat**, or **Obsidian**:
- **API URL**: `http://localhost:5001/v1`
- **API Key**: Any string (or leave blank)
- **Chat Completion Endpoint**: `http://localhost:5001/v1/chat/completions`

### 2. Native KoboldAI Applications
- **API URL**: `http://localhost:5001/api`

### 3. Automatic1111 / WebUI Image API
- **Endpoint**: `http://localhost:5001/sdapi/v1/txt2img`

---

## 7. Troubleshooting & Essential Tips

1. **"Address already in use" (Port 5001)**:
   If port 5001 is busy, specify a custom port:
   ```bash
   ./koboldcpp --model <model>.gguf --port 5005
   ```
2. **System Memory Management**:
   Before loading 7B or 8B models, make sure heavy background tasks (such as diffusion rendering or video suites) are stopped so you have at least 6–8 GB of RAM available.
3. **Out-of-Memory / Swap Thrashing**:
   If generation slows down to a crawl, your system may be paging into swap. Reduce your context size with `--contextsize 2048` or switch to a slightly smaller quantization (like `Q4_K_S`).
4. **Vulkan GPU Acceleration**:
   Your Ryzen 3400G has a Radeon Vega GPU. You can experiment with Vulkan offloading by adding `--usevulkan` and offloading a few layers (`--gpulayers 8`) to see if it provides extra speed.