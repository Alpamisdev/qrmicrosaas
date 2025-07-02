import markdown
import bleach
from markdown.extensions import fenced_code
from markdown.extensions import codehilite
from markdown.extensions import tables
from markdown.extensions import toc

# List of allowed HTML tags
ALLOWED_TAGS = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code', 'div', 'em',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'li', 'ol', 'p',
    'pre', 'span', 'strong', 'table', 'tbody', 'td', 'th', 'thead', 'tr', 'ul'
]

# List of allowed HTML attributes
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'rel'],
    'abbr': ['title'],
    'acronym': ['title'],
    'img': ['src', 'alt', 'title'],
    'div': ['class'],
    'p': ['class'],
    'span': ['class'],
    'pre': ['class'],
    'code': ['class']
}

def convert_markdown_to_html(markdown_text: str) -> str:
    """
    Convert markdown text to HTML with security measures.
    
    Args:
        markdown_text: Raw markdown text
        
    Returns:
        Sanitized HTML string
    """
    # Configure Markdown extensions
    extensions = [
        'fenced_code',
        'codehilite',
        'tables',
        'toc'
    ]
    
    extension_configs = {
        'codehilite': {
            'css_class': 'highlight',
            'linenums': False
        }
    }
    
    # Convert markdown to HTML
    html = markdown.markdown(
        markdown_text,
        extensions=extensions,
        extension_configs=extension_configs
    )
    
    # Sanitize HTML
    clean_html = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
    
    return clean_html 