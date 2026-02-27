import uuid
import time
from datetime import datetime, timedelta
from flask import request, jsonify, session
from flask_restful import Resource
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, current_user,
    get_jwt
)
from app.extensions import db
from app.model import ActivityLog, User, register_parser, user_schema, login_parser, UserSession, chat_parser, \
    feedback_parser, Feedback, activities_schema, search_parser, users_schema, activity_schema, Book, Contact, book_schema, books_schema, contact_schema, contacts_schema
from app.chatbot import dialogue_manager, metrics_tracker, get_opac_client


def get_client_info():
    return {
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', '')
    }


def log_activity(user_id, session_id, activity_type, details):
    client_info = get_client_info()
    activity = ActivityLog(
        user_id=user_id,
        session_id=session_id,
        activity_type=activity_type,
        activity_details=details,
        **client_info
    )
    db.session.add(activity)
    db.session.commit()


class GetSession(Resource):
    def get(self):
        """Get or create a session"""
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())

        return jsonify({
            'session_id': session['session_id'],
            'user_authenticated': False
        })


class RegisterResource(Resource):
    def post(self):
        """Register a new user"""
        args = register_parser.parse_args()

        if User.query.filter_by(username=args['username']).first():
            return {'error': 'Username already exists'}, 400

        if User.query.filter_by(email=args['email']).first():
            return {'error': 'Email already exists'}, 400

        user = User(
            username=args['username'],
            email=args['email'],
            first_name=args.get('first_name', ''),
            last_name=args.get('last_name', ''),
            user_type=args.get('user_type', 'Guest')
        )
        user.set_password(args['password'])

        db.session.add(user)
        db.session.commit()

        log_activity(user.id, 'registration', 'system_interaction', {
            'action': 'user_registration'
        })

        return {
            'status': 'success',
            'message': 'User created successfully',
            'user': user_schema.dump(user)
        }, 201


class LoginResource(Resource):
    def post(self):
        """Login user and return JWT tokens"""
        args = login_parser.parse_args()

        user = User.query.filter_by(username=args['username']).first()
        if not user or not user.check_password(args['password']):
            return {'error': 'Invalid username or password'}, 401

        if not user.is_active:
            return {'error': 'Account is deactivated'}, 403

        user.last_login = datetime.utcnow()
        db.session.commit()

        # Create JWT tokens with additional claims
        additional_claims = {
            'user_type': user.user_type,
            'username': user.username
        }
        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            additional_claims=additional_claims
        )

        session_id = str(uuid.uuid4())

        # Record session
        client_info = get_client_info()
        user_session = UserSession(
            user_id=user.id,
            session_id=session_id,
            **client_info
        )
        db.session.add(user_session)
        db.session.commit()

        log_activity(user.id, session_id, 'login', {'method': 'password'})

        return {
            'status': 'success',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_schema.dump(user),
            'session_id': session_id
        }


class LogoutResource(Resource):
    @jwt_required()
    def post(self):
        """Logout user"""
        user_id = get_jwt_identity()

        log_activity(user_id, session.get('session_id', ''), 'logout', {})

        # Invalidate active sessions
        active_sessions = UserSession.query.filter_by(
            user_id=user_id,
            is_active=True
        ).all()
        for s in active_sessions:
            s.logout_time = datetime.utcnow()
            s.is_active = False
        db.session.commit()

        return {'status': 'success', 'message': 'Logged out'}


class ProfileResource(Resource):
    @jwt_required()
    def get(self):
        """Get current user profile"""
        user = User.query.get(get_jwt_identity())
        if not user:
            return {'error': 'User not found'}, 404
        return user_schema.dump(user)


class ChatResource(Resource):
    def post(self):
        """Handle chat messages"""
        args = chat_parser.parse_args()

        session_id = args.get('session_id') or session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id

        # Try to get user from JWT if provided
        user_id = None
        user_type = 'Guest'
        is_authenticated = False
        try:
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request(optional=True)
            jwt_identity = get_jwt_identity()
            if jwt_identity:
                user_id = jwt_identity
                jwt_data = get_jwt()
                user_type = jwt_data.get('user_type', 'Guest')
                is_authenticated = True
        except Exception:
            pass

        if not user_id:
            user_id = f"anon_{session_id}"

        start_time = time.time()

        try:
            result = dialogue_manager.process_message(
                user_id=user_id,
                session_id=session_id,
                message=args['message']
            )

            required_keys = ['response', 'confidence', 'processing_method']
            for key in required_keys:
                if key not in result:
                    raise KeyError(f"Missing required key in result: {key}")

            if not isinstance(result['response'], str):
                result['response'] = str(result['response'])

            if not result['response']:
                result['response'] = "I'm here to help with library services."

            if not isinstance(result['confidence'], (int, float)):
                result['confidence'] = 0.0
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'error': 'Processing error', 'message': str(e)}, 500

        response_time = (time.time() - start_time) * 1000

        if is_authenticated and user_id:
            log_activity(user_id, session_id, 'chat_message', {
                'message': args['message'],
                'response_time_ms': response_time,
                'confidence': result.get('confidence', 0),
                'intent': result.get('intent', 'unknown')
            })

        metrics_tracker.record_interaction(
            user_id=user_id,
            session_id=session_id,
            message=args['message'],
            response=result['response'],
            response_time=response_time,
            confidence=result['confidence'],
            method=result.get('processing_method', 'unknown')
        )

        return {
            'response': result['response'],
            'session_id': session_id,
            'response_time_ms': round(response_time, 2),
            'confidence': round(result['confidence'], 3),
            'processing_method': result['processing_method'],
            'suggested_follow_ups': result.get('suggested_follow_ups', []),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'user_authenticated': is_authenticated,
            'user_type': user_type
        }


class FeedbackResource(Resource):
    def post(self):
        """Submit feedback"""
        args = feedback_parser.parse_args()

        # Try to get user from JWT if provided
        user_id = None
        try:
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request(optional=True)
            jwt_identity = get_jwt_identity()
            if jwt_identity:
                user_id = jwt_identity
        except Exception:
            pass

        feedback = Feedback(
            user_id=user_id,
            message_id=args['message_id'],
            rating=args['rating'],
            comment=args.get('comment', ''),
            corrected_response=args.get('corrected_response', '')
        )

        db.session.add(feedback)
        db.session.commit()

        if user_id:
            log_activity(user_id, session.get('session_id', ''), 'feedback', {
                'message_id': args['message_id'],
                'rating': args['rating']
            })

        # Update learning if correction provided
        if args['rating'] == 'thumbs_down' and args.get('corrected_response'):
            from app.models.feedback_module import update_knowledge_base
            update_knowledge_base(
                original_message_id=args['message_id'],
                corrected_response=args['corrected_response']
            )

        return {
            'status': 'success',
            'feedback_id': feedback.id,
            'message': 'Thank you for your feedback!'
        }


class QuestionnaireResource(Resource):
    """API endpoints for user satisfaction questionnaire"""
    
    def get(self):
        """Get the questionnaire questions"""
        from app.utils.metrics import UserSatisfactionQuestionnaire
        questionnaire = UserSatisfactionQuestionnaire()
        return {
            'status': 'success',
            'questionnaire': questionnaire.get_questionnaire()
        }
    
    def post(self):
        """Submit questionnaire response - saves to database"""
        from flask import request
        from flask_jwt_extended import get_jwt_identity
        from app.model import SurveyResponse
        from app.extensions import db
        from datetime import datetime
        
        data = request.get_json()
        
        session_id = data.get('session_id', '')
        user_id = data.get('user_id')
        answers = data.get('answers', {})
        overall_rating = data.get('overall_rating')
        
        # Try to get user from JWT
        try:
            jwt_identity = get_jwt_identity()
            if jwt_identity:
                user_id = jwt_identity
        except Exception:
            pass
        
        # Calculate satisfaction score
        likert_scores = []
        for ans in answers.values():
            if isinstance(ans, (int, float)):
                likert_scores.append(ans)
        satisfaction_score = sum(likert_scores) / len(likert_scores) if likert_scores else 0
        
        # Save to database
        survey = SurveyResponse(
            session_id=session_id,
            user_id=user_id,
            answers=answers,
            overall_rating=overall_rating,
            satisfaction_score=satisfaction_score
        )
        db.session.add(survey)
        db.session.commit()
        
        return {
            'status': 'success',
            'message': 'Thank you for your feedback!',
            'satisfaction_score': satisfaction_score
        }


class QuestionnaireStatsResource(Resource):
    """Get questionnaire statistics (admin only)"""
    
    @jwt_required()
    def get(self):
        """Get satisfaction statistics from database"""
        from flask import request
        from app.model import SurveyResponse
        from app.extensions import db
        from datetime import datetime
        from collections import Counter
        import statistics
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = SurveyResponse.query
        
        if start_date:
            start = datetime.fromisoformat(start_date)
            query = query.filter(SurveyResponse.created_at >= start)
        if end_date:
            end = datetime.fromisoformat(end_date)
            query = query.filter(SurveyResponse.created_at <= end)
        
        responses = query.all()
        
        if not responses:
            return {
                'status': 'success',
                'statistics': {
                    'total_responses': 0,
                    'message': 'No survey responses yet'
                }
            }
        
        # Calculate statistics
        satisfaction_scores = [r.satisfaction_score for r in responses if r.satisfaction_score]
        overall_ratings = [r.overall_rating for r in responses if r.overall_rating]
        
        # Calculate per-question averages
        question_stats = {}
        all_answers = {}
        for r in responses:
            if r.answers:
                for q_id, ans in r.answers.items():
                    if isinstance(ans, (int, float)):
                        if q_id not in all_answers:
                            all_answers[q_id] = []
                        all_answers[q_id].append(ans)
        
        for q_id, scores in all_answers.items():
            question_stats[q_id] = {
                'question': f'Question {q_id}',
                'mean': statistics.mean(scores),
                'median': statistics.median(scores),
                'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0,
                'min': min(scores),
                'max': max(scores),
                'total_responses': len(scores)
            }
        
        # NPS calculation
        would_use_again = sum(1 for r in responses if r.answers and r.answers.get('q5') in ['Yes', 'yes', True])
        nps_score = (would_use_again / len(responses)) * 100 if responses else 0
        
        # Rating distribution
        rating_dist = Counter(overall_ratings)
        
        return {
            'status': 'success',
            'statistics': {
                'total_responses': len(responses),
                'overall_satisfaction': {
                    'mean': statistics.mean(satisfaction_scores) if satisfaction_scores else 0,
                    'median': statistics.median(satisfaction_scores) if satisfaction_scores else 0,
                    'std_dev': statistics.stdev(satisfaction_scores) if len(satisfaction_scores) > 1 else 0
                },
                'overall_rating': {
                    'mean': statistics.mean(overall_ratings) if overall_ratings else 0,
                    'distribution': dict(rating_dist)
                },
                'question_statistics': question_stats,
                'nps_score': nps_score,
                'would_use_again': f"{would_use_again}/{len(responses)}"
            }
        }


class EvaluationReportResource(Resource):
    """Get F1 score and evaluation reports (admin only)"""
    
    @jwt_required()
    def get(self):
        """Get classification report with F1 scores from database"""
        from app.model import IntentPrediction
        from app.extensions import db
        from collections import defaultdict
        
        predictions = IntentPrediction.query.all()
        
        if not predictions:
            return {
                'status': 'success',
                'report': {
                    'precision': 0,
                    'recall': 0,
                    'f1_score': 0,
                    'average_type': 'weighted',
                    'total_samples': 0,
                    'per_class': {},
                    'message': 'No F1 data yet - intent predictions will be recorded automatically'
                }
            }
        
        # Calculate F1 from actual predictions
        true_labels = [p.true_intent if p.true_intent else p.predicted_intent for p in predictions]
        predicted_labels = [p.predicted_intent for p in predictions]
        
        # Build confusion matrix and calculate metrics
        all_labels = set(true_labels) | set(predicted_labels)
        per_class = {}
        
        for label in all_labels:
            tp = sum(1 for t, p in zip(true_labels, predicted_labels) if t == label and p == label)
            fp = sum(1 for t, p in zip(true_labels, predicted_labels) if t != label and p == label)
            fn = sum(1 for t, p in zip(true_labels, predicted_labels) if t == label and p != label)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            per_class[label] = {
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'support': true_labels.count(label)
            }
        
        # Calculate weighted averages
        total_support = sum(m['support'] for m in per_class.values())
        avg_precision = sum(m['precision'] * m['support'] for m in per_class.values()) / total_support
        avg_recall = sum(m['recall'] * m['support'] for m in per_class.values()) / total_support
        avg_f1 = sum(m['f1_score'] * m['support'] for m in per_class.values()) / total_support
        
        return {
            'status': 'success',
            'report': {
                'precision': avg_precision,
                'recall': avg_recall,
                'f1_score': avg_f1,
                'average_type': 'weighted',
                'total_samples': len(predictions),
                'per_class': per_class
            }
        }


class ActivityResource(Resource):
    @jwt_required()
    def get(self):
        """Get user's activity logs"""
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        activities = ActivityLog.query.filter_by(user_id=user_id) \
            .order_by(ActivityLog.timestamp.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

        return {
            'activities': activities_schema.dump(activities.items),
            'total': activities.total,
            'page': activities.page,
            'per_page': activities.per_page,
            'total_pages': activities.pages
        }


class BookSearchResource(Resource):
    def get(self):
        """Search books"""
        # Use Flask's request.args for GET requests instead of reqparse
        query = request.args.get('q', '')
        author = request.args.get('author', '')
        subject = request.args.get('subject', '')
        limit = int(request.args.get('limit', 20))

        if not query and not author and not subject:
            return {'error': 'At least one search parameter is required'}, 400

        # Try to log activity if user is authenticated
        try:
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request(optional=True)
            jwt_identity = get_jwt_identity()
            if jwt_identity:
                log_activity(jwt_identity, session.get('session_id', ''), 'book_search', {
                    'query': query,
                    'author': author,
                    'subject': subject
                })
        except Exception:
            pass

        # Search local database first
        from app.utils.database import search_catalog
        local_results = search_catalog(query=query, author=author, subject=subject, limit=limit)
        
        # Also try external OPAC search
        opac_client = get_opac_client()
        opac_results = opac_client.search(query, author, subject)
        
        # Combine results
        results = local_results + opac_results

        return {
            'query': query,
            'count': len(results),
            'results': results[:limit],
            'source': 'local+opac'
        }


class AdminUsersResource(Resource):
    @jwt_required()
    def get(self):
        """Get all users (admin only)"""
        jwt_data = get_jwt()
        if jwt_data.get('user_type') != 'Admin':
            return {'error': 'Unauthorized'}, 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)

        users = User.query.order_by(User.created_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

        return {
            'users': users_schema.dump(users.items),
            'total': users.total,
            'page': users.page,
            'per_page': users.per_page
        }


class AdminActivitiesResource(Resource):
    @jwt_required()
    def get(self):
        """Get all activities (admin only)"""
        jwt_data = get_jwt()
        if jwt_data.get('user_type') != 'Admin':
            return {'error': 'Unauthorized'}, 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)

        activities = ActivityLog.query \
            .join(User, ActivityLog.user_id == User.id) \
            .add_columns(User.username, User.user_type) \
            .order_by(ActivityLog.timestamp.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

        results = []
        for activity, username, user_type in activities.items:
            result = activity_schema.dump(activity)
            result['username'] = username
            result['user_type'] = user_type
            results.append(result)

        return {
            'activities': results,
            'total': activities.total,
            'page': activities.page,
            'per_page': activities.per_page
        }


class AdminMetricsResource(Resource):
    @jwt_required()
    def get(self):
        """Get system metrics (admin only)"""
        jwt_data = get_jwt()
        if jwt_data.get('user_type') != 'Admin':
            return {'error': 'Unauthorized'}, 403

        user_stats = db.session.query(
            User.user_type,
            db.func.count(User.id).label('count'),
            db.func.date(User.created_at).label('date')
        ).group_by(User.user_type, db.func.date(User.created_at)).all()

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        activity_stats = db.session.query(
            ActivityLog.activity_type,
            db.func.count(ActivityLog.id).label('count'),
            db.func.date(ActivityLog.timestamp).label('date')
        ).filter(ActivityLog.timestamp >= thirty_days_ago) \
            .group_by(ActivityLog.activity_type, db.func.date(ActivityLog.timestamp)) \
            .order_by(db.func.date(ActivityLog.timestamp).desc()).all()

        chat_stats = db.session.query(
            db.func.date(ActivityLog.timestamp).label('date'),
            db.func.count(ActivityLog.id).label('chat_count')
        ).filter(
            ActivityLog.timestamp >= thirty_days_ago,
            ActivityLog.activity_type == 'chat_message'
        ).group_by(db.func.date(ActivityLog.timestamp)) \
            .order_by(db.func.date(ActivityLog.timestamp).desc()).all()

        return {
            'user_statistics': [
                {'user_type': stat.user_type, 'count': stat.count, 'date': str(stat.date)}
                for stat in user_stats
            ],
            'activity_statistics': [
                {'activity_type': stat.activity_type, 'count': stat.count, 'date': str(stat.date)}
                for stat in activity_stats
            ],
            'chat_statistics': [
                {'date': str(stat.date), 'chat_count': stat.chat_count}
                for stat in chat_stats
            ],
            'system_metrics': metrics_tracker.get_all_metrics(),
            'total_users': User.query.count(),
            'total_activities': ActivityLog.query.count()
        }


class AdminBooksResource(Resource):
    @jwt_required()
    def get(self):
        """Get all books (admin only)"""
        jwt_data = get_jwt()
        if jwt_data.get('user_type') != 'Admin':
            return {'error': 'Unauthorized'}, 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '')

        query = Book.query
        if search:
            query = query.filter(
                (Book.title.ilike(f'%{search}%')) |
                (Book.author.ilike(f'%{search}%')) |
                (Book.topic.ilike(f'%{search}%'))
            )

        books = query.order_by(Book.id.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return {
            'books': books_schema.dump(books.items),
            'total': books.total,
            'page': books.page,
            'per_page': books.per_page,
            'total_pages': books.pages
        }

    @jwt_required()
    def post(self):
        """Add a new book (admin only)"""
        jwt_data = get_jwt()
        if jwt_data.get('user_type') != 'Admin':
            return {'error': 'Unauthorized'}, 403

        data = request.get_json()
        if not data:
            return {'error': 'No data provided'}, 400

        required_fields = ['title', 'author']
        for field in required_fields:
            if field not in data or not data[field]:
                return {'error': f'{field} is required'}, 400

        # Check for duplicate ISBN
        if data.get('isbn'):
            existing = Book.query.filter_by(isbn=data['isbn']).first()
            if existing:
                return {'error': 'A book with this ISBN already exists'}, 400

        book = Book(
            title=data['title'],
            author=data['author'],
            isbn=data.get('isbn'),
            topic=data.get('topic'),
            copies_available=data.get('copies_available', 1),
            location=data.get('location'),
            summary=data.get('summary')
        )

        db.session.add(book)
        db.session.commit()

        log_activity(
            get_jwt_identity(),
            session.get('session_id', ''),
            'book_added',
            {'book_id': book.id, 'title': book.title}
        )

        return {
            'status': 'success',
            'message': 'Book added successfully',
            'book': book_schema.dump(book)
        }, 201


class AdminBookResource(Resource):
    @jwt_required()
    def get(self, book_id):
        """Get a specific book (admin only)"""
        jwt_data = get_jwt()
        if jwt_data.get('user_type') != 'Admin':
            return {'error': 'Unauthorized'}, 403

        book = Book.query.get(book_id)
        if not book:
            return {'error': 'Book not found'}, 404

        return book_schema.dump(book)

    @jwt_required()
    def put(self, book_id):
        """Update a book (admin only)"""
        jwt_data = get_jwt()
        if jwt_data.get('user_type') != 'Admin':
            return {'error': 'Unauthorized'}, 403

        book = Book.query.get(book_id)
        if not book:
            return {'error': 'Book not found'}, 404

        data = request.get_json()
        if not data:
            return {'error': 'No data provided'}, 400

        # Check for duplicate ISBN if changing
        if data.get('isbn') and data['isbn'] != book.isbn:
            existing = Book.query.filter_by(isbn=data['isbn']).first()
            if existing:
                return {'error': 'A book with this ISBN already exists'}, 400

        if 'title' in data:
            book.title = data['title']
        if 'author' in data:
            book.author = data['author']
        if 'isbn' in data:
            book.isbn = data['isbn']
        if 'topic' in data:
            book.topic = data['topic']
        if 'copies_available' in data:
            book.copies_available = data['copies_available']
        if 'location' in data:
            book.location = data['location']
        if 'summary' in data:
            book.summary = data['summary']

        db.session.commit()

        log_activity(
            get_jwt_identity(),
            session.get('session_id', ''),
            'book_updated',
            {'book_id': book.id, 'title': book.title}
        )

        return {
            'status': 'success',
            'message': 'Book updated successfully',
            'book': book_schema.dump(book)
        }

    @jwt_required()
    def delete(self, book_id):
        """Delete a book (admin only)"""
        jwt_data = get_jwt()
        if jwt_data.get('user_type') != 'Admin':
            return {'error': 'Unauthorized'}, 403

        book = Book.query.get(book_id)
        if not book:
            return {'error': 'Book not found'}, 404

        book_title = book.title
        db.session.delete(book)
        db.session.commit()

        log_activity(
            get_jwt_identity(),
            session.get('session_id', ''),
            'book_deleted',
            {'book_id': book_id, 'title': book_title}
        )

        return {
            'status': 'success',
            'message': 'Book deleted successfully'
        }


class AdminBooksBulkResource(Resource):
    @jwt_required()
    def post(self):
        """Bulk import books (admin only)"""
        jwt_data = get_jwt()
        if jwt_data.get('user_type') != 'Admin':
            return {'error': 'Unauthorized'}, 403

        data = request.get_json()
        if not data or 'books' not in data:
            return {'error': 'No books data provided'}, 400

        books_data = data['books']
        if not isinstance(books_data, list):
            return {'error': 'Books must be a list'}, 400

        added_books = []
        errors = []

        for idx, book_data in enumerate(books_data):
            try:
                if 'title' not in book_data or 'author' not in book_data:
                    errors.append(f'Row {idx + 1}: Title and author are required')
                    continue

                # Check for duplicate ISBN
                if book_data.get('isbn'):
                    existing = Book.query.filter_by(isbn=book_data['isbn']).first()
                    if existing:
                        errors.append(f'Row {idx + 1}: ISBN {book_data["isbn"]} already exists')
                        continue

                book = Book(
                    title=book_data['title'],
                    author=book_data['author'],
                    isbn=book_data.get('isbn'),
                    topic=book_data.get('topic'),
                    copies_available=book_data.get('copies_available', 1),
                    location=book_data.get('location'),
                    summary=book_data.get('summary')
                )
                db.session.add(book)
                added_books.append(book)

            except Exception as e:
                errors.append(f'Row {idx + 1}: {str(e)}')

        db.session.commit()

        log_activity(
            get_jwt_identity(),
            session.get('session_id', ''),
            'books_bulk_import',
            {'count': len(added_books)}
        )

        return {
            'status': 'success',
            'message': f'Successfully added {len(added_books)} books',
            'added_count': len(added_books),
            'errors': errors if errors else None,
            'books': books_schema.dump(added_books)
        }


class AdminContactsResource(Resource):
    @jwt_required()
    def get(self):
        """Get all contacts (admin only)"""
        jwt_data = get_jwt()
        if jwt_data.get('user_type') != 'Admin':
            return {'error': 'Unauthorized'}, 403

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('q', '')

        # Build query
        query = Contact.query
        
        # Add search if provided
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                db.or_(
                    Contact.name.ilike(search_filter),
                    Contact.email.ilike(search_filter),
                    Contact.subject.ilike(search_filter),
                    Contact.message.ilike(search_filter)
                )
            )

        # Get total count before pagination
        total = query.count()

        # Apply pagination
        contacts = query.order_by(Contact.id.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        ).items

        return {
            'contacts': contacts_schema.dump(contacts),
            'total': total,
            'page': page,
            'per_page': per_page
        }

    @jwt_required()
    def post(self):
        """Add a new contact (admin only)"""
        jwt_data = get_jwt()
        if jwt_data.get('user_type') != 'Admin':
            return {'error': 'Unauthorized'}, 403

        data = request.get_json()
        if not data:
            return {'error': 'No data provided'}, 400

        # Validate required fields - accept name/email/message from frontend
        if 'name' not in data or not data['name']:
            return {'error': 'Name is required'}, 400
        if 'email' not in data or not data['email']:
            return {'error': 'Email is required'}, 400
        if 'message' not in data or not data['message']:
            return {'error': 'Message is required'}, 400

        contact = Contact(
            department=data.get('department', ''),  # Optional - can be empty
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            subject=data.get('subject'),
            message=data.get('message'),
            hours=data.get('hours'),
            status='active'
        )

        db.session.add(contact)
        db.session.commit()

        log_activity(
            get_jwt_identity(),
            session.get('session_id', ''),
            'contact_added',
            {'contact_id': contact.id, 'name': contact.name}
        )

        return {
            'status': 'success',
            'message': 'Contact added successfully',
            'contact': contact_schema.dump(contact)
        }, 201


class AdminContactResource(Resource):
    @jwt_required()
    def get(self, contact_id):
        """Get a specific contact (admin only)"""
        jwt_data = get_jwt()
        if jwt_data.get('user_type') != 'Admin':
            return {'error': 'Unauthorized'}, 403

        contact = Contact.query.get(contact_id)
        if not contact:
            return {'error': 'Contact not found'}, 404

        return contact_schema.dump(contact)

    @jwt_required()
    def put(self, contact_id):
        """Update a contact (admin only)"""
        jwt_data = get_jwt()
        if jwt_data.get('user_type') != 'Admin':
            return {'error': 'Unauthorized'}, 403

        contact = Contact.query.get(contact_id)
        if not contact:
            return {'error': 'Contact not found'}, 404

        data = request.get_json()
        if not data:
            return {'error': 'No data provided'}, 400

        # Update all fields from frontend
        if 'name' in data:
            contact.name = data['name']
        if 'email' in data:
            contact.email = data['email']
        if 'phone' in data:
            contact.phone = data['phone']
        if 'subject' in data:
            contact.subject = data['subject']
        if 'message' in data:
            contact.message = data['message']
        if 'department' in data:
            contact.department = data['department']
        if 'hours' in data:
            contact.hours = data['hours']
        if 'status' in data:
            contact.status = data['status']

        db.session.commit()

        log_activity(
            get_jwt_identity(),
            session.get('session_id', ''),
            'contact_updated',
            {'contact_id': contact.id, 'name': contact.name}
        )

        return {
            'status': 'success',
            'message': 'Contact updated successfully',
            'contact': contact_schema.dump(contact)
        }

    @jwt_required()
    def delete(self, contact_id):
        """Delete a contact (admin only)"""
        jwt_data = get_jwt()
        if jwt_data.get('user_type') != 'Admin':
            return {'error': 'Unauthorized'}, 403

        contact = Contact.query.get(contact_id)
        if not contact:
            return {'error': 'Contact not found'}, 404

        db.session.delete(contact)
        db.session.commit()

        log_activity(
            get_jwt_identity(),
            session.get('session_id', ''),
            'contact_deleted',
            {'contact_id': contact_id}
        )

        return {
            'status': 'success',
            'message': 'Contact deleted successfully'
        }

    @jwt_required()
    def delete(self, contact_id):
        """Delete a contact (admin only)"""
        jwt_data = get_jwt()
        if jwt_data.get('user_type') != 'Admin':
            return {'error': 'Unauthorized'}, 403

        contact = Contact.query.get(contact_id)
        if not contact:
            return {'error': 'Contact not found'}, 404

        dept_name = contact.department
        db.session.delete(contact)
        db.session.commit()

        log_activity(
            get_jwt_identity(),
            session.get('session_id', ''),
            'contact_deleted',
            {'contact_id': contact_id, 'department': dept_name}
        )

        return {
            'status': 'success',
            'message': 'Contact deleted successfully'
        }
