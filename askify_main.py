import os
import json
import time
import threading
import pyperclip
import sqlite3
import tkinter as tk
from tkinter import messagebox
from plyer import notification
from pystray import Icon as TrayIcon, Menu as TrayMenu, MenuItem as TrayMenuItem
from PIL import Image, ImageDraw
import requests
import re
import keyboard
import pyautogui
import numpy as np
import easyocr
import speech_recognition as sr
from tkinterdnd2 import TkinterDnD, DND_TEXT
import subprocess
import sys
import signal
import psutil
import time





# ========== CONFIG ==========
data_dir = os.path.join(os.getenv("APPDATA"), "Askify")
os.makedirs(data_dir, exist_ok=True)
APPP_NAME = "Askify"
api_path = os.path.join(data_dir, "serper_key.txt")
groq_path = os.path.join(data_dir, "groq_key.txt")



# file paths
gui_path_run=r"C:\Program Files\Askify\GUI\gui.pyw"
access_bin_path_run=r"C:\Program Files\Askify\Access\Access_bin.pyw"


MID_FILE = os.path.join(os.getenv("APPDATA"), APPP_NAME, "MID_Access.dat")


def kill_python_script(target_name):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline and any(target_name.lower() in part.lower() for part in cmdline):
                os.kill(proc.info['pid'], signal.SIGTERM)
                print(f"🛑 Killed: {proc.info['pid']} -> {' '.join(cmdline)}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if "python" in proc.info['name'].lower():
            print(proc.info)
    except:
        continue
        
def ask_user_and_run():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    answer = messagebox.askyesno("Confirmation", "Do you want to change the API keys?")

    if answer:
        print("✅ User selected YES. Running gui.py...")
        subprocess.run([sys.executable, gui_path_run], check = True)
    else:
        print("❌ User selected NO. Exiting.")

# Call it


def run_script(script_name):
    subprocess.run([sys.executable, script_name])
#for below logic
a = 0
while(a<2):
    if os.path.exists(MID_FILE):
        if not os.path.exists(api_path) or not os.path.exists(groq_path):
            print("✅ MID_Acess.dat found. Running GUI...")
            run_script(gui_path_run)
        break    
    elif(a==2):
        sys.exit(0)
    else:
        print("❌ MID_Acess.dat not found. Running access_bin.py to generate it...")
        run_script(access_bin_path_run)
        a=a+1
    time.sleep(3)

if not os.path.exists(api_path) or not os.path.exists(groq_path):
    sys.exit(0)

#== asks user if anything needed in modification of API keys
kill_python_script("bin_quiery.pyw")
ask_user_and_run()


try:
    with open(api_path, "r") as f:
        SERPER_API_KEY = f.read().strip()

    with open(groq_path, "r") as f:
        GROQ_API_KEY = f.read().strip()
except:
    print("")
    
DB_FILE = os.path.join(data_dir, "history.db")
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

reader = easyocr.Reader(['en'], gpu=False)
latest_question = None
latest_answer = None

# ========== GROQ + LLAMA ==========
import google.generativeai as genai

# ✅ Configure Gemini with GROQ_API_KEY (even though it's a Gemini key now)
genai.configure(api_key=GROQ_API_KEY)

def ask_gpt4(prompt, model="gemini-1.5-flash"):
    try:
        model_obj = genai.GenerativeModel(model)
        response = model_obj.generate_content(prompt)

        if hasattr(response, "text"):
            return response.text
        else:
            print("[Gemini Error] No text in response.")
            return "❌ Gemini returned an empty response."

    except Exception as e:
        print(f"[Gemini Exception] {e}")
        return f"Exception: {e}"



def ask_gemini(prompt):
    return ask_gpt4(prompt)

# ========== DB ==========
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        answer TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def save_history(q, a):
    global latest_question, latest_answer
    latest_question = q
    latest_answer = a
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO history (question, answer) VALUES (?, ?)", (q, a))
    conn.commit()
    conn.close()

# ========== SERPER ==========
def search_serper(query):
    try:
        if not query.strip():
            print("[Serper] Empty query, skipping API call.")
            return None

        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        body = {"q": query}
        response = requests.post("https://google.serper.dev/search", headers=headers, json=body)
        response.raise_for_status()
        data = response.json()
        if "organic" in data and len(data["organic"]):
            return data["organic"][0].get("snippet", "")
        else:
            return "No results found."
    except Exception as e:
        print(f"[Serper Error] {e}")
        return "❌ Serper failed. Check your query or API key."


def is_live_answer_query(text):
    keywords = ['who is', 'current', 'latest', 'president', 'prime minister', 'cm of',
                'capital of', 'weather', 'today', 'news', 'stock price', 'currency rate', 'exchange rate']
    return any(kw in text.lower() for kw in keywords)

# ========== POPUP =========
import tkinter as tk
import pyperclip
import threading
import re

def show_popup(title, message):
    def extract_code_blocks(text):
        code_blocks = re.findall(r"```(?:\w*\n)?(.*?)```", text, re.DOTALL)
        plain_text = re.sub(r"```(?:\w*\n)?(.*?)```", "", text, flags=re.DOTALL).strip()
        return plain_text, code_blocks

    def run_popup():
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.geometry("+20+650")
        root.configure(bg='white')

        def start_move(event): root._x, root._y = event.x_root, event.y_root
        def do_move(event):
            dx, dy = event.x_root - root._x, event.y_root - root._y
            x, y = root.winfo_x() + dx, root.winfo_y() + dy
            root.geometry(f"+{x}+{y}")
            root._x, root._y = event.x_root, event.y_root

        # === Wrapper with border ===
        bordered_wrapper = tk.Frame(root, bg='black', bd=2)
        bordered_wrapper.pack(fill='both', expand=True)

        # === Top scrollable area ===
        outer_frame = tk.Frame(bordered_wrapper, bg='white')
        outer_frame.pack(fill='both', expand=True)
        separator = tk.Frame(bordered_wrapper, height=1, bg='#DDDDDD')
        separator.pack(fill='x', side='bottom')

        # === Fixed bottom input bar ===
        bottom_frame = tk.Frame(bordered_wrapper, bg='white')
        bottom_frame.pack(side='bottom', fill='x')



        canvas = tk.Canvas(outer_frame, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white', padx=15, pady=10)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width - 15))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        drag_bar = tk.Frame(root, bg='black', height=8, cursor='fleur')
        drag_bar.place(relx=0, rely=0, relwidth=1.0)
        drag_bar.bind("<Button-1>", start_move)
        drag_bar.bind("<B1-Motion>", do_move)

        def close_popup(): root.destroy()
        def copy_full(): pyperclip.copy(message or "")

        floating_btns = tk.Frame(root, bg='white')
        floating_btns.place(relx=1.0, x=-5, y=5, anchor='ne')
        tk.Button(floating_btns, text="📋", command=copy_full, bg='white', fg='black',
                  font=('Arial', 10), borderwidth=0).pack(side='left', padx=2)
        tk.Button(floating_btns, text="×", command=close_popup, bg='white', fg='black',
                  font=('Arial', 12, 'bold'), borderwidth=0).pack(side='left')

        # Original context shown at top
        tk.Label(scrollable_frame, text=title, bg='white', font=('Arial', 10, 'bold')).pack(
            padx=10, pady=(15, 5), anchor='w')

        plain_text, code_blocks = extract_code_blocks(message or "")
        if plain_text:
            bubble_frame = tk.Frame(scrollable_frame, bg='white', bd=1, relief='solid')
            bubble_frame.pack(padx=10, pady=5, fill='both', expand=True)

            content_wrapper = tk.Frame(bubble_frame, bg='white', padx=10, pady=10)
            content_wrapper.pack(fill='both', expand=True)

            text_widget = tk.Text(content_wrapper, height=10, bg='white', fg='black',
                                  font=('Segoe UI', 10), wrap='word', relief='flat', borderwidth=0)
            text_widget.insert('1.0', plain_text)
            text_widget.config(state='disabled')
            text_widget.pack(fill='both', expand=True)




        for code in code_blocks:
            code_frame = tk.Frame(scrollable_frame, bg='#f5f5f5', bd=1, relief='solid')
            code_frame.pack(padx=10, pady=10, fill='both', expand=True)

            def copy_code(c=code.strip()):
                pyperclip.copy(c)

            copy_btn = tk.Button(code_frame, text="📋", command=copy_code,
                                 bg='#f5f5f5', fg='blue', borderwidth=0)
            copy_btn.pack(pady=(6, 0))

            inner_frame = tk.Frame(code_frame, bg='#f5f5f5')
            inner_frame.pack(padx=(5, 5), pady=(5, 10), fill='both', expand=True)

            code_text = tk.Text(inner_frame, height=10, bg='#f5f5f5', fg='black',
                                font=('Consolas', 10), wrap='none', relief='flat')
            code_text.insert('1.0', code.strip())
            code_text.config(state='disabled')
            code_text.pack(side='left', fill='both', expand=True)

            scrollbar_code = tk.Scrollbar(inner_frame, orient='vertical', command=code_text.yview)
            scrollbar_code.pack(side='right', fill='y')
            code_text.config(yscrollcommand=scrollbar_code.set)

        # === ChatGPT-style Input Box ===
        input_frame = tk.Frame(bottom_frame, bg='white', padx=10, pady=10)
        input_frame.pack(fill='x', pady=(10, 15), padx=10)

        entry_border = tk.Frame(input_frame, background='black', bd=1)
        entry_border.pack(side='left', fill='x', expand=True)

        entry = tk.Entry(entry_border, font=('Segoe UI', 10), bg='white', relief='flat')
        entry.pack(fill='x', padx=1, pady=1)

        def submit_query(event=None):
            user_query = entry.get().strip()
            if not user_query:
                return
            entry.delete(0, tk.END)

            full_context_prompt = f"{plain_text.strip()}\n\nFollow-up: {user_query}"
            response = search_serper(full_context_prompt) if is_live_answer_query(full_context_prompt) else ask_gemini(full_context_prompt)
            save_history(full_context_prompt, response)

            # Extract model response parts
            resp_text, resp_code_blocks = extract_code_blocks(response)

            # === Display User Query ===
            bubble_frame = tk.Frame(scrollable_frame, bg='white', bd=1, relief='solid', padx=10, pady=10)
            bubble_frame.pack(padx=10, pady=5, fill='x', anchor='w')

            tk.Label(bubble_frame, text=f"🧠 You: {user_query}", bg='white',
                     font=('Segoe UI', 10, 'italic'), fg='gray', wraplength=580, justify='left').pack(anchor='w', pady=(0, 5))

            # === Display Plain Text Answer ===
            if resp_text:
                text_widget = tk.Text(bubble_frame, height=10, bg='white', fg='black',
                                      font=('Segoe UI', 10), wrap='word', relief='flat', borderwidth=0)
                text_widget.insert('1.0', resp_text)
                text_widget.config(state='disabled')
                text_widget.pack(padx=10, pady=(0, 5), fill='both', expand=True)

            # === Display Code Blocks (with scrollbars) ===
            for code in resp_code_blocks:
                code_frame = tk.Frame(scrollable_frame, bg='#f5f5f5', bd=1, relief='solid')
                code_frame.pack(padx=10, pady=10, fill='x', anchor='w')

                def copy_code(c=code.strip()):
                    pyperclip.copy(c)

                copy_btn = tk.Button(code_frame, text="📋", command=copy_code,
                                     bg='#f5f5f5', fg='blue', borderwidth=0)
                copy_btn.pack(pady=(6, 0), anchor='ne')

                inner_frame = tk.Frame(code_frame, bg='#f5f5f5')
                inner_frame.pack(padx=(5, 5), pady=(5, 10), fill='x', expand=True)

                scrollbar_y = tk.Scrollbar(inner_frame, orient='vertical')
                scrollbar_x = tk.Scrollbar(inner_frame, orient='horizontal')

                code_text = tk.Text(inner_frame, height=10, bg='#f5f5f5', fg='black',
                                    font=('Consolas', 10), wrap='none', relief='flat',
                                    yscrollcommand=scrollbar_y.set,
                                    xscrollcommand=scrollbar_x.set)

                code_text.insert('1.0', code.strip())
                code_text.config(state='disabled')
                code_text.pack(side='top', fill='x', expand=True)

                scrollbar_y.config(command=code_text.yview)
                scrollbar_y.pack(side='right', fill='y')

                scrollbar_x.config(command=code_text.xview)
                scrollbar_x.pack(side='bottom', fill='x')






        # Up-arrow styled submit button
        submit_btn = tk.Button(input_frame, text="↑", command=submit_query, bg='white',
                               fg='black', font=('Segoe UI', 12, 'bold'),
                               relief='flat', bd=1, width=3, height=1)
        submit_btn.pack(side='right', padx=(5, 0))
        entry.bind("<Return>", submit_query)

        root.mainloop()

    threading.Thread(target=run_popup).start()




# ========== CLIPBOARD ==========
def monitor_clipboard():
    last_text = ""
    while True:
        try:
            text = pyperclip.paste()
            if text != last_text and text.strip():
                last_text = text
                answer = search_serper(text) if is_live_answer_query(text) else ask_gemini(text)
                save_history(text, answer)
                show_popup("Answer", answer)
            time.sleep(2)
        except Exception as e:
            print(f"[Clipboard Error] {e}")
            time.sleep(5)

# ========== SCREENSHOT ==========
screenshot_region = None

def region_selector():
    global screenshot_region
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.attributes('-alpha', 0.3)
    root.config(cursor="cross")
    root.lift()
    root.focus_force()
    root.attributes("-topmost", True)

    canvas = tk.Canvas(root, cursor="cross")
    canvas.pack(fill=tk.BOTH, expand=True)
    rect = None
    start_x = start_y = 0
    def on_button_press(event): nonlocal start_x, start_y; start_x, start_y = event.x, event.y
    def on_move_press(event):
        nonlocal rect
        if rect: canvas.delete(rect)
        rect = canvas.create_rectangle(start_x, start_y, event.x, event.y, outline='red', width=2)
    def on_button_release(event):
        global screenshot_region
        x1, y1 = min(start_x, event.x), min(start_y, event.y)
        x2, y2 = max(start_x, event.x), max(start_y, event.y)
        screenshot_region = (x1, y1, x2 - x1, y2 - y1)
        root.quit()
        root.destroy()
    canvas.bind("<ButtonPress-1>", on_button_press)
    canvas.bind("<B1-Motion>", on_move_press)
    canvas.bind("<ButtonRelease-1>", on_button_release)
    root.mainloop()

def take_screenshot_and_process():
    global screenshot_region
    if not screenshot_region:
        print("No region selected.")
        return
    x, y, w, h = screenshot_region
    image = pyautogui.screenshot(region=(x, y, w, h))
    results = reader.readtext(np.array(image))
    text = " ".join([res[1] for res in results]).strip()
    if text:
        answer = search_serper(text) if is_live_answer_query(text) else ask_gemini(text)
        save_history(text, answer)
        show_popup("Answer from Screenshot", answer)
    else:
        print("No text detected.")

# ========== VOICE ==========
voice_mode = False
voice_buffer = []

def start_voice_input():
    global voice_mode, voice_buffer
    if not voice_mode:
        voice_mode = True
        voice_buffer = []
        threading.Thread(target=listen_voice, daemon=True).start()

def stop_voice_input():
    global voice_mode
    voice_mode = False
    print("[Voice] Voice capture stopped.")

def listen_voice():
    global voice_mode, voice_buffer, latest_question, latest_answer
    r = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("[Voice] Adjusting for ambient noise...")
            r.adjust_for_ambient_noise(source)
            print("[Voice] Listening started...")

            while voice_mode:
                try:
                    print("[Voice] Waiting for voice input...")
                    audio = r.listen(source, timeout=5, phrase_time_limit=10)
                    print("[Voice] Recognizing...")
                    text = r.recognize_google(audio)
                    print("[Voice] Heard:", text)
                    voice_buffer.append(text)
                except sr.WaitTimeoutError:
                    print("[Voice] Timeout, no speech detected.")
                    continue
                except sr.UnknownValueError:
                    print("[Voice] Could not understand audio.")
                    continue
                except Exception as e:
                    print(f"[Voice] Error during recognition: {e}")
                    continue

    except Exception as mic_error:
        print(f"[Voice] Microphone error: {mic_error}")
        voice_mode = False
        return

    # Process captured speech
    full_text = ' '.join(voice_buffer).strip()
    voice_buffer = []
    if full_text:
        print("[Voice] Final input:", full_text)
        answer = search_serper(full_text) if is_live_answer_query(full_text) else ask_gemini(full_text)
        save_history(full_text, answer)
        show_popup("Answer from Voice", answer)
        latest_question, latest_answer = full_text, answer
    else:
        print("[Voice] No valid input captured.")


# ========== DRAG-DROP ==========
def show_drag_popup():
    def on_drop(event):
        text = event.data.strip()
        root.destroy()
        if text:
            answer = search_serper(text) if is_live_answer_query(text) else ask_gemini(text)
            save_history(text, answer)
            show_popup("Answer from Drag-Drop", answer)

    root = TkinterDnD.Tk()
    root.title("Askify - Drag & Drop")
    root.geometry("400x100+600+350")
    root.configure(bg="#202020")
    root.attributes("-topmost", True)

    label = tk.Label(root, text="🟢 Drag text here", font=("Segoe UI", 14),
                     bg="#202020", fg="white")
    label.pack(expand=True, fill="both", padx=10, pady=10)

    label.drop_target_register(DND_TEXT)
    label.dnd_bind('<<Drop>>', on_drop)

    root.mainloop()


# ========== HOTKEYS ==========
def show_latest_popup():
    if latest_question and latest_answer:
        show_popup("Latest Answer", f"Q: {latest_question}\n\nA: {latest_answer}")
    else:
        show_popup("Latest Answer", "No data yet.")

def start_hotkeys():
    keyboard.add_hotkey('ctrl+shift+1', lambda: threading.Thread(target=region_selector).start())
    keyboard.add_hotkey('ctrl+shift+2', lambda: threading.Thread(target=take_screenshot_and_process).start())
    keyboard.add_hotkey('ctrl+shift+3', lambda: threading.Thread(target=show_drag_popup).start())
    keyboard.add_hotkey('ctrl+shift+4', show_latest_popup)
    keyboard.add_hotkey('ctrl+shift+5', start_voice_input)
    keyboard.add_hotkey('ctrl+shift+6', stop_voice_input)
    keyboard.wait()

# ========== SYSTEM TRAY ==========
def create_image():
    img = Image.new('RGB', (64, 64), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([16, 16, 48, 48], fill='green')
    return img

def on_quit(icon, item):
    icon.stop()
    os._exit(0)

def run_tray():
    icon = TrayIcon("Askify", create_image(), menu=TrayMenu(
        TrayMenuItem("Quit", on_quit)
    ))
    icon.run()

# ========== MAIN ==========
def main():
    print("[✔] Askify is running.")
    init_db()
    threading.Thread(target=monitor_clipboard, daemon=True).start()
    threading.Thread(target=start_hotkeys, daemon=True).start()
    run_tray()

if __name__ == "__main__":
    main()
