import os
import re
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Load the environment variables from the .env file
load_dotenv()

# 2. Extract and check the API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError(
        "GEMINI_API_KEY is missing from your .env file! "
        "Please ensure your .env file contains: GEMINI_API_KEY=your_key_here"
    )

# 3. Initialize the Google GenAI Client
client = genai.Client(api_key=api_key)

def generate_manim_code(user_instruction: str) -> str:
    """
    Sends a query to Gemini (gemini-2.5-flash) to write Python code
    using the Manim library. Implements exponential backoff retries and strict guardrails.
    """
    system_instruction = (
        "You are an expert mathematical animator using Python's Manim library (Community Edition).\n"
        "Generate a complete, syntactically perfect Python script containing a Manim Scene class representing the animation requested.\n\n"
        "STRICT COMPILATION GUARDRAILS:\n"
        "1. NEVER initialize completely empty text objects like Text(\"\") or Tex(\"\") and then position them using .next_to() or .align_to(). "
        "This triggers a fatal IndexError. Always use at least a space, like Text(\" \"), or a visible placeholder string.\n"
        "2. NEVER use the non-existent '.to_center()' method on any object or VGroup. To center elements, use '.move_to(ORIGIN)' or '.center()'.\n"
        "3. Do not hallucinate or guess methods. Stick to core, standard Manim methods like .shift(), .scale(), .rotate(), .next_to(), .align_to(), and .move_to().\n"
        "4. Ensure all imported modules and custom classes (such as custom Mobjects) are fully defined within this single file.\n"
        "5. Wrap your entire output strictly inside a single code block using standard markdown: ```python ... ```\n"
        "6. Do not write any conversational intro or outro text, explanations, or warnings. Generate ONLY the code block.\n"
        "7. NEVER compare Manim direction vectors (like UP, DOWN, LEFT, RIGHT) directly using Python comparison operators (e.g., `direction == DOWN` or `if direction == UP:`). "
        "Since these are numpy arrays, this raises a ValueError ('The truth value of an array with more than one element is ambiguous'). "
        "Instead, check elements or use `all(direction == DOWN)` or `np.array_equal(direction, DOWN)`.\n"
        "8. NEVER write new text/explanation Mobjects directly on top of existing ones. When updating on-screen explanation/status texts, "
        "use `Transform` or explicitly `FadeOut` the old text before writing/fading in the new one. Place explanation/status text "
        "at the bottom edge of the screen using `.to_edge(DOWN, buff=0.5)` to avoid overlapping with array cells or pointers.\n"
        "9. Keep horizontal element layouts within the screen boundaries. A standard Manim screen has a width of 14.2 units and height of 8.0 units. "
        "When arranging sequences of objects horizontally (like arrays or lists), scale the elements and keep the spacing buffer small "
        "(e.g., `buff=0.1` to `0.2` rather than large values like `0.8`) to prevent objects from being cut off at the left and right edges.\n"
        "10. Do not hallucinate or guess color constants. Stick to standard Manim color constants (such as `RED`, `GREEN`, `BLUE`, `YELLOW`, `ORANGE`, `PURPLE`, `PINK`, `TEAL`, `WHITE`, `BLACK`, `GRAY`, or shades like `RED_A`, `GREEN_B`). Do NOT use non-existent constants like `GREEN_SCREEN` or `RED_SCREEN`.\n"
        "11. NEVER call non-existent methods like `.is_shown()` or `.is_visible()` on Mobjects to check if they are displayed on screen. "
        "Manim Mobjects do not track visibility this way. Instead, track visibility using a plain Python boolean flag (e.g., `mid_shown = False`) "
        "or check if the mobject is present in the scene list: `if my_mobject in self.mobjects:`.\n"
        "12. NEVER use `Transform(explanation_text, Text(...))` to update status texts repeatedly, as this leads to text ghosting/double-printing. "
        "Instead, update the text smoothly using `self.play(explanation_text.animate.become(Text(...)))`.\n"
        "13. Keep status labels (like `Target: X`) and high/low pointer groups vertically separated from the list cells. "
        "Group labels at the top using `.to_edge(UP, buff=0.5)` and shift the central array slightly down using `.shift(UP * 0.8)` or `.move_to(UP * 0.8)` to avoid overlaps.\n"
        "14. NEVER call non-existent methods like `.is_empty()` on VGroup or VMobject to check if they have sub-mobjects. "
        "Instead, check if the group has zero elements using `len(vgroup) == 0` or `if not vgroup:`."
    )


    # Exponential backoff parameters (up to 5 retries: 1s, 2s, 4s, 8s, 16s)
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_instruction,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,  # Keep it highly deterministic
                )
            )
            return response.text
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"\n[Error] API call failed after {max_retries} attempts: {e}")
                return ""
            time.sleep(2 ** attempt)  # Delays of 1s, 2s, 4s, 8s...

def extract_python_code(raw_response: str) -> str:
    """
    Parses out code block delimiters like ```python and ``` to return
    only clean Python code.
    """
    pattern = r"```python\s*(.*?)\s*```"  
    match = re.search(pattern, raw_response, re.DOTALL)  
    if match:  
        return match.group(1).strip()  
    return raw_response.strip()  

def save_code_to_file(code_content: str, filepath: str = "generated_scene.py") -> None:  
    """  
    Overwrites or creates a new file to store the parsed Python script.  
    """  
    try:  
        with open(filepath, "w", encoding="utf-8") as f:  
            f.write(code_content)  
        print(f"\n[Success] Executable Manim animation code successfully saved to: '{filepath}'")  
    except IOError as e:  
        print(f"\n[File Error] Could not write Python code to file: {e}")  

if __name__ == "__main__":  
    print("==========================================================")  
    print(" AI EDUCATIONAL ANIMATION PLATFORM (WEEK 1 LLM BRIDGE) ")  
    print("==========================================================")  

    # Get interactive prompt input directly in your VS Code terminal  
    user_prompt = input("\nEnter your animation concept (e.g. 'Show a blue circle expanding '): ")
    
    if not user_prompt.strip():
        user_prompt = "Create a blue circle in the center that morphs into a yellow square."
        print(f"Using default prompt: '{user_prompt}'")

    print("\nContacting Gemini to generate animation logic...")
    raw_response = generate_manim_code(user_prompt)

    if raw_response:
        print("\n--- Raw Response Received ---")
        print(raw_response)
        print("-----------------------------")

        # Clean and save the response
        clean_code = extract_python_code(raw_response)
        save_code_to_file(clean_code, "generated_scene.py")
    else:
        print("\n[Pipeline Failed] No output was received. Please check your .env API key and connection.")