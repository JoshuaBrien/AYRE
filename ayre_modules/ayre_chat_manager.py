import json
import os
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

class ChatManager:
    def __init__(self, console):
        self.console = console
        self.chats_dir = Path("ayre_chats")
        self.chats_dir.mkdir(exist_ok=True)
        self.current_chat = None
        self.current_chat_file = None
    
    def get_latest_chat(self):
        """Get the most recently modified chat"""
        chat_files = list(self.chats_dir.glob("*.json"))
        
        if not chat_files:
            return None
        
        # Sort by modification time (most recent first)
        latest_file = max(chat_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)
            
            return latest_file, chat_data
        except Exception as e:
            self.console.print(f"[red]❌ Error reading latest chat: {e}[/red]")
            return None
    
    def load_latest_chat(self):
        """Load the most recently modified chat"""
        latest_chat = self.get_latest_chat()
        
        if not latest_chat:
            # No existing chats, create a new one
            return self.create_new_chat("default")
        
        chat_file, chat_data = latest_chat
        chat_name = chat_data.get("name", chat_file.stem)
        
        self.current_chat = chat_name
        self.current_chat_file = chat_file
        
        self.console.print(f"[green]✓ Loaded latest chat: '{chat_name}'[/green]")
        return chat_data["message_history"]
    
    def create_new_chat(self, chat_name=None):
        """Create a new chat session"""
        if not chat_name:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            chat_name = f"chat_{timestamp}"
        
        # Sanitize chat name
        chat_name = "".join(c for c in chat_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        chat_name = chat_name.replace(' ', '_')
        
        chat_file = self.chats_dir / f"{chat_name}.json"
        
        # Check if chat already exists
        counter = 1
        original_name = chat_name
        while chat_file.exists():
            chat_name = f"{original_name}_{counter}"
            chat_file = self.chats_dir / f"{chat_name}.json"
            counter += 1
        
        # Load system prompt
        try:
            with open("ayre_gemini.txt", "r", encoding="utf-8") as f:
                system_prompt = f.read().strip()
        except FileNotFoundError:
            system_prompt = "You are Ayre, an AI companion from Armored Core 6."
        
        # Create new chat data
        chat_data = {
            "name": chat_name,
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "message_history": [{"role": "system", "content": system_prompt}]
        }
        
        # Save chat
        with open(chat_file, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)
        
        self.current_chat = chat_name
        self.current_chat_file = chat_file
        
        self.console.print(f"[green]✓ Created new chat: '{chat_name}'[/green]")
        return chat_data["message_history"]
    
    def load_chat(self, chat_name):
        """Load an existing chat"""
        chat_file = self.chats_dir / f"{chat_name}.json"
        
        if not chat_file.exists():
            self.console.print(f"[red]❌ Chat '{chat_name}' not found![/red]")
            return None
        
        try:
            with open(chat_file, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)
            
            self.current_chat = chat_name
            self.current_chat_file = chat_file
            
            self.console.print(f"[green]✓ Loaded chat: '{chat_name}'[/green]")
            return chat_data["message_history"]
        
        except Exception as e:
            self.console.print(f"[red]❌ Error loading chat: {e}[/red]")
            return None
    
    def save_current_chat(self, message_history):
        """Save current chat to file"""
        if not self.current_chat_file:
            return
        
        try:
            with open(self.current_chat_file, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)
            
            chat_data["message_history"] = message_history
            chat_data["last_modified"] = datetime.now().isoformat()
            
            with open(self.current_chat_file, 'w', encoding='utf-8') as f:
                json.dump(chat_data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            self.console.print(f"[red]❌ Error saving chat: {e}[/red]")
    
    def list_chats(self):
        """Display all available chats"""
        chat_files = list(self.chats_dir.glob("*.json"))
        
        if not chat_files:
            self.console.print("[yellow]No chats found. Use 'newchat' to create one![/yellow]")
            return
        
        table = Table(title="💬 Available Chats", border_style="#ff4b4b")
        table.add_column("Name", style="#ffffff", no_wrap=True)
        table.add_column("Created", style="#888888")
        table.add_column("Last Modified", style="#888888")
        table.add_column("Messages", style="#00ff00", justify="right")
        table.add_column("Current", style="#ff4b4b", justify="center")
        
        for chat_file in sorted(chat_files, key=lambda f: f.stat().st_mtime, reverse=True):
            try:
                with open(chat_file, 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)
                
                name = chat_data.get("name", chat_file.stem)
                created = chat_data.get("created", "Unknown")
                if created != "Unknown":
                    created = datetime.fromisoformat(created).strftime("%Y-%m-%d %H:%M")
                
                last_modified = chat_data.get("last_modified", "Unknown")
                if last_modified != "Unknown":
                    last_modified = datetime.fromisoformat(last_modified).strftime("%Y-%m-%d %H:%M")
                
                # Count non-system messages
                message_count = len([msg for msg in chat_data.get("message_history", []) 
                                   if msg.get("role") != "system"])
                
                is_current = "●" if self.current_chat == name else ""
                
                table.add_row(name, created, last_modified, str(message_count), is_current)
            
            except Exception as e:
                table.add_row(chat_file.stem, "Error", "Error", "?", "")
        
        self.console.print(table)
    
    def delete_chat(self, chat_name):
        """Delete a chat"""
        chat_file = self.chats_dir / f"{chat_name}.json"
        
        if not chat_file.exists():
            self.console.print(f"[red]❌ Chat '{chat_name}' not found![/red]")
            return False
        
        # Confirm deletion
        response = self.console.input(f"[yellow]⚠️  Delete chat '{chat_name}'? (y/N): [/yellow]")
        if response.lower() != 'y':
            self.console.print("[cyan]Deletion cancelled.[/cyan]")
            return False
        
        try:
            chat_file.unlink()
            
            # If we deleted the current chat, load the latest remaining chat
            if self.current_chat == chat_name:
                self.current_chat = None
                self.current_chat_file = None
                # Try to load the next most recent chat
                return "load_latest"
            
            self.console.print(f"[green]✓ Deleted chat: '{chat_name}'[/green]")
            return True
        
        except Exception as e:
            self.console.print(f"[red]❌ Error deleting chat: {e}[/red]")
            return False
    
    def show_chat_history(self, limit=10):
        """Show recent messages from current chat"""
        if not self.current_chat:
            self.console.print("[yellow]No chat loaded. Use 'chats' to see available chats or 'newchat' to create one.[/yellow]")
            return
        
        try:
            with open(self.current_chat_file, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)
            
            messages = chat_data.get("message_history", [])
            # Filter out system messages for display
            user_messages = [msg for msg in messages if msg.get("role") != "system"]
            
            if not user_messages:
                self.console.print("[yellow]No messages in current chat yet.[/yellow]")
                return
            
            # Show last N messages
            recent_messages = user_messages[-limit:]
            
            self.console.print(Panel(
                f"[bold #ff4b4b]Chat History: {self.current_chat}[/bold #ff4b4b]",
                border_style="#ff4b4b"
            ))
            
            for msg in recent_messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                
                if role == "user":
                    self.console.print(f"[bold green]Raven:[/bold green] {content}")
                elif role == "assistant":
                    self.console.print(Panel(
                        Markdown(content), 
                        title="Ayre", 
                        border_style="magenta"
                    ))
                self.console.print()
        
        except Exception as e:
            self.console.print(f"[red]❌ Error reading chat history: {e}[/red]")