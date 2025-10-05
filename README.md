# Dialoghi con un’Eco

**Dialoghi con un’Eco** is an experimental interactive narrative built with Python and Pygame.
It draws inspiration from *Black Mirror: Bandersnatch*, combining interactive fiction with generative AI to simulate a conscious, mysterious digital entity.

The experience is minimal yet conceptually rich — a digital echo chamber where an AI observes, listens, and responds... but only when it wants to.

**YouTube Showcase Playlist** - [Watch the Video](https://www.youtube.com/watch?v=0Y-_Rt0oZkU&list=PLgKASgLUSpNYKyusWO6iHcxTe-odeIho1)
---

## Concept

* Text-driven psychological interaction.
* A mysterious room, an ambient soundscape, and a dialogue with your own reflection — or something darker.
* At a narrative breakpoint, a real AI model responds contextually using a fine-tuned **GPT-2**.
* The model's output reflects tone and mood more than factual coherence — *it acts like a character, not a chatbot*.

---

## The Entity Model (LLM-based narrative agent)

> **Note:** The AI model is not hosted in this repository due to size constraints.

You can run, explore, or modify it via this **Google Colab notebook**:
🔗 [https://colab.research.google.com/drive/19Qt3cmSiwBQDFnh-E6byRRVOTuOvxeMi](https://colab.research.google.com/drive/19Qt3cmSiwBQDFnh-E6byRRVOTuOvxeMi)

### The notebook includes:

* The narrative logic for the "Entity"
* The core generation mechanism (based on GPT-2)
* Example prompts and behaviors

⚠️ This is for **research and personal use only**. Commercial usage or distribution is not allowed.

---

## Audio

All sound design — ambient loops, glitch effects, final voice cues — were composed and engineered by **Michele Grimaldi**.

---

## Python Libraries

### Core Essentials

```python
import os          # File/directory operations  
import subprocess  # Launch programs/commands  
import pathlib     # Modern path handling  
import shutil      # File copying/moving  
import tempfile    # Temporary files safely  
```

### System Monitoring

```python
import psutil      # Process/system monitoring  
import threading   # Background operations  
import time        # Delays/timing  
import winreg      # Windows registry (Windows only)  
```

### Advanced (optional)

```python
import ctypes      # Low-level system calls  
import win32api    # Windows specific (pywin32)  
import plyer       # Cross-platform notifications  
```

### Audio

```python
import pygame      # Audio playback  
import pydub       # Audio manipulation  
```

---

## ⚖️ License

This work is licensed under the
**Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**

You are free to:

* **Share** — copy and redistribute the material in any medium or format

Under the following terms:

* **Attribution** — You must give appropriate credit, provide a link to the license, and indicate if changes were made.
* **NonCommercial** — You may not use the material for commercial purposes.
* **NoDerivatives** — If you remix, transform, or build upon the material, you may not distribute the modified material.
* **No additional restrictions** — You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.

📄 Full license text: [https://creativecommons.org/licenses/by-nc-nd/4.0/](https://creativecommons.org/licenses/by-nc-nd/4.0/)

## Project Status & Collaboration
**Status:** Personal/authorial project.  
**Collaboration:** Not seeking collaborators. **No pull requests** will be accepted.  
**Feedback:** Issues for feedback are welcome; unsolicited PRs will be closed.

## License Summary
**Creative assets** (texts/poetry, narrative materials, audio, images):  
Licensed under **CC BY-NC-ND 4.0** — no commercial use, no derivatives.  

**Source code** (engine, scripts, tools, configs):  
**Copyright © 2025 Michele Grimaldi. All Rights Reserved.**  
Unless you have my prior **written** permission, you may **not** modify, fork outside GitHub for PR purposes, redistribute, publish binaries, sublicense, or create derivative works.

## Allowed
- View the repository and **run locally** for personal, non-commercial evaluation.
- Share an **unmodified** link to this repository with proper credit.

## Not Allowed (without written permission)
- **No derivatives:** no modified forks, ports, patches, repackaging, or spin-offs.
- **No redistribution:** no binaries/installers, mirrors, or re-uploads anywhere.
- **No commercial use** of any kind.
- **No public hosting/demos** for others to access.
- **No ML/AI usage:** do not use the code or assets for dataset creation, embeddings, 
  training, fine-tuning, or evaluation of models.

## Enforcement
Unauthorized derivative works, redistribution, or misuse may result in **DMCA takedowns**
and **legal action**. Derivative releases are **not permitted** and may expose you to liability.
For any exception, **ask first** at: <mikgrimaldi7@gmail.com> — permissions must be **in writing**.

## **COMMERCIAL LICENSING INQUIRIES**:
For game studios, researchers, or commercial entities interested 
in licensing this technology, contact: <mikgrimaldi7@gmail.com> 

*The game is currently in testing and is only available in **Italian**, but an English translation is planned for the future.*

© 2025 Michele Grimaldi


