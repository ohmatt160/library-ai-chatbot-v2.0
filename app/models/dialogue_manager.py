import datetime
import json
from enum import Enum
from typing import Dict, List, Optional
import redis  # For session management


class ConversationState(Enum):
    GREETING = "greeting"
    QUERY_PROCESSING = "query_processing"
    FOLLOW_UP = "follow_up"
    CLARIFICATION = "clarification_needed"
    COMPLETED = "completed"


class DialogueManager:
    def __init__(self, rule_engine, nlp_engine, response_generator):
        self.rule_engine = rule_engine
        self.nlp_engine = nlp_engine
        self.response_generator = response_generator
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            self.redis_client.ping()
        except Exception:
            print("Redis not available, using in-memory context storage")
            class MockRedis:
                def __init__(self): self.data = {}
                def get(self, key): return self.data.get(key)
                def setex(self, key, time, value): self.data[key] = value
                def set(self, key, value): self.data[key] = value
            self.redis_client = MockRedis()
        self.conversation_contexts = {}

    def process_message(self, user_id: str, session_id: str, message: str) -> Dict:
        """Process user message with context tracking"""

        print(f"\n=== DIALOGUE MANAGER PROCESSING ===")
        print(f"Message: '{message}'")

        print(f"self.response_generator exists: {hasattr(self, 'response_generator')}")
        print(f"self.response_generator type: {type(self.response_generator)}")

        # Get or create conversation context
        context_key = f"conv:{user_id}:{session_id}"
        context = self._get_context(context_key)

        # Check for borrow/reserve keywords BEFORE NLP processing
        # This handles cases like "borrow bimbo" where NLP might return unknown intent
        import re
        message_lower = message.lower().strip()
        borrow_patterns = [r'\bborrow\b', r'\bborrowing\b', r'\bloan\b', r'\bcheck\s*out\b']
        reserve_patterns = [r'\breserve\b', r'\breservation\b', r'\bhold\b']
        
        is_borrow = any(re.search(p, message_lower) for p in borrow_patterns)
        is_reserve = any(re.search(p, message_lower) for p in reserve_patterns)
        
        if is_borrow or is_reserve:
            print(f"DEBUG: Detected borrow={is_borrow}, reserve={is_reserve} from keywords")
            # Extract book name by removing borrow/reserve words
            book_query = message_lower
            for p in borrow_patterns + reserve_patterns:
                book_query = re.sub(p, '', book_query)
            book_query = book_query.strip()
            
            # If no book name, ask for it
            if not book_query:
                return {
                    'response': f"Sure! Which book would you like to {'borrow' if is_borrow else 'reserve'}? Please provide the book title.",
                    'intent': 'borrow_request' if is_borrow else 'book_reservation',
                    'confidence': 0.95,
                    'processing_method': 'keyword_fallback'
                }
            
            # Search for the book
            from app.api.opac_client import OpenLibraryClient
            from app.model import Book
            from app.extensions import db
            
            action_type = 'borrow' if is_borrow else 'reserve'
            
            # Search local database
            local_books = Book.query.filter(
                db.or_(
                    Book.title.ilike(f'%{book_query}%'),
                    Book.author.ilike(f'%{book_query}%'),
                    Book.isbn.ilike(f'%{book_query}%')
                )
            ).limit(10).all()
            
            local_results = []
            for book in local_books:
                local_results.append({
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'isbn': book.isbn or '',
                    'source': 'local',
                    'action_type': action_type
                })
            
            # Search OpenLibrary
            opac_results = []
            try:
                opac_client = OpenLibraryClient()
                opac_books = opac_client.search(query=book_query, limit=5)
                for book in opac_books:
                    opac_results.append({
                        'title': book.get('title', 'Unknown'),
                        'author': book.get('author', 'Unknown'),
                        'isbn': book.get('isbn', ''),
                        'source': 'openlibrary',
                        'action_type': action_type
                    })
            except Exception as e:
                print(f"Error searching OpenLibrary: {e}")
            
            all_books = local_results + opac_results
            
            if not all_books:
                return {
                    'response': f"I couldn't find any book matching '{book_query}'. Would you like to try a different search term?",
                    'intent': 'book_search',
                    'confidence': 0.9,
                    'processing_method': 'keyword_fallback'
                }
            
            # Store books in context for later selection
            context['last_books'] = all_books[:5]
            context['last_query'] = book_query
            context['action_type'] = action_type
            context['user_id'] = user_id  # Store user_id for later selection
            self._update_context(context_key, context)
            
            if len(all_books) == 1:
                # Single book - process immediately
                book = all_books[0]
                if book['source'] == 'local':
                    if is_borrow:
                        result = self._create_borrow_request(user_id, book)
                    else:
                        result = self._create_reservation(user_id, book)
                else:
                    result = self._create_reservation(user_id, {
                        'title': book['title'],
                        'author': book['author'],
                        'isbn': book.get('isbn', '')
                    })
                return {
                    'response': result.get('message', 'Request processed!'),
                    'intent': 'borrow_created' if is_borrow else 'reservation_created',
                    'confidence': 0.95,
                    'processing_method': 'keyword_fallback'
                }
            
            # Multiple books - ask for clarification
            book_list = []
            for i, b in enumerate(all_books[:5], 1):
                book_list.append(f"{i}. {b['title'][:40]} by {b['author'][:30]}")
            
            return {
                'response': f"I found multiple books matching '{book_query}'. Which one would you like to {action_type}?\n\n" + "\n".join(book_list) + "\n\nPlease reply with the number (e.g., '1').",
                'intent': 'book_search',
                'confidence': 0.9,
                'processing_method': 'clarification',
                'db_results': all_books[:5]
            }


        # Step 1: Intent and Entity Extraction
        nlp_result = self.nlp_engine.process(message)

        if 'entities' not in nlp_result:
            nlp_result['entities'] = []

        # Add context-based entities
        if context.get('user_name'):
            nlp_result['entities'].append({'label': 'user_name', 'text': context['user_name']})

        intent = nlp_result.get('intent', 'unknown')
        confidence = nlp_result.get('confidence', 0.5)
        print(f"NLP Result keys: {nlp_result.keys()}")

        print(f"DEBUG: confidence type: {type(confidence)}, value: {confidence}")

        print(f"Intent: {intent}, Confidence: {confidence}")

        # Convert to float if needed
        if isinstance(confidence, (int, float)):
            conf_value = float(confidence)
        else:
            print(f"WARNING: confidence is not numeric: {confidence}")
            conf_value = 0.5  # Default

        # Now compare
        # Identity intents should always be answered, even with lower confidence
        identity_intents = ['introduction', 'about_you', 'bot_identity', 'bot_purpose', 'greeting', 'farewell']
        
        if conf_value < 0.5 and intent not in identity_intents:
            print(f"DEBUG: Low confidence detected: {conf_value}")
            # Get context to check for confirmation responses
            context_key = f"conv:{user_id}:{session_id}"
            context = self._get_context(context_key)
            
            # Handle low confidence with ALL required arguments
            return self._handle_low_confidence(
                user_message=message,
                confidence=conf_value,
                context=context,
                user_id=user_id
            )

        processing_method = nlp_result.get('processing_method', 'hybrid')


        # Step 2: Database Integration (Factual Querying)
        from app.utils.database import search_catalog, get_contact_info, get_user_account

        db_results = None
        opac_results = []
        corrected_query = None
        
        if intent == 'book_search':
            # First try local database
            db_results = search_catalog(query=message)
            
            # If no results, try fuzzy matching and OPAC
            if not db_results:
                # Check for common typos and get corrected query
                corrected_query = self._check_typo_and_suggest(message)
                
                if corrected_query and corrected_query != message.lower().strip():
                    # Try with corrected query
                    db_results = search_catalog(query=corrected_query)
                
                # If still no results, search OPAC (OpenLibrary)
                if not db_results:
                    # Extract clean search term (remove 'find', 'search', etc. prefixes)
                    import re
                    original_query = corrected_query if corrected_query else message.lower().strip()
                    search_term = re.sub(r'^(find|search|look for|get|show|\?)\s+', '', original_query)
                    search_term = search_term.strip()
                    
                    print(f"DEBUG: Searching OPAC with term: '{search_term}'")
                    try:
                        from app.api.opac_client import OpenLibraryClient
                        opac_client = OpenLibraryClient()
                        opac_results = opac_client.search(query=search_term, limit=10)
                        if opac_results:
                            print(f"DEBUG: Found {len(opac_results)} results from OpenLibrary")
                    except Exception as e:
                        print(f"DEBUG: OPAC search failed: {e}")
            
            # Combine results
            if opac_results:
                db_results = db_results + opac_results if db_results else opac_results
            
            nlp_result['db_results'] = db_results
            nlp_result['opac_results'] = opac_results
            nlp_result['corrected_query'] = corrected_query
        elif intent == 'contact_info':
            db_results = get_contact_info()
            nlp_result['db_results'] = db_results
        elif intent == 'book_availability':
            db_results = search_catalog(query=message) # Simplified
            nlp_result['db_results'] = db_results

        # Step 3: Determine processing path (Hybrid Decision)
        rule_response = self.rule_engine.match(message, intent)

        if rule_response and rule_response['confidence'] > 0.9:
            processing_method = "rule_based"
            response_data = rule_response
        elif nlp_result['confidence'] > 0.6:
            processing_method = "nlp_based"
            response_data = nlp_result
        # Identity intents should use NLP response even with lower confidence
        elif intent in identity_intents:
            print(f"DEBUG: Using NLP response for identity intent with confidence {nlp_result['confidence']}")
            processing_method = "nlp_based"
            response_data = nlp_result
        else:
            # RAG Fallback would go here
            # processing_method = "clarification"
            # response_data = self._handle_low_confidence(message, confidence, context)
            # Step 4: RAG (Retrieval-Augmented Generation) Fallback
            print("🔍 Attempting RAG fallback...")
            kb_match = self.nlp_engine.find_kb_match(message)
            if kb_match['match_found']:
                print(f"✅ RAG Match found: {kb_match['category']} (conf: {kb_match['confidence']})")
                processing_method = "knowledge_base"
                response_data = kb_match
            else:
                print("❌ No RAG match found, using clarification")
                processing_method = "clarification"
                response_data = self._handle_low_confidence(message, confidence, context, user_id)

        # Step 4: Determine state
        current_state = self._determine_state(user_id, session_id, intent, confidence, context)

        # Step 5: Update conversation context
        self._update_context(context_key, {
            'last_intent': nlp_result['intent'],
            'last_entities': nlp_result['entities'],
            'conversation_history': context.get('history', []) + [message],
            'state': current_state
        })

        # Step 6: Generate final response
        final_response = self.response_generator.generate(
            response_data,
            context,
            processing_method
        )

        # Step 7: Log interaction
        self._log_interaction(
            user_id=user_id, session_id=session_id, message=message, response=final_response,
            processing_method=processing_method, intent=intent, confidence=confidence, context=context
        )

        # Get follow-ups
        print("Getting follow-ups...")
        follow_ups = self._suggest_follow_ups(intent, confidence, current_state, context)
        print(f"Follow-ups: {follow_ups}")

        return {
            'response': final_response,
            'confidence': response_data.get('confidence', confidence),
            'processing_method': processing_method,
            'suggested_follow_ups': follow_ups,
            'context_id': context_key
        }

    def _get_context(self, context_key: str) -> Dict:
        """Retrieve conversation context from Redis"""
        context_data = self.redis_client.get(context_key)
        return json.loads(context_data) if context_data else {
            'history': [],
            'state': ConversationState.GREETING.value,
            'entities': {},
            'user_preferences': {}
        }

    def _get_state_enum(self, context: Dict) -> ConversationState:
        """Get ConversationState enum from context, defaulting to GREETING"""
        state_value = context.get('state', 'greeting')
        try:
            return ConversationState(state_value)
        except ValueError:
            return ConversationState.GREETING

    def _update_context(self, context_key: str, updates: Dict):
        """Update conversation context"""
        current = self._get_context(context_key)
        current.update(updates)
        
        # Convert any Enum values to their string representations for JSON serialization
        def convert_enums(obj):
            if isinstance(obj, dict):
                return {k: convert_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enums(item) for item in obj]
            elif isinstance(obj, Enum):
                return obj.value
            return obj
        
        serializable_current = convert_enums(current)
        self.redis_client.setex(
            context_key,
            3600,  # 1 hour expiry
            json.dumps(serializable_current)
        )

    def _handle_low_confidence(self, user_message: str, confidence, context: Dict = None, user_id: str = None) -> Dict:
        """
        Handle cases where intent confidence is low
        """
        if context is None: context = {}

        # Check for book selection (numeric input like "1", "2", etc.)
        user_lower = user_message.lower().strip()
        
        # Check if this is a number selection for a book
        if user_lower.isdigit():
            selection_num = int(user_lower)
            last_books = context.get('last_books', [])
            action_type = context.get('action_type', 'borrow')
            last_query = context.get('last_query', '')
            
            if last_books and 1 <= selection_num <= len(last_books):
                # Valid book selection
                book = last_books[selection_num - 1]
                from app.model import Book, User
                from app.extensions import db
                
                # Use user_id from parameter
                effective_user_id = user_id if user_id else context.get('user_id')
                
                if not effective_user_id:
                    return {
                        'response': 'Please log in to borrow or reserve books.',
                        'action': 'login_required',
                        'confidence': 0.95,
                        'processing_method': 'auth_required',
                        'requires_clarification': False
                    }
                
                # Process the borrow/reserve request
                if book.get('source') == 'local':
                    # Book exists in local database
                    if action_type == 'borrow':
                        result = self._create_borrow_request(effective_user_id, book)
                    else:
                        result = self._create_reservation(effective_user_id, book)
                else:
                    # Book from OpenLibrary - create reservation
                    result = self._create_reservation(effective_user_id, {
                        'title': book.get('title', 'Unknown'),
                        'author': book.get('author', 'Unknown'),
                        'isbn': book.get('isbn', '')
                    })
                
                return {
                    'response': result.get('message', f'Your {action_type} request for "{book["title"]}" has been submitted!'),
                    'action': 'book_selected',
                    'confidence': 0.95,
                    'processing_method': 'book_selection',
                    'requires_clarification': False,
                    'book_title': book.get('title', ''),
                    'action_type': action_type
                }
            elif last_books:
                # Invalid selection number
                return {
                    'response': f"Please enter a number between 1 and {len(last_books)}. Which book would you like to {action_type}?",
                    'action': 'invalid_selection',
                    'confidence': 0.9,
                    'processing_method': 'book_selection_error',
                    'requires_clarification': True
                }

        # Check for confirmation responses (yes/yeah/sure) to continue previous context
        confirmation_words = ['yes', 'yeah', 'sure', 'yep', 'ok', 'okay', 'please']
        
        if user_lower in confirmation_words:
            # Get previous intent from context
            last_intent = context.get('last_intent')
            
            # If previous intent was research_assistance, continue with detailed help
            if last_intent == 'research_assistance':
                return {
                    'response': "I'd be happy to help with your research!\n\nTo assist you better, could you tell me:\n1. What is your research topic or subject area?\n2. What type of resources are you looking for (books, journal articles, etc.)?\n3. Do you need help with citations?",
                    'action': 'continue',
                    'confidence': 0.9,
                    'processing_method': 'context_continuation',
                    'requires_clarification': False,
                    'follow_ups': ['My topic is...', 'I need journal articles', 'Help with APA citations'],
                    'original_message': user_message
                }

        # Ensure confidence is a float
        try:
            conf_value = float(confidence)
            # if isinstance(confidence, dict):
            #     # If confidence is a dict, try to extract a numeric value
            #     conf_value = confidence.get('score', confidence.get('confidence', 0.0))
            # else:
            #     conf_value = float(confidence)
        except (ValueError, TypeError):
            conf_value = 0.0  # Default to low confidence

        # Different strategies based on confidence level
        if conf_value < 0.3:
            # Very low confidence - ask for clarification
            responses = [
                "I'm not quite sure what you mean. Could you rephrase that?",
                "I want to make sure I understand correctly. Could you say that differently?",
                "I'm having trouble understanding. Could you provide more details?"
            ]
            import random
            response = random.choice(responses)
            action = 'clarify'
            processing_method = 'low_confidence_clarification'  # ADD THIS

        elif conf_value < 0.5:
            # Medium-low confidence - offer suggestions
            responses = [
                "I think you might be asking about: (1) Library hours, (2) Finding books, or (3) Borrowing policies. Which one interests you?",
                "Could this be about: Library hours, Book search, or Borrowing information?",
                "I can help with library hours, book searches, or borrowing questions. Which would you like?"
            ]
            import random
            response = random.choice(responses)
            action = 'suggest'
            processing_method = 'medium_confidence_suggestion'  # ADD THIS

        else:
            # Confidence is okay, but we still want to verify
            responses = [
                f"Just to make sure I understood: are you asking about '{user_message}'?",
                f"I think you're asking about: {user_message}. Is that correct?",
                f"Let me confirm: you want to know about '{user_message}', right?"
            ]
            import random
            response = random.choice(responses)
            action = 'confirm'
            processing_method = 'high_confidence_confirmation'  # ADD THIS

        # Generate follow-up questions
        follow_ups = self._get_clarification_questions(user_message, conf_value)

        return {
            'response': response,
            'action': action,
            'confidence': conf_value,
            'processing_method': processing_method,  # ADD THIS LINE
            'requires_clarification': True,
            'suggested_follow_ups': follow_ups,
            'original_message': user_message
        }

    def _check_typo_and_suggest(self, message: str) -> Optional[str]:
        """
        Check for common typos and suggest corrections
        Returns corrected query or None if no correction needed
        """
        import re
        
        # Common programming language/library typos
        common_typos = {
            'pyton': 'python',
            'phyton': 'python',
            'pythn': 'python',
            'pythno': 'python',
            'javscript': 'javascript',
            'javscript': 'javascript',
            'javasript': 'javascript',
            'rubby': 'ruby',
            'rubi': 'ruby',
            'c++': 'c plus plus',
            'c#': 'c sharp',
            'fsharp': 'f sharp',
            'goLang': 'golang',
            'bable': 'bible',
            'bibble': 'bible',
            'bible': 'bible',
            'html': 'HTML',
            'css': 'CSS',
            'sql': 'SQL',
            'api': 'API',
        }
        
        # Clean and normalize the message
        message_lower = message.lower().strip()
        # Remove 'find ' prefix if present
        query = re.sub(r'^(find|search|look for|get|show)\s+', '', message_lower)
        query = query.strip()
        
        # Check for direct typos
        for typo, correction in common_typos.items():
            if typo in query:
                corrected = query.replace(typo, correction)
                print(f"DEBUG: Corrected typo '{typo}' to '{correction}'")
                return corrected
        
        # Try using difflib for fuzzy matching if no direct typo found
        try:
            import difflib
            words = query.split()
            corrected_words = []
            
            for word in words:
                # Only check words with 4+ characters
                if len(word) >= 4:
                    # Check against common programming terms
                    common_terms = ['python', 'javascript', 'java', 'ruby', 'golang', 'rust', 
                                   'typescript', 'php', 'swift', 'kotlin', 'csharp', 'cpp',
                                   'bible', 'quran', 'torah', 'books', 'library', 'computer',
                                   'science', 'history', 'math', 'physics', 'biology', 'chemistry']
                    
                    matches = difflib.get_close_matches(word, common_terms, n=1, cutoff=0.8)
                    if matches:
                        corrected_words.append(matches[0])
                        print(f"DEBUG: Fuzzy corrected '{word}' to '{matches[0]}'")
                    else:
                        corrected_words.append(word)
                else:
                    corrected_words.append(word)
            
            corrected_query = ' '.join(corrected_words)
            if corrected_query != query:
                return corrected_query
        except Exception as e:
            print(f"DEBUG: Fuzzy matching error: {e}")
        
        return None

    # def _handle_low_confidence(self, user_message: str, confidence, context: Dict = None) -> Dict:
    #     """
    #     Handle cases where intent confidence is low
    #     """
    #     if context is None:
    #         context = {}
    #
    #     # Ensure confidence is a float
    #     try:
    #         if isinstance(confidence, dict):
    #             # If confidence is a dict, try to extract a numeric value
    #             conf_value = confidence.get('score', confidence.get('confidence', 0.0))
    #         else:
    #             conf_value = float(confidence)
    #     except (ValueError, TypeError):
    #         conf_value = 0.0  # Default to low confidence
    #
    #     # Different strategies based on confidence level
    #     if conf_value < 0.3:
    #         # Very low confidence - ask for clarification
    #         responses = [
    #             "I'm not quite sure what you mean. Could you rephrase that?",
    #             "I want to make sure I understand correctly. Could you say that differently?",
    #             "I'm having trouble understanding. Could you provide more details?"
    #         ]
    #         import random
    #         response = random.choice(responses)
    #         action = 'clarify'
    #
    #     elif conf_value < 0.5:
    #         # Medium-low confidence - offer suggestions
    #         responses = [
    #             "I think you might be asking about: (1) Library hours, (2) Finding books, or (3) Borrowing policies. Which one interests you?",
    #             "Could this be about: Library hours, Book search, or Borrowing information?",
    #             "I can help with library hours, book searches, or borrowing questions. Which would you like?"
    #         ]
    #         import random
    #         response = random.choice(responses)
    #         action = 'suggest'
    #
    #     else:
    #         # Confidence is okay, but we still want to verify
    #         responses = [
    #             f"Just to make sure I understood: are you asking about '{user_message}'?",
    #             f"I think you're asking about: {user_message}. Is that correct?",
    #             f"Let me confirm: you want to know about '{user_message}', right?"
    #         ]
    #         import random
    #         response = random.choice(responses)
    #         action = 'confirm'
    #
    #     # Generate follow-up questions
    #     follow_ups = self._get_clarification_questions(user_message, conf_value)
    #
    #     return {
    #         'response': response,
    #         'action': action,
    #         'confidence': conf_value,
    #         'requires_clarification': True,
    #         'suggested_follow_ups': follow_ups,
    #         'original_message': user_message
    #     }

    def _get_clarification_questions(self, user_message: str, confidence) -> List[str]:
        """
        Generate clarification questions based on the user's message
        """
        # Ensure confidence is numeric
        try:
            conf_value = float(confidence)
        except (ValueError, TypeError):
            conf_value = 0.0

        questions = []

        # Common library topics to suggest
        library_topics = [
            "Library hours and schedule",
            "Finding and searching for books",
            "Borrowing and returning books",
            "Library policies and rules",
            "Research assistance",
            "Using library computers"
        ]

        # If confidence is very low, offer general topics
        if conf_value < 0.3:
            questions = library_topics[:3]

        # If we detect some keywords, offer related topics
        user_lower = user_message.lower()

        if any(word in user_lower for word in ['hour', 'time', 'open', 'close']):
            questions = ["Library opening hours", "Weekend hours", "Holiday schedule"]
        elif any(word in user_lower for word in ['book', 'find', 'search', 'look']):
            questions = ["Search by title", "Search by author", "E-book availability"]
        elif any(word in user_lower for word in ['borrow', 'loan', 'return', 'due']):
            questions = ["Borrowing period", "Late fees", "Renewing books"]
        else:
            # Default suggestions
            questions = ["Library hours", "Book search", "Borrowing information"]

        return questions

    def _determine_state(self, user_id: str, session_id: str, intent: str, confidence: float,
                         context: Dict = None) -> str:
        """
        Determine the current conversation state based on intent and context

        Returns:
            State string: 'greeting', 'searching', 'clarifying', 'confirming', 'completed', etc.
        """
        if context is None:
            context = {}

        # Get conversation history for this session
        history_key = f"{user_id}_{session_id}"
        conversation_history = context.get('history', [])

        # If this is first message, it's likely greeting
        if len(conversation_history) == 0:
            return 'greeting'

        # Check confidence level
        if confidence < 0.3:
            return 'clarifying'
        elif confidence < 0.6:
            return 'confirming'

        # Determine state based on intent
        intent_state_map = {
            'greeting': 'greeting',
            'farewell': 'farewell',
            'book_search': 'searching',
            'library_hours': 'informing',
            'borrowing_info': 'explaining',
            'research_help': 'assisting',
            'unknown': 'clarifying'
        }

        # Check if we're in a multi-turn conversation
        last_intent = None
        if conversation_history:
            last_intent = conversation_history[-1].get('intent')

        # If same intent repeated, might need clarification
        if last_intent == intent:
            return 'clarifying'

        # Get state from map or default
        return intent_state_map.get(intent, 'conversing')

    def _log_interaction(self, user_id: str, session_id: str, message: str,
                         response: str, intent: str, confidence: float,
                         processing_method: str, context: Dict = None):
        """
        Log user interaction for analytics and conversation tracking
        """
        if context is None:
            context = {}

        import time
        import json

        log_entry = {
            'timestamp': time.time(),
            'datetime': time.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': user_id,
            'session_id': session_id,
            'user_message': message,
            'bot_response': response,
            'intent': intent,
            'confidence': float(confidence),
            'processing_method': processing_method,
            'context': context
        }

        # Print to console for debugging
        print(f"\n📝 INTERACTION LOG:")
        print(f"  User: {user_id}")
        print(f"  Session: {session_id}")
        print(f"  Message: '{message}'")
        print(f"  Response: '{response}'")
        print(f"  Intent: {intent} (confidence: {confidence:.2f})")
        print(f"  Method: {processing_method}")

        # You could also save to database or file here
        # Example: Save to JSON file
        try:
            log_file = 'chat_logs.json'
            logs = []

            # Try to read existing logs
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass

            # Add new log
            logs.append(log_entry)

            # Save back to file (limit to last 1000 entries)
            with open(log_file, 'w') as f:
                json.dump(logs[-1000:], f, indent=2, default=str)

        except Exception as e:
            print(f"⚠️ Failed to save log: {e}")

        # Update conversation history in context
        if 'conversation_history' not in context:
            context['conversation_history'] = []

        context['conversation_history'].append({
            'role': 'user',
            'message': message,
            'timestamp': log_entry['timestamp']
        })

        context['conversation_history'].append({
            'role': 'bot',
            'message': response,
            'intent': intent,
            'timestamp': log_entry['timestamp']
        })

        # Keep only last 20 messages to prevent memory issues
        if len(context['conversation_history']) > 20:
            context['conversation_history'] = context['conversation_history'][-20:]

        return context

    def _suggest_follow_ups(self, intent: str, confidence: float,
                            current_state: str, context: Dict = None) -> List[str]:
        """
        Generate relevant follow-up questions based on the conversation
        """
        if context is None:
            context = {}

        # Get conversation history
        history = context.get('conversation_history', [])

        # Base follow-ups by intent
        intent_follow_ups = {
            'greeting': [
                "What are the library hours?",
                "How do I search for books?",
                "What are the borrowing policies?",
                "Can you help with research?"
            ],
            'library_hours': [
                "What are weekend hours?",
                "Are you open on holidays?",
                "When is the library busiest?",
                "Do you have extended exam hours?"
            ],
            'book_search': [
                "How do I search by author?",
                "Can I search for e-books?",
                "How do I reserve a book?",
                "What if the book is checked out?"
            ],
            'borrowing_info': [
                "How long can I borrow books?",
                "What are the late fees?",
                "How do I renew a book?",
                "Can I borrow reference books?"
            ],
            'research_help': [
                "How do I access journals?",
                "Can you help with citations?",
                "Are there research guides?",
                "How do I use databases?"
            ],
            'research_assistance': [
                "Help me find journal articles",
                "How do I access databases?",
                "Citation help (APA/MLA)",
                "Research consultation booking"
            ],
            'unknown': [
                "Tell me about library hours",
                "How do I find a book?",
                "What are the borrowing rules?",
                "Can you help with research?"
            ]
        }

        # Get base suggestions
        suggestions = intent_follow_ups.get(intent, intent_follow_ups['unknown'])

        # Adjust based on confidence
        if confidence < 0.4:
            # Low confidence - offer broader options
            suggestions = [
                "Library hours information",
                "Book search help",
                "Borrowing policies",
                "Research assistance"
            ]
        elif confidence > 0.8:
            # High confidence - offer more specific follow-ups
            if intent == 'book_search':
                suggestions = [
                    "Search for fiction books",
                    "Find textbooks for my course",
                    "Look up books by a specific author",
                    "Check if a book is available"
                ]
            elif intent == 'library_hours':
                suggestions = [
                    "Today's opening hours",
                    "Weekend schedule",
                    "Special holiday hours",
                    "Quiet study hours"
                ]

        # Adjust based on conversation state
        if current_state == 'clarifying':
            suggestions = ["Could you rephrase?", "What specifically are you asking?",
                           "Let me try to understand better..."]
        elif current_state == 'confirming':
            suggestions = ["Yes, that's correct", "No, let me clarify", "Partly, but also..."]

        # Limit to 3-4 suggestions
        import random
        if len(suggestions) > 4:
            suggestions = random.sample(suggestions, 4)

        return suggestions

    def _create_borrow_request(self, user_id: str, book_info: Dict) -> Dict:
        """Create a borrow request for a book"""
        from app.model import BorrowRequest, Book
        from app.extensions import db
        
        try:
            book_id = book_info.get('id')
            if book_id:
                book = Book.query.get(book_id)
                if book:
                    existing = BorrowRequest.query.filter_by(
                        user_id=user_id,
                        book_id=book_id,
                        status='active'
                    ).first()
                    if existing:
                        return {'success': False, 'message': 'You already have this book borrowed.'}
                    
                    borrow = BorrowRequest(
                        user_id=user_id,
                        book_id=book_id,
                        status='pending',
                        admin_notes=f"Borrowed via chatbot: {book.title}"
                    )
                    db.session.add(borrow)
                    db.session.commit()
                    return {'success': True, 'message': f'Successfully submitted borrow request for "{book.title}"! You can check your borrow requests in your account.'}
            
            return {'success': False, 'message': 'Book not found in local catalog.'}
        except Exception as e:
            print(f"Error creating borrow request: {e}")
            return {'success': False, 'message': 'Sorry, I encountered an error while submitting your borrow request. Please try again.'}

    def _create_reservation(self, user_id: str, book_info: Dict) -> Dict:
        """Create a reservation for a book"""
        from app.model import ReserveRequest, Book
        from app.extensions import db
        
        try:
            book_id = book_info.get('id')
            if book_id:
                book = Book.query.get(book_id)
                if book:
                    reservation = ReserveRequest(
                        user_id=user_id,
                        book_id=book_id,
                        status='active',
                        notes=f"Reserved via chatbot: {book.title}"
                    )
                    db.session.add(reservation)
                    db.session.commit()
                    return {'success': True, 'message': f'Successfully reserved "{book.title}"! You can pick it up at the library. Check your reservations in your account.'}
            
            # For OpenLibrary books without book_id
            title = book_info.get('title', 'Unknown')
            reservation = ReserveRequest(
                user_id=user_id,
                book_id=None,
                status='pending',
                notes=f"Reserved via chatbot (external): {title}"
            )
            db.session.add(reservation)
            db.session.commit()
            return {'success': True, 'message': f'Successfully reserved "{title}"! Note: This is an external book. Please contact the library for pickup instructions.'}
        except Exception as e:
            print(f"Error creating reservation: {e}")
            return {'success': False, 'message': 'Sorry, I encountered an error while submitting your reservation. Please try again.'}


