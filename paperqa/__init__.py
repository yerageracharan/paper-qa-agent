"""paperqa - ask questions about a research paper and get cited answers (or an honest 'not found')."""
from .agent import Answer, Citation, PaperQAAgent
from .config import Config

__all__ = ["PaperQAAgent", "Answer", "Citation", "Config"]
__version__ = "0.1.0"
