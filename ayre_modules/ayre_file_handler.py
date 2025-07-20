import google.generativeai as genai
from rich.markdown import Markdown
from rich.panel import Panel
from pathlib import Path

class FileHandler:
    def __init__(self, console):
        self.console = console
        self.model = genai.GenerativeModel("gemini-2.5-flash")
    
    def upload_to_gemini(self, filepath):
        """Upload file to Gemini"""
        try:
            file = genai.upload_file(filepath)
            self.console.print(f"[green]✓ Uploaded: {filepath}[/green]")
            return file
        except Exception as e:
            self.console.print(f"[red]✗ Upload failed: {e}[/red]")
            return None
    
    def analyze_with_gemini(self, file_ref, prompt="Analyze this file"):
        """Analyze file with Gemini"""
        try:
            response = self.model.generate_content([prompt, file_ref])
            return response.text.strip()
        except Exception as e:
            return f"Analysis failed: {str(e)}"
    
    def add_code_context(self, filename, message_history):
        """Add code file as context"""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                code = f.read()
            message_history.append({
                "role": "user", 
                "content": f"Code from {filename}:\n{code}"
            })
            self.console.print(Panel(Markdown(f"```python\n{code}\n```"), 
                                   title=f"Context: {filename}", border_style="cyan"))
        except Exception as e:
            self.console.print(f"[red]Error reading {filename}: {e}[/red]")
    
    def process_file_auto(self, file_path, message_history):
        """Auto-process file based on type"""
        self.console.print(f"[cyan]📁 Processing: {Path(file_path).name}[/cyan]")
        
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
            file_ref = self.upload_to_gemini(file_path)
            if file_ref:
                analysis = self.analyze_with_gemini(file_ref, "Analyze this image in detail")
                self.console.print(Panel(Markdown(analysis), title="Ayre - Image Analysis", border_style="cyan"))
                message_history.extend([
                    {"role": "user", "content": f"Image: {file_path}"},
                    {"role": "assistant", "content": analysis}
                ])
        
        elif file_ext in ['.py', '.js', '.html', '.css', '.txt', '.md']:
            self.add_code_context(file_path, message_history)
        
        else:
            file_ref = self.upload_to_gemini(file_path)
            if file_ref:
                analysis = self.analyze_with_gemini(file_ref, "Analyze this file")
                self.console.print(Panel(Markdown(analysis), title="Ayre - File Analysis", border_style="cyan"))
                message_history.extend([
                    {"role": "user", "content": f"File: {file_path}"},
                    {"role": "assistant", "content": analysis}
                ])
    
    def handle_file_input(self, user_input, message_history):
        """Handle drag & drop file paths"""
        cleaned = user_input.strip().strip('"').strip("'")
        
        if Path(cleaned).exists() and Path(cleaned).is_file():
            self.process_file_auto(cleaned, message_history)
            return True
        return False
    
    def handle_command(self, user_input, message_history):
        """Handle file commands"""
        if user_input.startswith("upload "):
            filepath = user_input[7:].strip()
            if Path(filepath).exists():
                file_ref = self.upload_to_gemini(filepath)
                if file_ref:
                    prompt = self.console.input("[yellow]What should Ayre do with this file? [/yellow]")
                    analysis = self.analyze_with_gemini(file_ref, prompt)
                    self.console.print(Panel(Markdown(analysis), title="Ayre - Analysis", border_style="cyan"))
                    message_history.extend([
                        {"role": "user", "content": f"Uploaded: {filepath}"},
                        {"role": "assistant", "content": analysis}
                    ])
            else:
                self.console.print(f"[red]File not found: {filepath}[/red]")
            return True
        
        elif user_input.startswith("analyze "):
            filepath = user_input[8:].strip()
            if Path(filepath).exists():
                file_ref = self.upload_to_gemini(filepath)
                if file_ref:
                    analysis = self.analyze_with_gemini(file_ref, "Analyze this in detail")
                    self.console.print(Panel(Markdown(analysis), title="Ayre - Analysis", border_style="cyan"))
                    message_history.extend([
                        {"role": "user", "content": f"Analyzed: {filepath}"},
                        {"role": "assistant", "content": analysis}
                    ])
            else:
                self.console.print(f"[red]File not found: {filepath}[/red]")
            return True
        
        elif user_input.startswith("context "):
            filename = user_input[8:].strip()
            self.add_code_context(filename, message_history)
            return True
        
        return False