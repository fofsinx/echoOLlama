import logging
import sys
from datetime import datetime

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors and emojis"""
    
    COLORS = {
        'DEBUG': '\033[94m',    # Blue
        'INFO': '\033[92m',     # Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'CRITICAL': '\033[95m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': '✨',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '💥'
    }

    def format(self, record):
        if not record.exc_info:
            level = record.levelname
            msg = record.getMessage()
            
            # Add timestamp
            timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
            
            # Add file and line info
            file_info = f"{record.filename}:{record.lineno}"
            
            # Format with color and emoji
            color = self.COLORS.get(level, '')
            emoji = self.EMOJIS.get(level, '')
            reset = self.COLORS['RESET']
            
            return f"{color}{timestamp} {emoji} [{level}] {file_info} - {msg}{reset}"
        return super().format(record)

def setup_logger():
    """Setup application logger"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter())
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler('app.log')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s'
    ))
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()
