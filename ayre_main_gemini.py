import os
import sys
import re
import webbrowser  # Add this import
import dotenv
import google.generativeai as genai
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from pyfiglet import Figlet
from pathlib import Path
import threading
import queue
from rich.table import Table

from ayre_modules.ayre_file_handler import FileHandler
from ayre_modules.ayre_gui import start_gui
from ayre_modules.ayre_chat_manager import ChatManager
from ayre_modules.ayre_web_handler import WebContentHandler

File_uploads = False
# Load environment variables
dotenv.load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)
console = Console()

# Global state
file_queue = queue.Queue()
gui_thread = None


#non-func req
def display_ans_file(filepath):
    """Display ANSI art file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            ansi_content = f.read().replace("\\x1b", "\x1b").replace("\\e", "\x1b")
            print(ansi_content)
    except:
        pass

def print_header():
    """Print stylized header"""
    figlet = Figlet(font='slant')
    header = figlet.renderText("AYRE")
    from rich.text import Text
    
    text = Text()
    for char in header:
        if char in "_|":
            text.append(char, style="#ff4b4b")
        elif char in "/\\-":
            text.append(char, style="#800000")
        elif char.strip() == "":
            text.append(char)
        else:
            text.append(char, style="#b22222")
    
    console.print(text)
    console.print("[italic #ff4b4b]Your Resonant AI Companion (Gemini)[/italic #ff4b4b]\n")

def print_tips():
    """Print usage tips"""
    tips = (
        "[bold #ff4b4b]Welcome, Raven.[/bold #ff4b4b]\n"
        "1. Ask questions about Armored Core, Ayre, or anything else.\n"
        "2. [bold]Drag & drop[/bold] files into terminal or use [bold]gui[/bold] command\n"
        "3. Commands: [bold]upload[/bold], [bold]analyze[/bold], [bold]context[/bold], [bold]gui[/bold]\n"
        "4. Chat commands: [bold]chats[/bold], [bold]newchat[/bold], [bold]loadchat[/bold], [bold]deletechat[/bold], [bold]history[/bold]\n"
        "5. Link commands: [bold]open <url>[/bold] or paste URLs directly to open them\n"
        "6. Type [bold]help[/bold] for detailed command reference or [bold]exit[/bold] to leave the resonance."
    )
    console.print(Panel(tips, title="[bold #b22222]Getting Started[/bold #b22222]", border_style="#ff4b4b"))


#func req

# chat
def chat_with_gemini(user_input, message_history):
    """Chat with Gemini AI"""
    prompt = ""
    for msg in message_history:
        if msg["role"] == "system":
            prompt += f"{msg['content']}\n"
        elif msg["role"] == "user":
            prompt += f"Raven: {msg['content']}\n"
        elif msg["role"] == "assistant":
            prompt += f"Ayre: {msg['content']}\n"
    prompt += f"Raven: {user_input}\nAyre:"

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    reply = response.text.strip()
    
    message_history.append({"role": "user", "content": user_input})
    message_history.append({"role": "assistant", "content": reply})
    
    # Check for links in the response
    detect_and_open_links(reply)
    
    return reply

# show help page
def show_help():
    """Display comprehensive help for all commands"""
    console.print("\n")
    console.print(Panel(
        "[bold #ff4b4b]AYRE Command Reference[/bold #ff4b4b]\n[italic]Your guide to resonating with the AI companion[/italic]",
        border_style="#ff4b4b"
    ))
    
    # Chat Management Commands
    chat_table = Table(title="💬 Chat Management", border_style="#ff4b4b")
    chat_table.add_column("Command", style="#ffffff", no_wrap=True)
    chat_table.add_column("Arguments", style="#00ff00")
    chat_table.add_column("Description", style="#888888")
    
    chat_table.add_row("chats", "", "List all available chat sessions")
    chat_table.add_row("newchat", "[name]", "Create new chat (optional custom name)")
    chat_table.add_row("loadchat", "<name>", "Load an existing chat session")
    chat_table.add_row("deletechat", "<name>", "Delete a chat (with confirmation)")
    chat_table.add_row("history", "[limit]", "Show recent messages (default: 10)")
    
    console.print(chat_table)
    console.print()
    
    # File Management Commands
    file_table = Table(title="📁 File Management", border_style="#ff4b4b")
    file_table.add_column("Command", style="#ffffff", no_wrap=True)
    file_table.add_column("Arguments", style="#00ff00")
    file_table.add_column("Description", style="#888888")
    
    file_table.add_row("upload", "<file_path>", "Upload and analyze a file")
    file_table.add_row("analyze", "<file_path>", "Deep analysis of file content")
    file_table.add_row("context", "<file_path>", "Add file to conversation context")
    file_table.add_row("gui", "", "Open graphical file interface")
    file_table.add_row("drag & drop", "file_path", "Drop files directly into terminal")
    
    console.print(file_table)
    console.print()
    
    link_table = Table(title="🔗 Link Management", border_style="#ff4b4b")
    link_table.add_column("Command", style="#ffffff", no_wrap=True)
    link_table.add_column("Arguments", style="#00ff00")
    link_table.add_column("Description", style="#888888")
    
    link_table.add_row("open", "<url>", "Open URL (option to analyze content)")
    link_table.add_row("analyze", "<url> [question]", "Analyze web page content with AI")
    link_table.add_row("https://...", "", "Auto-detect URLs (choose open/analyze)")
    link_table.add_row("Auto-detect", "", "Links in responses are auto-detected")
    
    console.print(link_table)
    console.print()
    
    # System Commands
    system_table = Table(title="⚙️ System Commands", border_style="#ff4b4b")
    system_table.add_column("Command", style="#ffffff", no_wrap=True)
    system_table.add_column("Arguments", style="#00ff00")
    system_table.add_column("Description", style="#888888")
    
    system_table.add_row("help", "", "Show this command reference")
    system_table.add_row("exit", "", "Save and exit AYRE")
    system_table.add_row("quit", "", "Save and exit AYRE")
    
    console.print(system_table)
    console.print()
    
    # Usage Examples
    examples = """[bold #ff4b4b]📝 Usage Examples:[/bold #ff4b4b]

[bold green]Chat Management:[/bold green]
• [cyan]newchat project_analysis[/cyan] - Create chat named "project_analysis"
• [cyan]chats[/cyan] - List all chats
• [cyan]loadchat project_analysis[/cyan] - Switch to that chat
• [cyan]history 20[/cyan] - Show last 20 messages
• [cyan]deletechat old_chat[/cyan] - Delete "old_chat"

[bold green]File Operations:[/bold green]
• [cyan]upload C:\\Users\\me\\document.pdf[/cyan] - Upload and analyze PDF
• [cyan]analyze code.py[/cyan] - Deep analysis of Python file
• [cyan]context data.json[/cyan] - Add JSON to conversation context
• [cyan]gui[/cyan] - Open file browser interface

[bold green]Web Analysis:[/bold green]
• [cyan]analyze https://github.com/user/repo[/cyan] - Analyze GitHub repo page
• [cyan]analyze https://docs.python.org What is asyncio?[/cyan] - Ask specific question
• [cyan]https://stackoverflow.com/questions/123[/cyan] - Auto-detect and choose action
• [cyan]open https://example.com[/cyan] - Open with option to analyze

[bold green]General Usage:[/bold green]
• Simply type questions: [cyan]"How does this code work?"[/cyan]
• Drag files directly into the terminal window
• Chat naturally - Ayre understands context from uploaded files
• Web content is automatically integrated into conversation context"""
    
    console.print(Panel(examples, border_style="#888888"))
    
    # File Types
    file_types = """[bold #ff4b4b]📋 Supported File Types:[/bold #ff4b4b]

[bold green]Images:[/bold green] .jpg, .jpeg, .png, .gif, .webp, .bmp
[bold green]Code:[/bold green] .py, .js, .html, .css, .cpp, .java, .c, .go, .rs
[bold green]Documents:[/bold green] .pdf, .txt, .md, .doc, .docx
[bold green]Data:[/bold green] .json, .xml, .csv, .yaml, .yml
[bold green]Archives:[/bold green] .zip (contents will be analyzed)"""
    
    console.print(Panel(file_types, border_style="#888888"))

def process_gui_queue(file_handler, message_history):
    """Process files from GUI queue"""
    try:
        while not file_queue.empty():
            action, file_path = file_queue.get_nowait()
            if action == "process":
                file_handler.process_file_auto(file_path, message_history)
    except queue.Empty:
        pass

def detect_and_open_links(text):
    """Detect and open links in text"""
    # URL regex pattern
    url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w)*)?)?'
    
    urls = re.findall(url_pattern, text, re.IGNORECASE)
    
    if urls:
        console.print(f"[cyan]🔗 Found {len(urls)} link(s):[/cyan]")
        for i, url in enumerate(urls, 1):
            console.print(f"[cyan]{i}. {url}[/cyan]")
        
        if len(urls) == 1:
            # Auto-open single link with confirmation
            response = console.input(f"[yellow]Open this link? (y/N): [/yellow]")
            if response.lower() == 'y':
                try:
                    webbrowser.open(urls[0])
                    console.print(f"[green]✓ Opened: {urls[0]}[/green]")
                except Exception as e:
                    console.print(f"[red]❌ Failed to open link: {e}[/red]")
        else:
            # Multiple links - let user choose
            response = console.input(f"[yellow]Open which link? (1-{len(urls)}, 'all', or Enter to skip): [/yellow]")
            
            if response.lower() == 'all':
                for url in urls:
                    try:
                        webbrowser.open(url)
                        console.print(f"[green]✓ Opened: {url}[/green]")
                    except Exception as e:
                        console.print(f"[red]❌ Failed to open {url}: {e}[/red]")
            elif response.isdigit():
                try:
                    index = int(response) - 1
                    if 0 <= index < len(urls):
                        webbrowser.open(urls[index])
                        console.print(f"[green]✓ Opened: {urls[index]}[/green]")
                    else:
                        console.print("[red]Invalid link number[/red]")
                except Exception as e:
                    console.print(f"[red]❌ Failed to open link: {e}[/red]")

def open_link_command(url):
    """Open a specific link via command"""
    # Clean up the URL
    url = url.strip()
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        webbrowser.open(url)
        console.print(f"[green]✓ Opened: {url}[/green]")
        return True
    except Exception as e:
        console.print(f"[red]❌ Failed to open link: {e}[/red]")
        return False


def analyze_web_content(url, user_question=None):
    """Analyze web content with AI"""
    web_handler = WebContentHandler(console)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    # Get current message history from chat manager
    # This is a simplified version - you might need to pass message_history as parameter
    temp_history = []
    
    result = web_handler.analyze_url_with_ai(url, user_question, temp_history, model)
    
    if result:
        console.print(Panel(Markdown(result), title="Web Content Analysis", border_style="cyan"))
    
    return result

def handle_commands(user_input, file_handler, message_history, chat_manager):
    """Handle special commands"""
    global gui_thread
    
    cmd = user_input.strip().lower()
    cmd_parts = user_input.strip().split()
    
    

    # Help command
    if cmd == "help":
        show_help()
        return True
    # Web analysis commands
    if cmd.startswith("analyze ") and any(user_input.strip().split()[1].startswith(proto) for proto in ['http://', 'https://']):
        if len(cmd_parts) > 1:
            url = cmd_parts[1]
            question = " ".join(cmd_parts[2:]) if len(cmd_parts) > 2 else None
            
            web_handler = WebContentHandler(console)
            model = genai.GenerativeModel("gemini-2.5-flash")
            result = web_handler.analyze_url_with_ai(url, question, message_history, model)
            
            if result:
                console.print(Panel(Markdown(result), title="Web Content Analysis", border_style="cyan"))
        return True
    
    # Link commands with analysis option
    if cmd.startswith("open "):
        if len(cmd_parts) > 1:
            url = " ".join(cmd_parts[1:])
            
            # Ask if user wants to analyze the content too
            response = console.input("[yellow]Also analyze the content? (y/N): [/yellow]")
            if response.lower() == 'y':
                web_handler = WebContentHandler(console)
                model = genai.GenerativeModel("gemini-2.5-flash")
                web_handler.analyze_url_with_ai(url, None, message_history, model)
            
            open_link_command(url)
        else:
            console.print("[red]Usage: open <url>[/red]")
        return True
    
    # Check if input looks like a URL
    if re.match(r'https?://', user_input.strip(), re.IGNORECASE):
        url = user_input.strip()
        
        # Ask what to do with the URL
        console.print(f"[cyan]🔗 URL detected: {url}[/cyan]")
        action = console.input("[yellow]Choose action - [O]pen, [A]nalyze, or [B]oth (O/A/B): [/yellow]").lower()
        
        if action == 'a':
            web_handler = WebContentHandler(console)
            model = genai.GenerativeModel("gemini-2.5-flash")
            result = web_handler.analyze_url_with_ai(url, None, message_history, model)
            if result:
                console.print(Panel(Markdown(result), title="Web Content Analysis", border_style="cyan"))
        elif action == 'b':
            open_link_command(url)
            web_handler = WebContentHandler(console)
            model = genai.GenerativeModel("gemini-2.5-flash")
            web_handler.analyze_url_with_ai(url, None, message_history, model)
        else:  # Default to open
            open_link_command(url)
        
        return True
    
    # Chat management commands
    if cmd == "chats":
        chat_manager.list_chats()
        return True
    
    elif cmd == "newchat":
        chat_name = None
        if len(cmd_parts) > 1:
            chat_name = " ".join(cmd_parts[1:])
        new_history = chat_manager.create_new_chat(chat_name)
        if new_history:
            message_history.clear()
            message_history.extend(new_history)
        return True
    
    elif cmd.startswith("loadchat "):
        if len(cmd_parts) > 1:
            chat_name = " ".join(cmd_parts[1:])
            loaded_history = chat_manager.load_chat(chat_name)
            if loaded_history:
                message_history.clear()
                message_history.extend(loaded_history)
        else:
            console.print("[red]Usage: loadchat <chat_name>[/red]")
        return True
    
    elif cmd.startswith("deletechat "):
        if len(cmd_parts) > 1:
            chat_name = " ".join(cmd_parts[1:])
            delete_result = chat_manager.delete_chat(chat_name)
            if delete_result == "load_latest":
                # Deleted current chat, load the latest remaining one
                new_history = chat_manager.load_latest_chat()
                message_history.clear()
                message_history.extend(new_history)
        else:
            console.print("[red]Usage: deletechat <chat_name>[/red]")
        return True
    
    elif cmd == "history":
        limit = 10
        if len(cmd_parts) > 1:
            try:
                limit = int(cmd_parts[1])
            except ValueError:
                console.print("[red]Invalid number for history limit[/red]")
                return True
        chat_manager.show_chat_history(limit)
        return True
    
    # GUI command
    if cmd == "gui" and File_uploads:
        if gui_thread is None or not gui_thread.is_alive():
            console.print("[cyan]🖥️ Opening GUI interface...[/cyan]")
            gui_thread = threading.Thread(target=start_gui, args=(file_queue,), daemon=True)
            gui_thread.start()
        else:
            console.print("[yellow]GUI is already running![/yellow]")
        return True
    elif cmd == "gui":
        console.print(f"[red]File upload is disabled.[/red]")
        return True
    
    # File commands
    if user_input.startswith(("upload ", "analyze ", "context ")):
        return file_handler.handle_command(user_input, message_history)
    
    # Check for drag & drop
    return file_handler.handle_file_input(user_input, message_history)

def main():
    # Initialize
    display_ans_file("ayre_img.ans")
    print_header()
    print_tips()
    console.print("")
    
    # Initialize chat manager
    chat_manager = ChatManager(console)
    
    # Load the latest chat instead of creating new one
    message_history = chat_manager.load_latest_chat()
    file_handler = FileHandler(console)
    
    while True:
        try:
            # Process GUI files
            process_gui_queue(file_handler, message_history)
            
            # Save current chat after each interaction
            chat_manager.save_current_chat(message_history)
            
            user_input = console.input("[bold green]Raven >[/bold green] ")
            
            if user_input.strip().lower() in {"exit", "quit"}:
                # Save before exiting
                chat_manager.save_current_chat(message_history)
                console.print("\n[bold red]Ayre's resonance fades. Until next time, Raven.[/bold red]")
                break
            
            # Skip empty inputs
            if not user_input.strip():
                continue
            
            # Handle commands and files
            if handle_commands(user_input, file_handler, message_history, chat_manager):
                continue
            
            # Regular chat with improved error handling
            try:
                reply = chat_with_gemini(user_input, message_history)
                if reply:
                    console.print(Panel(Markdown(reply), title="Ayre", border_style="magenta"))
                else:
                    console.print("[yellow]⚠️ No response received. Please try again.[/yellow]")
            except Exception as chat_error:
                console.print(f"[red]❌ Chat error: {chat_error}[/red]")
                console.print("[yellow]💡 Try checking your internet connection and API key[/yellow]")
            
        except KeyboardInterrupt:
            # Save before exiting
            chat_manager.save_current_chat(message_history)
            console.print("\n[bold magenta]Ayre's resonance interrupted. Farewell, Raven.[/bold magenta]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            console.print("[yellow]💡 The conversation continues...[/yellow]")

if __name__ == "__main__":
    main()