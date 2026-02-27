from app.models.dialogue_manager import DialogueManager
from app.models.rule_engine import AdvancedRuleEngine
from app.models.nlp_engine import HybridNLPEngine
from app.models.response_generator import ResponseGenerator
from app.utils.metrics import MetricsTracker
from app.api.opac_client import create_opac_client

# Initialize components lazily or as singletons
rule_engine = AdvancedRuleEngine('app/data/rules.json')
nlp_engine = HybridNLPEngine()
response_generator = ResponseGenerator('app/data/response_templates.json')
metrics_tracker = MetricsTracker()

# OPAC client - will be initialized lazily
opac_client = None

def get_opac_client():
    """Get or create OPAC client with configuration from app config"""
    global opac_client
    if opac_client is None:
        # Import current_app to get config
        try:
            from flask import current_app
            opac_config = {
                'opac_type': current_app.config.get('OPAC_TYPE', 'generic'),
                'base_url': current_app.config.get('OPAC_URL', ''),
                'api_key': current_app.config.get('OPAC_API_KEY', ''),
                'username': current_app.config.get('OPAC_USERNAME', ''),
                'password': current_app.config.get('OPAC_PASSWORD', ''),
                'timeout': current_app.config.get('OPAC_TIMEOUT', 30),
                'use_mock': current_app.config.get('OPAC_USE_MOCK', False)
            }
        except RuntimeError:
            # Fallback if not in app context
            import os
            opac_config = {
                'opac_type': os.getenv('OPAC_TYPE', 'generic'),
                'base_url': os.getenv('OPAC_URL', ''),
                'api_key': os.getenv('OPAC_API_KEY', ''),
                'username': os.getenv('OPAC_USERNAME', ''),
                'password': os.getenv('OPAC_PASSWORD', ''),
                'timeout': int(os.getenv('OPAC_TIMEOUT', '30')),
                'use_mock': os.getenv('OPAC_USE_MOCK', 'false').lower() == 'true'
            }
        opac_client = create_opac_client(opac_config)
    return opac_client

# For backward compatibility
def get_opac():
    return get_opac_client()

# Create dialogue manager
dialogue_manager = DialogueManager(rule_engine, nlp_engine, response_generator)
