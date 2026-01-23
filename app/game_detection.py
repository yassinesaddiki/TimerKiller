"""
Game Detection & Blocking Notifications Module

Detects games and provides user-friendly blocking notifications.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Common game process names (can be expanded)
GAME_KEYWORDS = [
    "steam", "epic", "origin", "battle.net", "launcher",
    "game", "wow", "ow2", "dota2", "csgo", "valorant",
    "minecraft", "roblox", "discord", "twitch",
    "overwatch", "league", "apex", "fortnite"
]

# Common game paths
GAME_PATHS = [
    r"C:\Program Files\Steam",
    r"C:\Program Files (x86)\Steam",
    r"C:\Program Files\Epic Games",
    r"C:\Program Files\Battle.net",
    r"C:\Program Files (x86)\Blizzard Entertainment"
]


def is_game_process(process_name):
    """
    Detect if a process is likely a game.
    
    Args:
        process_name (str): Process name (e.g., 'steam.exe')
        
    Returns:
        bool: True if likely a game
    """
    lower_name = process_name.lower()
    
    for keyword in GAME_KEYWORDS:
        if keyword in lower_name:
            return True
    
    return False


def categorize_processes(processes):
    """
    Categorize a list of processes into Games, Chat, and Other.
    
    Args:
        processes (list): List of process names
        
    Returns:
        dict: Categorized processes {"Games": [...], "Chat": [...], "Other": [...]}
    """
    categories = {
        "Games": [],
        "Chat": [],
        "Other": []
    }
    
    chat_keywords = ["discord", "slack", "telegram", "whatsapp", "skype", "zoom"]
    
    for proc in processes:
        lower_name = proc.lower()
        
        # Check chat
        if any(chat in lower_name for chat in chat_keywords):
            categories["Chat"].append(proc)
        # Check games
        elif is_game_process(proc):
            categories["Games"].append(proc)
        else:
            categories["Other"].append(proc)
    
    return categories


def get_common_games():
    """
    Get list of common game executables that might be installed.
    
    Returns:
        list: Common game process names
    """
    return [
        "steam.exe",
        "epicgameslauncher.exe",
        "battle.net.exe",
        "launcher.exe",
        "ow2.exe",
        "wow.exe",
        "diablo3.exe",
        "diabloimmortal.exe",
        "minecraft.exe",
        "javaw.exe",  # Minecraft Java
        "robloxplayerlauncher.exe",
        "csgo.exe",
        "hl2.exe",
        "dota2.exe",
        "valorant.exe",
        "valorantclient.exe",
        "apexlegends.exe",
        "fortnite.exe",
        "leagueoflegends.exe",
        "bluestacks.exe",
        "noxplayer.exe"
    ]
