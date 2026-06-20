# AI Educational Animation Platform

An automation pipeline and web application for generating high-quality mathematical and educational animations from human-readable text prompts. It connects **Gemini 2.5 Flash** (via the modern Google GenAI SDK) with the **Manim (Community Edition)** math animation engine to compile prompts directly into browser-ready MP4 videos.

---

## Key Features
1. **Interactive Web Dashboard**: Input prompts, monitor compiler terminal logs, inspect generated python code, and watch the output video in a custom dark-mode interface.
2. **Dynamic Scene Parser**: Automatic regex analysis to extract scene class blueprints and target them during subprocess compiling.
3. **Prompt Cache / Replay**: LocalStorage-backed compilation history allows users to instantly reload previously generated animations and codes.
4. **Robust Guardrail System**: 14 strict formatting and architectural guardrails are embedded into the model instructions to prevent typical LLM compilation errors.

---

## Project Structure
```
Animation_Ai/
├── src/
│   ├── app.py                # Flask Web Server & API routes
│   ├── llm_client.py         # Gemini API Bridge & System Guardrails
│   ├── pipeline.py           # CLI Pipeline runner
│   └── static/               # Frontend Assets
│       ├── index.html        # Glassmorphic web panel
│       ├── style.css         # Styling, gradients, and micro-animations
│       └── app.js            # Client-side API orchestration & local history
├── media/                    # Output directory for compiled video frames
├── documentation.tex         # LaTeX full system documentation
├── requirements.txt          # Project python dependencies
└── README.md                 # This file
```

---

## Installation & Setup

### Prerequisites
Make sure the following system tools are installed on your computer:
* **Python 3.12+**
* **FFmpeg** (For video encoding: `choco install ffmpeg` or scoop)
* **LaTeX** (Optional, required if rendering complex formulas: MikTeX or TeX Live)

### Setup Steps
1. **Clone/Navigate** into the project workspace directory.
2. **Create and Activate a Virtual Environment**:
   ```bash
   # Windows PowerShell
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Windows Command Prompt
   .\venv\Scripts\activate.bat
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure environment variables**:
   Create a `.env` file in the root workspace folder:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

---

## Running the Application

### 1. Web Application (Recommended)
Launch the Flask local web server:
```bash
python src/app.py
```
Open your browser and navigate to **`http://localhost:5000`**. Enter a concept (e.g. *"explaining binary search visually"*), watch the terminal compile logs, and watch the resulting animation play directly in the browser.

### 2. Command Line Pipeline
To run a generation directly from your terminal:
```bash
python src/pipeline.py
```

---

## The Compilation Guardrail System

The platform maintains a list of **14 strict system guardrails** embedded in the LLM instruction prompts. These guardrails prevent syntax errors, rendering failures, and visual collisions:

1. **IndexError Prevention**: Never initialize completely empty text objects (like `Text("")`) and position them using `.next_to()`. Use at least a space placeholder: `Text(" ")`.
2. **Centering Validation**: Never call `.to_center()`. Always use `.move_to(ORIGIN)` or `.center()`.
3. **No Method Hallucination**: Only use standard, core methods (`.shift()`, `.scale()`, `.rotate()`, `.next_to()`, `.align_to()`, `.move_to()`).
4. **Self-Containment**: Ensure all custom imported modules and helpers are defined inside the single generated script file.
5. **Markdown Fencing**: Wrap the final script inside standard ```python ``` markdown fences.
6. **No Conversational Outro**: Output only the executable code block, with no conversational intros or warnings.
7. **Safe Numpy Comparison**: Never compare Manim direction vectors directly (e.g. `direction == DOWN`). Use `all(direction == DOWN)` or `np.array_equal()` to avoid array ambiguity exceptions.
8. **Text Collision Prevention**: Never write new text Mobjects directly on top of existing ones. Use `Transform` or `FadeOut` to clear previous logs.
9. **Screen Boundary Compliance**: Maintain horizontal array bounds within standard screen boundaries (width 14.2, height 8.0). Scale lists and keep buffer spacings between `0.1` and `0.2`.
10. **Color Constant Validation**: Avoid hallucinating constants (like `GREEN_SCREEN`). Stick to standard colors (`RED`, `GREEN`, `BLUE`, etc.) and shade weights.
11. **Mobject Visibility Safety**: Never call `.is_shown()` or `.is_visible()`. Track visibility states using boolean flags or by checking presence in `self.mobjects`.
12. **Text Ghosting Prevention**: Avoid repeated `Transform(explanation_text, Text(...))` calls. Update text smoothly using `self.play(explanation_text.animate.become(Text(...)))`.
13. **Centered & Vertically Symmetric Layout**: Keep the main array centered (`y=0`). Group header labels at the top (`y=2.2`) and pointers symmetrically above and below the cells with a matching buffer (e.g., `buff=0.4`).
14. **VGroup Element Check**: Never call `.is_empty()` on VGroups. Check length instead: `len(vgroup) == 0` or `if not vgroup:`.