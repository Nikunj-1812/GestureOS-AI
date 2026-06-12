"""
GestureOS AI — Word Predictor
=============================
Prefix-based word completion, case matching, and text segment analysis for virtual keyboard autocomplete.
"""

COMMON_WORDS = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
    "people", "into", "year", "your", "good", "some", "could", "them", "see",
    "other", "than", "then", "now", "look", "only", "come", "its", "over", "think",
    "also", "back", "after", "use", "two", "how", "our", "work", "first", "well",
    "way", "even", "new", "want", "because", "any", "these", "give", "day", "most",
    "us", "hello", "gesture", "keyboard", "mouse", "screen", "system", "camera",
    "hand", "detect", "pinch", "drag", "scroll", "volume", "brightness", "active",
    "control", "track", "model", "weight", "predict", "suggest", "autocomplete", "word",
    "speed", "accuracy", "recent", "emoji", "panel", "telemetry", "dashboard", "visual",
    "stream", "feed", "frame", "fps", "threshold", "sensitivity", "device", "setup",
    "configure", "settings", "theme", "dark", "light", "clear", "buffer", "sound", "click"
]

def get_current_word(text: str) -> str:
    """Extracts the word currently being typed from the end of the text buffer."""
    if not text:
        return ""
    
    # If the text ends with a whitespace, we are not currently typing a word
    if text[-1].isspace():
        return ""
        
    # Split by whitespace and grab the last chunk
    words = text.split()
    if not words:
        return ""
        
    # Remove trailing punctuation from the prefix check if any
    last_chunk = words[-1]
    cleaned = "".join(c for c in last_chunk if c.isalnum() or c in ("'", "-"))
    return cleaned

def get_suggestions(prefix: str) -> list[str]:
    """Returns the top 3 matching word completions matching the prefix, preserving casing style."""
    if not prefix:
        return []
        
    prefix_lower = prefix.lower()
    matches = []
    
    for word in COMMON_WORDS:
        if word.startswith(prefix_lower) and word != prefix_lower:
            matches.append(word)
            
    # Sort matches by length (shorter words first) then alphabetically
    matches.sort(key=lambda w: (len(w), w))
    
    # Casing preservation
    is_upper = prefix.isupper() if len(prefix) > 1 else False
    is_title = prefix[0].isupper() if prefix else False
    
    formatted = []
    for word in matches:
        if is_upper:
            formatted.append(word.upper())
        elif is_title:
            formatted.append(word.title())
        else:
            formatted.append(word)
            
    return formatted[:3]
