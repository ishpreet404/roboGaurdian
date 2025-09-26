# Quick fix for MediaPipe initialization section
import re

# Read the file
with open('windows_ai_controller.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken else block
pattern = r'                else:\s*\n\s*\n\s*if sys\.version_info >= \(3, 13\):\s*\n\s*self\.log\("� Try: Python 3\.11 or 3\.12 for full AI features"\)\s*else:\s*\n\s*'
replacement = '                else:\n                    pass  # Using OpenCV fallbacks\n                '

content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

# Write back
with open('windows_ai_controller.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed MediaPipe initialization section")