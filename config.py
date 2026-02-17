"""
MekanAI Configuration Manager
Handles loading, saving, and managing configuration from config.yaml
"""

import yaml
import os
from pathlib import Path
from typing import Any, Dict
import secrets


class Config:
    """Configuration manager for MekanAI application"""

    def __init__(self, config_path: str = "configs/config.yaml"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            print(f"[!] Config file not found: {self.config_path}")
            print("Creating default configuration...")
            self.create_default_config()
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
            print(f"[+] Configuration loaded from {self.config_path}")
        except Exception as e:
            print(f"[-] Error loading config: {e}")
            self.config = {}

    def save(self) -> bool:
        """Save configuration to YAML file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False,
                         allow_unicode=True, sort_keys=False)
            print(f"[+] Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            print(f"[-] Error saving config: {e}")
            return False

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        Example: config.get('system.name') or config.get('online_api.openai.api_key')
        """
        keys = key_path.split('.')
        value = self.config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value using dot notation
        Example: config.set('system.theme', 'light')
        """
        keys = key_path.split('.')
        target = self.config

        # Navigate to the parent dictionary
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]

        # Set the value
        target[keys[-1]] = value

    def update_section(self, section: str, values: Dict[str, Any]) -> None:
        """Update entire configuration section"""
        if section in self.config:
            self.config[section].update(values)
        else:
            self.config[section] = values

    def create_default_config(self) -> None:
        """Create default configuration file"""
        self.config = {
            'system': {
                'name': 'MekanAI',
                'version': '1.0.0',
                'language': 'tr',
                'theme': 'dark',
                'debug_mode': False,
                'log_level': 'info'
            },
            'server': {
                'host': '0.0.0.0',
                'port': 5000,
                'secret_key': secrets.token_hex(32),
                'max_upload_size': 16777216
            },
            'database': {
                'type': 'sqlite',
                'path': 'data/db/mekanai.db'
            },
            'paths': {
                'projects': 'data/projects',
                'uploads': 'data/uploads',
                'outputs': 'data/outputs',
                'temp': 'data/temp',
                'db': 'data/db'
            }
        }
        self.save()

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        paths = self.get('paths', {})
        for path_name, path_value in paths.items():
            Path(path_value).mkdir(parents=True, exist_ok=True)
            print(f"[+] Directory ensured: {path_value}")

    def validate(self) -> bool:
        """Validate configuration"""
        required_sections = ['system', 'server', 'paths']

        for section in required_sections:
            if section not in self.config:
                print(f"[-] Missing required section: {section}")
                return False

        # Validate server settings
        port = self.get('server.port')
        if not isinstance(port, int) or port < 1 or port > 65535:
            print(f"[-] Invalid server port: {port}")
            return False

        print("[+] Configuration validation passed")
        return True

    def print_config(self) -> None:
        """Print current configuration (hide sensitive data)"""
        print("\n" + "="*50)
        print("Current Configuration:")
        print("="*50)

        safe_config = self.config.copy()

        if 'server' in safe_config and 'secret_key' in safe_config['server']:
            safe_config['server']['secret_key'] = '***HIDDEN***'

        print(yaml.dump(safe_config, default_flow_style=False, allow_unicode=True))
        print("="*50 + "\n")


# Global configuration instance
config = Config()


# CLI for testing and management
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "show":
            config.print_config()

        elif command == "validate":
            if config.validate():
                print("[+] Configuration is valid")
            else:
                print("[-] Configuration has errors")

        elif command == "reset":
            print("[!]  Resetting configuration to defaults...")
            config.create_default_config()
            print("[+] Configuration reset complete")

        elif command == "dirs":
            print("Creating directories...")
            config.ensure_directories()

        elif command == "get" and len(sys.argv) > 2:
            key = sys.argv[2]
            value = config.get(key)
            print(f"{key} = {value}")

        elif command == "set" and len(sys.argv) > 3:
            key = sys.argv[2]
            value = sys.argv[3]
            # Try to convert to appropriate type
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.isdigit():
                value = int(value)

            config.set(key, value)
            config.save()
            print(f"[+] Set {key} = {value}")

        else:
            print("Unknown command")

    else:
        print("""
MekanAI Configuration Manager

Usage:
    python config.py show              - Show current configuration
    python config.py validate          - Validate configuration
    python config.py reset             - Reset to default configuration
    python config.py dirs              - Create necessary directories
    python config.py get <key>         - Get configuration value
    python config.py set <key> <value> - Set configuration value

Examples:
    python config.py get system.theme
    python config.py set system.theme light
        """)
