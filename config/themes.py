"""Theme definitions for UI."""

from typing import Dict, Any

# Theme color definitions
THEMES: Dict[str, Dict[str, Any]] = {
    "Modern Dark": {
        "bg_primary": "#0A0A0F",
        "bg_secondary": "#16161F",
        "bg_tertiary": "#1F1F2E",
        "fg_primary": "#67E8F9",
        "fg_secondary": "#A5F3FC",
        "accent": "#22D3EE",
        "file_colors": {
            '.pdf': '#3B82F6', '.docx': '#3B82F6', '.doc': '#3B82F6', '.txt': '#60A5FA',
            '.xlsx': '#10B981', '.xls': '#10B981', '.csv': '#10B981', '.md': '#F97316',
            '.png': '#EC4899', '.jpg': '#EC4899', '.jpeg': '#EC4899', '.mp3': '#F59E0B',
            '.mp4': '#8B5CF6', '.mkv': '#8B5CF6', '.py': '#10B981', '.js': '#F59E0B',
            '.html': '#EF4444', '.css': '#3B82F6', '.zip': '#FBBF24', '.exe': '#EF4444',
            '.sys': '#6B7280', '.dll': '#6B7280', '.log': '#ECA5A5', '.db': '#DC2626',
            "folder": "#F59E0B", "folder_system": "#7F1D1D", "default": "#F472B6"
        }
    },
    "Deep Indigo": {
        "bg_primary": "#0F0F23",
        "bg_secondary": "#1A1A3E",
        "bg_tertiary": "#2D2D5F",
        "fg_primary": "#A8D8FF",
        "fg_secondary": "#C7E9FF",
        "accent": "#7C3AED",
        "file_colors": {
            '.pdf': '#4F46E5', '.docx': '#4F46E5', '.doc': '#4F46E5', '.txt': '#818CF8',
            '.xlsx': '#06B6D4', '.xls': '#06B6D4', '.csv': '#06B6D4', '.md': '#FB923C',
            '.png': '#EC4899', '.jpg': '#EC4899', '.jpeg': '#EC4899', '.mp3': '#FBBF24',
            '.mp4': '#A78BFA', '.mkv': '#A78BFA', '.py': '#10B981', '.js': '#F97316',
            '.html': '#F87171', '.css': '#4F46E5', '.zip': '#FCD34D', '.exe': '#EF4444',
            '.sys': '#4B5563', '.dll': '#6B7280', '.log': '#FECACA', '.db': '#DC2626',
            "folder": "#A78BFA", "folder_system": "#4C0519", "default": "#C084FC"
        }
    },
    "Cyber Neon": {
        "bg_primary": "#000000",
        "bg_secondary": "#0D1117",
        "bg_tertiary": "#161B22",
        "fg_primary": "#00FF88",
        "fg_secondary": "#00FFCC",
        "accent": "#00FF00",
        "file_colors": {
            '.pdf': '#00FF00', '.docx': '#00FF00', '.doc': '#00FF00', '.txt': '#00FFCC',
            '.xlsx': '#FF00FF', '.xls': '#FF00FF', '.csv': '#FF00FF', '.md': '#FFFF00',
            '.png': '#FF0080', '.jpg': '#FF0080', '.jpeg': '#FF0080', '.mp3': '#00FFFF',
            '.mp4': '#00FF88', '.mkv': '#00FF88', '.py': '#00FF00', '.js': '#FFFF00',
            '.html': '#FF0000', '.css': '#00FF00', '.zip': '#FFFF00', '.exe': '#FF0000',
            '.sys': '#00FFCC', '.dll': '#00FFCC', '.log': '#FF00FF', '.db': '#FF0000',
            "folder": "#00FF88", "folder_system": "#660000", "default": "#FF00FF"
        }
    },
    "Soft Warm": {
        "bg_primary": "#FBF8F3",
        "bg_secondary": "#F5F1E8",
        "bg_tertiary": "#EFE9E0",
        "fg_primary": "#5A4A42",
        "fg_secondary": "#7B6B63",
        "accent": "#D4876C",
        "file_colors": {
            '.pdf': '#8B6F47', '.docx': '#8B6F47', '.doc': '#8B6F47', '.txt': '#A0826D',
            '.xlsx': '#7FB069', '.xls': '#7FB069', '.csv': '#7FB069', '.md': '#D4876C',
            '.png': '#D4876C', '.jpg': '#D4876C', '.jpeg': '#D4876C', '.mp3': '#C89D5A',
            '.mp4': '#B8956A', '.mkv': '#B8956A', '.py': '#7FB069', '.js': '#D4876C',
            '.html': '#C85A54', '.css': '#8B6F47', '.zip': '#D4A574', '.exe': '#C85A54',
            '.sys': '#9B9B9B', '.dll': '#A0A0A0', '.log': '#E6B5A8', '.db': '#A94432',
            "folder": "#C89D5A", "folder_system": "#5A3A2A", "default": "#D4A574"
        }
    },
    "Ocean Blue": {
        "bg_primary": "#0D1B2A",
        "bg_secondary": "#1B3A52",
        "bg_tertiary": "#265C84",
        "fg_primary": "#90E0EF",
        "fg_secondary": "#CAF0F8",
        "accent": "#00B4D8",
        "file_colors": {
            '.pdf': '#0077B6', '.docx': '#0077B6', '.doc': '#0077B6', '.txt': '#0096C7',
            '.xlsx': '#00D9FF', '.xls': '#00D9FF', '.csv': '#00D9FF', '.md': '#03045E',
            '.png': '#FF006E', '.jpg': '#FF006E', '.jpeg': '#FF006E', '.mp3': '#FB5607',
            '.mp4': '#00B4D8', '.mkv': '#00B4D8', '.py': '#00D9FF', '.js': '#FB5607',
            '.html': '#FF006E', '.css': '#0077B6', '.zip': '#FFB703', '.exe': '#D62828',
            '.sys': '#4A90E2', '.dll': '#4A90E2', '.log': '#90E0EF', '.db': '#D62828',
            "folder": "#00B4D8", "folder_system": "#03045E", "default": "#90E0EF"
        }
    },
    "White": {
        "bg_primary": "#FFFFFF",
        "bg_secondary": "#F9F9F9",
        "bg_tertiary": "#F0F0F0",
        "fg_primary": "#1F2937",
        "fg_secondary": "#4B5563",
        "accent": "#3B82F6",
        "file_colors": {
            '.pdf': '#1E40AF', '.docx': '#1E40AF', '.doc': '#1E40AF', '.txt': '#1E40AF',
            '.xlsx': '#059669', '.xls': '#059669', '.csv': '#059669', '.md': '#D97706',
            '.png': '#DC2626', '.jpg': '#DC2626', '.jpeg': '#DC2626', '.mp3': '#EA580C',
            '.mp4': '#7C3AED', '.mkv': '#7C3AED', '.py': '#059669', '.js': '#D97706',
            '.html': '#DC2626', '.css': '#1E40AF', '.zip': '#D97706', '.exe': '#DC2626',
            '.sys': '#6B7280', '.dll': '#6B7280', '.log': '#991B1B', '.db': '#991B1B',
            "folder": "#D97706", "folder_system": "#7F1D1D", "default": "#9CA3AF"
        }
    }
}


def get_theme(name: str) -> Dict[str, Any]:
    """Get theme by name.
    
    Args:
        name: Theme name
        
    Returns:
        Theme dictionary, or Modern Dark if not found
    """
    return THEMES.get(name, THEMES["Modern Dark"])


from typing import List

def get_all_themes() -> List[str]:
    """Get all available themes.
    
    Returns:
        List of theme names
    """
    return list(THEMES.keys())
