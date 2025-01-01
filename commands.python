import requests
from bs4 import BeautifulSoup
import json
import logging
import re

# Configuration
CONFIG = {
    "BARITONE": {
        "url": "https://baritone.leijurv.com/commands",
        "file": "baritone_commands.json",
        "parser": "parse_baritone_commands"
    },
    "MINESCRIPT": {
        "url": "https://minescript.net/docs",
        "file": "minescript_commands.json",
        "parser": "parse_minescript_commands"
    },
    "OLLAMA": {
        "url": "https://ollama.ai/docs",
        "file": "ollama_commands.json",
        "parser": "parse_ollama_commands"
    }
}

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def fetch_page(url):
    """Fetch the content of a webpage."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch {url}: {e}")
        return None

def parse_baritone_commands(html):
    """Parse Baritone commands from HTML content."""
    soup = BeautifulSoup(html, "html.parser")
    commands = []
    code_blocks = soup.find_all("pre")
    for block in code_blocks:
        syntax = block.find("code").text.strip()
        # Extract command and arguments using regex
        match = re.match(r'^(#\w+)\s*(.*)$', syntax)
        if match:
            command = match.group(1)
            args = match.group(2).split() if match.group(2) else []
            # Find the next <p> tag for the description
            description_tag = block.find_next("p")
            description = description_tag.text.strip() if description_tag else ""
            commands.append({
                "command": command,
                "syntax": syntax,
                "description": description,
                "args": args
            })
    return commands

def parse_minescript_commands(html):
    """Parse Minescript commands from HTML content."""
    soup = BeautifulSoup(html, "html.parser")
    commands = []
    code_blocks = soup.find_all("pre")
    for block in code_blocks:
        syntax = block.find("code").text.strip()
        # Extract command and arguments using regex
        match = re.match(r'^(\w+)\s*(.*)$', syntax)
        if match:
            command = match.group(1)
            args = match.group(2).split() if match.group(2) else []
            # Find the next <p> tag for the description
            description_tag = block.find_next("p")
            description = description_tag.text.strip() if description_tag else ""
            commands.append({
                "command": command,
                "syntax": syntax,
                "description": description,
                "args": args
            })
    return commands

def parse_ollama_commands(html):
    """Parse Ollama commands from HTML content."""
    soup = BeautifulSoup(html, "html.parser")
    commands = []
    code_blocks = soup.find_all("pre")
    for block in code_blocks:
        syntax = block.find("code").text.strip()
        # Extract command and arguments using regex
        match = re.match(r'^(\w+)\s*(.*)$', syntax)
        if match:
            command = match.group(1)
            args = match.group(2).split() if match.group(2) else []
            # Find the next <p> tag for the description
            description_tag = block.find_next("p")
            description = description_tag.text.strip() if description_tag else ""
            commands.append({
                "command": command,
                "syntax": syntax,
                "description": description,
                "args": args
            })
    return commands

def save_commands(commands, filename):
    """Save commands to a JSON file."""
    try:
        with open(filename, "w") as f:
            json.dump(commands, f, indent=4)
        logging.info(f"Saved {len(commands)} commands to {filename}")
    except IOError as e:
        logging.error(f"Failed to save {filename}: {e}")

def fetch_and_save_commands(service):
    """Fetch and save commands for a specific service."""
    config = CONFIG[service]
    parser_func = globals()[config["parser"]]
    html = fetch_page(config["url"])
    if html:
        commands = parser_func(html)
        save_commands(commands, config["file"])
    else:
        logging.warning(f"No commands fetched for {service}")

def main():
    """Main function to fetch and save commands for all services."""
    for service in CONFIG:
        logging.info(f"Processing {service} commands...")
        fetch_and_save_commands(service)
    logging.info("Command fetching and organization complete.")

if __name__ == "__main__":
    main()
