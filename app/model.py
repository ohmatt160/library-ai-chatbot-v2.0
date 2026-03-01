# ====================== DATABASE MODELS ======================
from datetime import datetime
import uuid
from flask_login import UserMixin
from flask_restful import reqparse
from .extensions import db, ma, bcrypt


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    user_type = db.Column(db.Enum('Student', 'Staff', 'Faculty', 'Guest', 'Admin'), default='Guest')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    borrowed_books = db.Column(db.JSON, default=list)  # List of book IDs and due dates

    # Relationships
    sessions = db.relationship('UserSession', backref='user', lazy=True)
    activities = db.relationship('ActivityLog', backref='user', lazy=True)
    feedbacks = db.relationship('Feedback', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class UserSession(db.Model):
    __tablename__ = 'user_sessions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    logout_time = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    session_id = db.Column(db.String(100))
    activity_type = db.Column(
        db.Enum('login', 'logout', 'chat_message', 'book_search', 'feedback', 'system_interaction'), nullable=False)
    activity_details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    message_id = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Enum('thumbs_up', 'thumbs_down', 'neutral'), nullable=False)
    comment = db.Column(db.Text)
    corrected_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    isbn = db.Column(db.String(20), unique=True)
    topic = db.Column(db.String(100))
    copies_available = db.Column(db.Integer, default=1)
    location = db.Column(db.String(100))
    summary = db.Column(db.Text)


class SurveyResponse(db.Model):
    """Store user satisfaction survey responses"""
    __tablename__ = 'survey_responses'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(100))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    answers = db.Column(db.JSON)  # Store answers as JSON
    overall_rating = db.Column(db.Integer)  # 1-5 rating
    satisfaction_score = db.Column(db.Float)  # Calculated score
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class IntentPrediction(db.Model):
    """Store intent classification predictions for F1-score calculation"""
    __tablename__ = 'intent_predictions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(100))
    message = db.Column(db.Text)  # User message
    predicted_intent = db.Column(db.String(100))  # What chatbot predicted
    true_intent = db.Column(db.String(100))  # Actual intent (can be set later or from corrections)
    confidence = db.Column(db.Float)  # Prediction confidence
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Contact(db.Model):
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    department = db.Column(db.String(100), nullable=True)  # Optional - can be empty for user inquiries
    name = db.Column(db.String(100))  # Contact person name
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    hours = db.Column(db.String(100))
    subject = db.Column(db.String(200))  # Subject area
    message = db.Column(db.Text)  # Contact message
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BorrowRequest(db.Model):
    """Store book borrowing requests"""
    __tablename__ = 'borrow_requests'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum('pending', 'approved', 'denied', 'picked_up', 'returned'), default='pending')
    admin_notes = db.Column(db.Text)
    processed_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    processed_date = db.Column(db.DateTime)
    pickup_deadline = db.Column(db.DateTime)
    return_date = db.Column(db.DateTime)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='borrow_requests')
    book = db.relationship('Book', backref='borrow_requests')
    processed_by_user = db.relationship('User', foreign_keys=[processed_by])
    history = db.relationship('BorrowHistory', backref='request', lazy=True, cascade='all, delete-orphan')


class BorrowHistory(db.Model):
    """Track history of borrow request actions"""
    __tablename__ = 'borrow_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    request_id = db.Column(db.Integer, db.ForeignKey('borrow_requests.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # created, approved, denied, picked_up, returned
    action_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    action_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    # Relationships
    user = db.relationship('User', foreign_keys=[action_by])


class Notification(db.Model):
    """Store user notifications"""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.Enum('borrow_request', 'borrow_approved', 'borrow_denied', 'pickup_reminder', 'general'), default='general')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='notifications')


class ReserveRequest(db.Model):
    """Store book reservation requests"""
    __tablename__ = 'reserve_requests'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=True)  # Nullable for OpenLibrary books
    reserve_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='active')  # Using String instead of Enum for flexibility
    notify_when_available = db.Column(db.Boolean, default=True)
    fulfilled_date = db.Column(db.DateTime)
    cancelled_date = db.Column(db.DateTime)
    expiry_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)  # For storing OpenLibrary book info

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='reserve_requests')
    book = db.relationship('Book', backref='reserve_requests')


# ====================== MARSHMALLOW SCHEMAS ======================

class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User

    id = ma.auto_field()
    username = ma.auto_field()
    email = ma.auto_field()
    first_name = ma.auto_field()
    last_name = ma.auto_field()
    user_type = ma.auto_field()
    created_at = ma.auto_field()
    last_login = ma.auto_field()
    is_active = ma.auto_field()


class ActivityLogSchema(ma.SQLAlchemySchema):
    class Meta:
        model = ActivityLog

    id = ma.auto_field()
    activity_type = ma.auto_field()
    activity_details = ma.auto_field()
    timestamp = ma.auto_field()
    ip_address = ma.auto_field()


class FeedbackSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Feedback

    id = ma.auto_field()
    message_id = ma.auto_field()
    rating = ma.auto_field()
    comment = ma.auto_field()
    corrected_response = ma.auto_field()
    created_at = ma.auto_field()


class BookSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Book

    id = ma.auto_field()
    title = ma.auto_field()
    author = ma.auto_field()
    isbn = ma.auto_field()
    topic = ma.auto_field()
    copies_available = ma.auto_field()
    location = ma.auto_field()
    summary = ma.auto_field()


class ContactSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Contact

    id = ma.auto_field()
    department = ma.auto_field()
    name = ma.auto_field()
    phone = ma.auto_field()
    email = ma.auto_field()
    hours = ma.auto_field()
    subject = ma.auto_field()
    message = ma.auto_field()
    status = ma.auto_field()
    created_at = ma.auto_field()


class BorrowRequestSchema(ma.SQLAlchemySchema):
    class Meta:
        model = BorrowRequest

    id = ma.auto_field()
    user_id = ma.auto_field()
    book_id = ma.auto_field()
    request_date = ma.auto_field()
    status = ma.auto_field()
    admin_notes = ma.auto_field()
    processed_by = ma.auto_field()
    processed_date = ma.auto_field()
    pickup_deadline = ma.auto_field()
    return_date = ma.auto_field()
    # Include nested relationships
    user = ma.Nested(UserSchema, only=['id', 'username', 'first_name', 'last_name'])
    book = ma.Nested(BookSchema)
    processed_by_user = ma.Nested(UserSchema, only=['id', 'username'])


class BorrowHistorySchema(ma.SQLAlchemySchema):
    class Meta:
        model = BorrowHistory

    id = ma.auto_field()
    request_id = ma.auto_field()
    action = ma.auto_field()
    action_by = ma.auto_field()
    action_date = ma.auto_field()
    notes = ma.auto_field()
    user = ma.Nested(UserSchema, only=['id', 'username'])


class NotificationSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Notification

    id = ma.auto_field()
    user_id = ma.auto_field()
    title = ma.auto_field()
    message = ma.auto_field()
    notification_type = ma.auto_field()
    is_read = ma.auto_field()
    created_at = ma.auto_field()


class ReserveRequestSchema(ma.SQLAlchemySchema):
    class Meta:
        model = ReserveRequest

    id = ma.auto_field()
    user_id = ma.auto_field()
    book_id = ma.auto_field()
    reserve_date = ma.auto_field()
    status = ma.auto_field()
    notify_when_available = ma.auto_field()
    fulfilled_date = ma.auto_field()
    cancelled_date = ma.auto_field()
    expiry_date = ma.auto_field()
    notes = ma.auto_field()
    user = ma.Nested(UserSchema, only=['id', 'username', 'first_name', 'last_name'])
    # Use Method field to provide virtual book data for external reservations
    book = ma.Method("get_book_data")
    
    def get_book_data(self, obj):
        """Get book data from relationship or create virtual book for external reservations"""
        if obj.book:
            # Return actual book data
            return {
                'id': obj.book.id,
                'title': obj.book.title,
                'author': obj.book.author,
                'isbn': obj.book.isbn,
                'source': 'local'
            }
        
        # For external books, parse from notes and return virtual book object
        # Format: "Reserved via chatbot (external): Title by Author" or "Reserved via chatbot (external): Title"
        title = "Unknown Title"
        author = "External Book"
        
        if obj.notes:
            if "external):" in obj.notes:
                content = obj.notes.split("external):", 1)[1].strip()
                # Check if author is included
                if " by " in content:
                    parts = content.rsplit(" by ", 1)
                    title = parts[0].strip()
                    author = parts[1].strip()
                else:
                    title = content
        
        return {
            'id': None,
            'title': title,
            'author': author,
            'isbn': None,
            'source': 'external'
        }


# Initialize schemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)
activity_schema = ActivityLogSchema()
activities_schema = ActivityLogSchema(many=True)
feedback_schema = FeedbackSchema()
feedbacks_schema = FeedbackSchema(many=True)
book_schema = BookSchema()
books_schema = BookSchema(many=True)
contact_schema = ContactSchema()
contacts_schema = ContactSchema(many=True)
borrow_request_schema = BorrowRequestSchema()
borrow_requests_schema = BorrowRequestSchema(many=True)
borrow_history_schema = BorrowHistorySchema()
borrow_histories_schema = BorrowHistorySchema(many=True)
notification_schema = NotificationSchema()
notifications_schema = NotificationSchema(many=True)
reserve_request_schema = ReserveRequestSchema()
reserve_requests_schema = ReserveRequestSchema(many=True)

# ====================== REQUEST PARSERS ======================

register_parser = reqparse.RequestParser()
register_parser.add_argument('username', type=str, required=True, help='Username is required')
register_parser.add_argument('email', type=str, required=True, help='Email is required')
register_parser.add_argument('password', type=str, required=True, help='Password is required')
register_parser.add_argument('first_name', type=str)
register_parser.add_argument('last_name', type=str)
register_parser.add_argument('user_type', type=str, choices=('Student', 'Staff', 'Faculty', 'Guest'), default='Guest')

login_parser = reqparse.RequestParser()
login_parser.add_argument('username', type=str, required=True, help='Username is required')
login_parser.add_argument('password', type=str, required=True, help='Password is required')

chat_parser = reqparse.RequestParser()
chat_parser.add_argument('message', type=str, required=True, help='Message is required')
chat_parser.add_argument('session_id', type=str)

feedback_parser = reqparse.RequestParser()
feedback_parser.add_argument('message_id', type=str, required=True, help='Message ID is required')
feedback_parser.add_argument('rating', type=str, required=True, choices=('thumbs_up', 'thumbs_down', 'neutral'),
                             help='Rating is required')
feedback_parser.add_argument('comment', type=str)
feedback_parser.add_argument('corrected_response', type=str)

search_parser = reqparse.RequestParser()
search_parser.add_argument('q', type=str, required=True, help='Search query is required')
search_parser.add_argument('author', type=str)
search_parser.add_argument('subject', type=str)