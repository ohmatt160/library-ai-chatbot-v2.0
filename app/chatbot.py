# OPAC client - will be initialized lazily
opac_client = None

def get_opac_client():
    """Get or create OPAC client with configuration from app config"""
    global opac_client
    if opac_client is None:
        from app.api.opac_client import create_opac_client
        try:
            from flask import current_app
            opac_config = {
                'opac_type': current_app.config.get('OPAC_TYPE', 'openlibrary'),
                'base_url': current_app.config.get('OPAC_URL', ''),
                'api_key': current_app.config.get('OPAC_API_KEY', ''),
                'username': current_app.config.get('OPAC_USERNAME', ''),
                'password': current_app.config.get('OPAC_PASSWORD', ''),
                'timeout': current_app.config.get('OPAC_TIMEOUT', 30),
                'use_mock': current_app.config.get('OPAC_USE_MOCK', False)
            }
        except RuntimeError:
            import os
            opac_config = {
                'opac_type': os.getenv('OPAC_TYPE', 'openlibrary'),
                'base_url': os.getenv('OPAC_URL', ''),
                'api_key': os.getenv('OPAC_API_KEY', ''),
                'username': os.getenv('OPAC_USERNAME', ''),
                'password': os.getenv('OPAC_PASSWORD', ''),
                'timeout': int(os.getenv('OPAC_TIMEOUT', '30')),
                'use_mock': os.getenv('OPAC_USE_MOCK', 'false').lower() == 'true'
            }
        opac_client = create_opac_client(opac_config)
    return opac_client


def reset_opac_client():
    """Reset and reinitialize the OPAC client - useful when config changes"""
    global opac_client
    opac_client = None
    return get_opac_client()


# For backward compatibility
def get_opac():
    return get_opac_client()


# Lazy component getters
_rule_engine = None
_nlp_engine = None
_response_generator = None
_metrics_tracker = None
_dialogue_manager = None

def get_rule_engine():
    global _rule_engine
    if _rule_engine is None:
        from app.models.rule_engine import AdvancedRuleEngine
        _rule_engine = AdvancedRuleEngine('app/data/rules.json')
    return _rule_engine

def get_nlp_engine():
    global _nlp_engine
    if _nlp_engine is None:
        from app.models.nlp_engine import HybridNLPEngine
        try:
            _nlp_engine = HybridNLPEngine()
        except Exception as e:
            print(f"[ERROR] Failed to initialize NLP engine: {e}")
            raise
    return _nlp_engine

def get_response_generator():
    global _response_generator
    if _response_generator is None:
        from app.models.response_generator import ResponseGenerator
        _response_generator = ResponseGenerator('app/data/response_templates.json')
    return _response_generator

def get_metrics_tracker():
    global _metrics_tracker
    if _metrics_tracker is None:
        from app.utils.metrics import MetricsTracker
        _metrics_tracker = MetricsTracker()
    return _metrics_tracker

def get_dialogue_manager():
    global _dialogue_manager
    if _dialogue_manager is None:
        from app.models.dialogue_manager import DialogueManager
        try:
            _dialogue_manager = DialogueManager(get_rule_engine(), get_nlp_engine(), get_response_generator())
        except Exception as e:
            print(f"[ERROR] Failed to initialize dialogue manager: {e}")
            import traceback
            traceback.print_exc()
            raise
    return _dialogue_manager
