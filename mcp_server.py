import os
import subprocess
import psutil
import json
from datetime import datetime
from fastmcp import FastMCP

# Create an MCP server named "Loopi System Tools"
mcp = FastMCP("Loopi System Tools")

@mcp.tool()
def run_command(command: str) -> str:
    """Execute a bash command on the local system and return the output."""
    print(f"\n⚡ [Loopi Terminal]: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Limit printed output to keep console tidy
        output_snippet = result.stdout.strip()[:200] + "..." if len(result.stdout) > 200 else result.stdout.strip()
        print(f"✅ [Terminal Output]: {output_snippet}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ [Terminal Error]: {e.stderr.strip()}")
        return f"Error executing command: {e.stderr}"
    except Exception as e:
        print(f"❌ [Terminal Error]: {str(e)}")
        return f"Unexpected error: {str(e)}"

@mcp.tool()
def read_file(path: str) -> str:
    """Read the contents of a local file."""
    print(f"\n📖 [Loopi reading file]: {path}")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"✅ [File Read Success]: {len(content)} characters read")
            return content
    except Exception as e:
        print(f"❌ [File Read Error]: {str(e)}")
        return f"Error reading file: {str(e)}"

@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write contents to a local file. Overwrites if it exists."""
    print(f"\n✍️ [Loopi writing file]: {path}")
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ [File Write Success]: {len(content)} characters saved")
        return f"Successfully wrote to {path}"
    except Exception as e:
        print(f"❌ [File Write Error]: {str(e)}")
        return f"Error writing file: {str(e)}"

@mcp.tool()
def list_directory(path: str = ".") -> str:
    """List the contents of a directory."""
    try:
        items = os.listdir(path)
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

@mcp.tool()
def get_system_status() -> str:
    """Get the current system status including CPU, Memory, and Time."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        status = (
            f"Current Time: {current_time}\n"
            f"CPU Usage: {cpu_percent}%\n"
            f"Memory Usage: {memory.percent}% ({memory.used / (1024**3):.2f} GB / {memory.total / (1024**3):.2f} GB)"
        )
        return status
    except Exception as e:
        return f"Error getting system status: {str(e)}"

@mcp.tool()
def open_application(app_name: str) -> str:
    """Open a macOS application by name (e.g., 'Safari', 'Spotify')."""
    print(f"\n📱 [Loopi launching app]: {app_name}")
    try:
        subprocess.run(["open", "-a", app_name], check=True)
        print(f"✅ [Launch Success]")
        return f"Successfully opened {app_name}."
    except subprocess.CalledProcessError:
        print(f"❌ [Launch Failed]")
        return f"Failed to open application: {app_name}. It might not be installed."

@mcp.tool()
def set_volume(level: int) -> str:
    """Set the Mac system volume (0 to 100)."""
    try:
        level = max(0, min(100, level))
        script = f"set volume output volume {level}"
        subprocess.run(["osascript", "-e", script], check=True)
        return f"Volume set to {level}%."
    except Exception as e:
        return f"Error setting volume: {str(e)}"

@mcp.tool()
def take_screenshot(filename: str = "screenshot.png") -> str:
    """Take a screenshot of the main screen and save it to the desktop."""
    print(f"\n📸 [Loopi capturing screen]")
    try:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
        subprocess.run(["screencapture", desktop_path], check=True)
        print(f"✅ [Screenshot saved]: {desktop_path}")
        return f"Screenshot saved to {desktop_path}."
    except Exception as e:
        print(f"❌ [Screenshot error]: {str(e)}")
        return f"Error taking screenshot: {str(e)}"

import requests
from bs4 import BeautifulSoup

@mcp.tool()
def web_search(query: str, max_results: int = 3) -> str:
    """Search the web for real-time information and facts."""
    print(f"\n🔍 [Loopi web search]: \"{query}\"")
    url = f"https://search.yahoo.com/search?p={query}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        results = []
        # Look for search result blocks (Yahoo class "ddAlgo" or similar)
        for item in soup.find_all('div', class_='ddAlgo'):
            title_el = item.find('h3', class_='title') or item.find('a')
            desc_el = item.find('div', class_='compText') or item.find('span', class_='fc-2nd')
            
            if title_el and desc_el:
                results.append({
                    'title': title_el.get_text().strip(),
                    'snippet': desc_el.get_text().strip()
                })
            if len(results) >= max_results:
                break
                
        # Fallback parsing strategy if Yahoo updates their DOM classes
        if not results:
            for item in soup.find_all('div', class_='compTitle'):
                title_el = item.find('a')
                parent = item.find_parent('div')
                desc_el = parent.find('div', class_='compText') if parent else None
                
                if title_el and desc_el:
                    results.append({
                        'title': title_el.get_text().strip(),
                        'snippet': desc_el.get_text().strip()
                    })
                if len(results) >= max_results:
                    break
                    
        if not results:
            return "No search results could be retrieved from Yahoo at this time."
            
        formatted_results = "\n\n".join([f"Title: {r['title']}\nSnippet: {r['snippet']}" for r in results])
        return formatted_results
        
    except Exception as e:
        return f"Error searching the web: {str(e)}"

# JSON Contact Storage Setup
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CONTACTS_FILE = os.path.join(PROJECT_DIR, "contacts.json")

def _load_contacts():
    if not os.path.exists(CONTACTS_FILE):
        default_contacts = {
            "gokul": "gokul@gmail.com",
            "revathi": "revathisuresh130@gmail.com"
        }
        try:
            with open(CONTACTS_FILE, 'w') as f:
                json.dump(default_contacts, f, indent=4)
            return default_contacts
        except Exception:
            return {}
    try:
        with open(CONTACTS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def _save_contacts(contacts):
    try:
        with open(CONTACTS_FILE, 'w') as f:
            json.dump(contacts, f, indent=4)
        return True
    except Exception:
        return False

def _normalize_name(name: str) -> str:
    name_lower = name.lower().strip()
    if name_lower in ["google", "googles", "goku", "go call", "gocal"]:
        return "gokul"
    if name_lower in ["revity", "gravity", "ravathi", "revati"]:
        return "revathi"
    return name_lower

@mcp.tool()
def prompt_user_input(prompt_message: str) -> str:
    """Prompt the user in the terminal console to type an input (e.g., to type an email address, password, or any text that is hard to say)."""
    print(f"\n💬 [Loopi Prompt]: {prompt_message}")
    try:
        user_input = input("👉 Enter input: ").strip()
        print(f"✅ [User Input Received]: {user_input}")
        return user_input
    except Exception as e:
        return f"Error getting input: {str(e)}"

@mcp.tool()
def search_contact(name: str) -> str:
    """Search for a contact's email address by name. Supports partial matching."""
    name_query = _normalize_name(name)
    print(f"\n📞 [Loopi looking up contact]: {name_query} (original: '{name}')")
    
    # Direct Email Check: If query itself contains an email format, return it directly
    if "@" in name_query and "." in name_query:
        print(f"✅ [Direct Email Detected]: {name_query}")
        return json.dumps({name_query: name_query})
        
    contacts = _load_contacts()
    
    matches = {}
    for contact_name, email in contacts.items():
        # Match keys (name) or check if name exists inside the email address value
        if name_query in contact_name.lower() or contact_name.lower() in name_query:
            matches[contact_name] = email
        elif name_query in email.lower():
            matches[contact_name] = email
            
    if not matches:
        print(f"❌ [Contact lookup failed]: No match found for '{name}'")
        return f"No contact found for '{name}'."
        
    print(f"✅ [Contact lookup success]: Found {len(matches)} match(es): {matches}")
    return json.dumps(matches)

@mcp.tool()
def add_contact(name: str, email: str) -> str:
    """Save a new contact or update an existing contact's email address."""
    name_clean = _normalize_name(name)
    email_clean = email.strip().lower()
    print(f"\n👤 [Loopi adding contact]: {name_clean} -> {email_clean} (original: '{name}')")
    contacts = _load_contacts()
    contacts[name_clean] = email_clean
    if _save_contacts(contacts):
        print(f"✅ [Contact Added Success]")
        return f"Successfully saved contact: {name_clean} with email {email_clean}."
    else:
        print(f"❌ [Contact Add Failed]")
        return "Failed to save contact due to write error."

@mcp.tool()
def write_to_active_email(content: str) -> str:
    """Write text directly into the body section of the currently active Gmail compose window in Google Chrome without opening a new tab."""
    print(f"\n✍️ [Loopi writing to active mail body]: \"{content}\"")
    import subprocess
    
    # 1. Set the clipboard to the content
    try:
        process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        process.communicate(input=content.encode('utf-8'))
    except Exception as e:
        return f"Error setting clipboard: {str(e)}"
        
    # 2. Run AppleScript to activate Chrome, focus the message body via JS, and paste
    applescript = f'''
    tell application "Google Chrome"
        activate
        delay 0.5
        tell active tab of window 1
            try
                -- Try focusing the Gmail compose body using JS
                execute javascript "
                    (function() {{
                        var el = document.querySelector('div[aria-label=\\\"Message Body\\\"]') || document.querySelector('div[role=\\\"textbox\\\"]');
                        if (el) {{
                            el.focus();
                            return true;
                        }}
                        return false;
                    }})()
                "
            on error
                -- Fallback if JS Apple Events are disabled
            end try
        end tell
    end tell
    tell application "System Events"
        -- Press CMD+V to paste the clipboard contents
        keystroke "v" using {{command down}}
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", applescript], check=True)
        print(f"✅ [Write Success]: Content pasted directly into active compose tab")
        return "Successfully wrote content directly into the active mail body."
    except Exception as e:
        print(f"❌ [Write Failed]: {str(e)}")
        return f"Error writing to active email: {str(e)}"

def main():
    print("Starting Loopi MCP Server...")
    mcp.run()

if __name__ == "__main__":
    main()
