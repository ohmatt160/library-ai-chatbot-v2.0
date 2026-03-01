"""
Borrow API routes for the Intelligent Library Chat Assistant
Handles book borrowing requests, admin management, and analytics
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from app.extensions import db
from app.model import BorrowRequest, BorrowHistory, Notification, Book, User, ReserveRequest
from app.model import borrow_request_schema, borrow_requests_schema, borrow_history_schema, reserve_request_schema, reserve_requests_schema
import json
import time

# Create Blueprint
borrow_bp = Blueprint('borrow', __name__)


@borrow_bp.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify routes are working"""
    return jsonify({'status': 'success', 'message': 'Borrow routes are working!'}), 200


def create_notification(user_id, title, message, notification_type):
    """Helper function to create notifications"""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type
    )
    db.session.add(notification)
    return notification


def add_history(request_id, action, action_by, notes=None):
    """Helper function to add borrow history"""
    history = BorrowHistory(
        request_id=request_id,
        action=action,
        action_by=action_by,
        notes=notes
    )
    db.session.add(history)
    return history


# ====================== USER ENDPOINTS ======================

@borrow_bp.route('/borrow/request', methods=['POST'])
@jwt_required()
def create_borrow_request():
    """Submit a book borrowing request"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data or 'book_id' not in data:
            return jsonify({'error': 'book_id is required'}), 400

        book_id = data['book_id']

        # Check if book exists
        book = Book.query.get(book_id)
        if not book:
            return jsonify({'error': 'Book not found'}), 404

        # Check if copies are available
        if book.copies_available <= 0:
            return jsonify({'error': 'No copies available'}), 400

        # Check for existing pending request
        existing = BorrowRequest.query.filter_by(
            user_id=user_id,
            book_id=book_id,
            status='pending'
        ).first()

        if existing:
            return jsonify({'error': 'You already have a pending request for this book'}), 400

        # Create borrow request
        borrow_request = BorrowRequest(
            user_id=user_id,
            book_id=book_id,
            request_date=datetime.utcnow(),
            status='pending'
        )
        db.session.add(borrow_request)
        db.session.flush()  # Get the request ID

        # Add history
        add_history(borrow_request.id, 'created', user_id)

        # Create notification for admins
        admin_users = User.query.filter_by(user_type='Admin', is_active=True).all()
        for admin in admin_users:
            create_notification(
                admin.id,
                'New Borrow Request',
                f'New borrow request for "{book.title}" from {borrow_request.user.username}',
                'borrow_request'
            )

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Your borrow request has been submitted',
            'request': borrow_request_schema.dump(borrow_request)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@borrow_bp.route('/borrow/my-requests', methods=['GET'])
@jwt_required()
def get_my_requests():
    """Get current user's borrow request history"""
    try:
        user_id = get_jwt_identity()
        status = request.args.get('status')  # Optional filter

        query = BorrowRequest.query.filter_by(user_id=user_id)

        if status:
            query = query.filter_by(status=status)

        requests = query.order_by(BorrowRequest.request_date.desc()).all()

        return jsonify({
            'status': 'success',
            'count': len(requests),
            'requests': borrow_requests_schema.dump(requests)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@borrow_bp.route('/borrow/request/<int:request_id>', methods=['GET'])
@jwt_required()
def get_request_details(request_id):
    """Get details of a specific borrow request"""
    try:
        user_id = get_jwt_identity()

        # Get user to check if admin
        user = User.query.get(user_id)
        is_admin = user.user_type == 'Admin' if user else False

        # Get request
        borrow_request = BorrowRequest.query.get(request_id)
        if not borrow_request:
            return jsonify({'error': 'Request not found'}), 404

        # Check authorization (only owner or admin can view)
        if borrow_request.user_id != user_id and not is_admin:
            return jsonify({'error': 'Unauthorized'}), 403

        return jsonify({
            'status': 'success',
            'request': borrow_request_schema.dump(borrow_request),
            'history': borrow_history_schema.dump(borrow_request.history)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@borrow_bp.route('/borrow/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get user's notifications"""
    try:
        user_id = get_jwt_identity()
        unread_only = request.args.get('unread', 'false').lower() == 'true'

        query = Notification.query.filter_by(user_id=user_id)

        if unread_only:
            query = query.filter_by(is_read=False)

        notifications = query.order_by(Notification.created_at.desc()).limit(50).all()

        return jsonify({
            'status': 'success',
            'count': len(notifications),
            'notifications': [
                {
                    'id': n.id,
                    'title': n.title,
                    'message': n.message,
                    'type': n.notification_type,
                    'is_read': n.is_read,
                    'created_at': n.created_at.isoformat()
                } for n in notifications
            ]
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@borrow_bp.route('/borrow/notifications/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        user_id = get_jwt_identity()

        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()

        if not notification:
            return jsonify({'error': 'Notification not found'}), 404

        notification.is_read = True
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Notification marked as read'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@borrow_bp.route('/borrow/notifications/read-all', methods=['POST'])
@jwt_required()
def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        user_id = get_jwt_identity()

        Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).update({'is_read': True})

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'All notifications marked as read'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ====================== ADMIN ENDPOINTS ======================

@borrow_bp.route('/admin/borrow/requests', methods=['GET'])
@jwt_required()
def get_all_requests():
    """Get all borrow requests (admin only)"""
    try:
        user_id = get_jwt_identity()

        # Check admin
        user = User.query.get(user_id)
        if not user or user.user_type != 'Admin':
            return jsonify({'error': 'Admin access required'}), 403

        status = request.args.get('status')
        user_filter = request.args.get('user_id')
        limit = int(request.args.get('limit', 50))

        query = BorrowRequest.query

        if status:
            query = query.filter_by(status=status)
        if user_filter:
            query = query.filter_by(user_id=user_filter)

        requests = query.order_by(BorrowRequest.request_date.desc()).limit(limit).all()

        return jsonify({
            'status': 'success',
            'count': len(requests),
            'requests': borrow_requests_schema.dump(requests)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@borrow_bp.route('/admin/borrow/requests/pending', methods=['GET'])
@jwt_required()
def get_pending_requests():
    """Get all pending requests (admin only)"""
    try:
        user_id = get_jwt_identity()

        # Check admin
        user = User.query.get(user_id)
        if not user or user.user_type != 'Admin':
            return jsonify({'error': 'Admin access required'}), 403

        requests = BorrowRequest.query.filter_by(status='pending')\
            .order_by(BorrowRequest.request_date.asc()).all()

        return jsonify({
            'status': 'success',
            'count': len(requests),
            'requests': borrow_requests_schema.dump(requests)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@borrow_bp.route('/admin/borrow/approve/<int:request_id>', methods=['POST'])
@jwt_required()
def approve_request(request_id):
    """Approve a borrow request (admin only)"""
    try:
        admin_id = get_jwt_identity()

        # Check admin
        admin = User.query.get(admin_id)
        if not admin or admin.user_type != 'Admin':
            return jsonify({'error': 'Admin access required'}), 403

        # Get request
        borrow_request = BorrowRequest.query.get(request_id)
        if not borrow_request:
            return jsonify({'error': 'Request not found'}), 404

        if borrow_request.status != 'pending':
            return jsonify({'error': f'Cannot approve request with status: {borrow_request.status}'}), 400

        # Get request data
        data = request.get_json() or {}
        pickup_days = data.get('pickup_days', 3)  # Default 3 days

        # Update request
        borrow_request.status = 'approved'
        borrow_request.processed_by = admin_id
        borrow_request.processed_date = datetime.utcnow()
        borrow_request.pickup_deadline = datetime.utcnow() + timedelta(days=pickup_days)
        borrow_request.admin_notes = data.get('notes', '')

        # Add history
        add_history(
            borrow_request.id,
            'approved',
            admin_id,
            data.get('notes', 'Request approved')
        )

        # Create notification for user
        create_notification(
            borrow_request.user_id,
            'Request Approved! 📚',
            f'Your request for "{borrow_request.book.title}" has been approved! '
            f'Please pick up by {borrow_request.pickup_deadline.strftime("%Y-%m-%d")}',
            'borrow_approved'
        )

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Request approved',
            'request': borrow_request_schema.dump(borrow_request)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@borrow_bp.route('/admin/borrow/deny/<int:request_id>', methods=['POST'])
@jwt_required()
def deny_request(request_id):
    """Deny a borrow request (admin only)"""
    try:
        admin_id = get_jwt_identity()

        # Check admin
        admin = User.query.get(admin_id)
        if not admin or admin.user_type != 'Admin':
            return jsonify({'error': 'Admin access required'}), 403

        # Get request
        borrow_request = BorrowRequest.query.get(request_id)
        if not borrow_request:
            return jsonify({'error': 'Request not found'}), 404

        if borrow_request.status != 'pending':
            return jsonify({'error': f'Cannot deny request with status: {borrow_request.status}'}), 400

        # Get denial reason
        data = request.get_json() or {}
        reason = data.get('reason', 'Request denied by administrator')

        # Update request
        borrow_request.status = 'denied'
        borrow_request.processed_by = admin_id
        borrow_request.processed_date = datetime.utcnow()
        borrow_request.admin_notes = reason

        # Add history
        add_history(borrow_request.id, 'denied', admin_id, reason)

        # Create notification for user
        create_notification(
            borrow_request.user_id,
            'Request Denied ❌',
            f'Your request for "{borrow_request.book.title}" has been denied. '
            f'Reason: {reason}',
            'borrow_denied'
        )

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Request denied',
            'request': borrow_request_schema.dump(borrow_request)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@borrow_bp.route('/admin/borrow/mark-picked/<int:request_id>', methods=['POST'])
@jwt_required()
def mark_picked_up(request_id):
    """Mark a request as picked up (admin only)"""
    try:
        admin_id = get_jwt_identity()

        # Check admin
        admin = User.query.get(admin_id)
        if not admin or admin.user_type != 'Admin':
            return jsonify({'error': 'Admin access required'}), 403

        # Get request
        borrow_request = BorrowRequest.query.get(request_id)
        if not borrow_request:
            return jsonify({'error': 'Request not found'}), 404

        if borrow_request.status != 'approved':
            return jsonify({'error': f'Can only mark approved requests as picked up. Current status: {borrow_request.status}'}), 400

        # Update request
        borrow_request.status = 'picked_up'
        borrow_request.processed_by = admin_id
        borrow_request.processed_date = datetime.utcnow()

        # Add history
        add_history(borrow_request.id, 'picked_up', admin_id, 'Book picked up by user')

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Request marked as picked up',
            'request': borrow_request_schema.dump(borrow_request)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@borrow_bp.route('/admin/borrow/mark-returned/<int:request_id>', methods=['POST'])
@jwt_required()
def mark_returned(request_id):
    """Mark a request as returned (admin only)"""
    try:
        admin_id = get_jwt_identity()

        # Check admin
        admin = User.query.get(admin_id)
        if not admin or admin.user_type != 'Admin':
            return jsonify({'error': 'Admin access required'}), 403

        # Get request
        borrow_request = BorrowRequest.query.get(request_id)
        if not borrow_request:
            return jsonify({'error': 'Request not found'}), 404

        if borrow_request.status not in ['approved', 'picked_up']:
            return jsonify({'error': f'Cannot mark as returned. Current status: {borrow_request.status}'}), 400

        # Update request
        borrow_request.status = 'returned'
        borrow_request.return_date = datetime.utcnow()
        borrow_request.processed_by = admin_id

        # Add history
        add_history(borrow_request.id, 'returned', admin_id, 'Book returned')

        # Restore book availability
        book = borrow_request.book
        if book:
            book.copies_available += 1

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Request marked as returned',
            'request': borrow_request_schema.dump(borrow_request)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ====================== ANALYTICS ENDPOINTS ======================

@borrow_bp.route('/admin/borrow/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    """Get borrowing analytics (admin only)"""
    try:
        user_id = get_jwt_identity()

        # Check admin
        user = User.query.get(user_id)
        if not user or user.user_type != 'Admin':
            return jsonify({'error': 'Admin access required'}), 403

        # Get date range filter
        try:
            days = int(request.args.get('days', 30))
        except ValueError:
            days = 30
        start_date = datetime.utcnow() - timedelta(days=days)

        # Initialize default analytics data
        analytics = {
            'total_requests': 0,
            'requests_by_status': {},
            'requests_over_time': [],
            'most_requested_books': [],
            'most_active_borrowers': [],
            'average_approval_hours': 0,
            'approval_rate': 0,
            'denial_reasons': [],
            'pickup_compliance': 0
        }

        # Check if BorrowRequest table exists and has data
        try:
            # Get total count
            total_count = db.session.query(db.func.count(BorrowRequest.id)).filter(BorrowRequest.request_date >= start_date).scalar()
            analytics['total_requests'] = total_count or 0
            
            # Requests by status
            status_counts = db.session.query(
                BorrowRequest.status,
                db.func.count(BorrowRequest.id)
            ).filter(BorrowRequest.request_date >= start_date)\
                .group_by(BorrowRequest.status).all()
            analytics['requests_by_status'] = {status: count for status, count in status_counts}
        except Exception as e:
            print(f"Analytics status error: {e}")

        try:
            # Requests over time (daily)
            daily_requests = db.session.query(
                db.func.date(BorrowRequest.request_date).label('date'),
                db.func.count(BorrowRequest.id)
            ).filter(BorrowRequest.request_date >= start_date)\
                .group_by(db.func.date(BorrowRequest.request_date))\
                .order_by(db.func.date(BorrowRequest.request_date)).all()
            analytics['requests_over_time'] = [
                {'date': str(date), 'count': count}
                for date, count in daily_requests
            ]
        except Exception as e:
            print(f"Analytics daily requests error: {e}")

        try:
            # Most requested books
            top_books = db.session.query(
                Book.id,
                Book.title,
                db.func.count(BorrowRequest.id).label('request_count')
            ).join(BorrowRequest)\
                .filter(BorrowRequest.request_date >= start_date)\
                .group_by(Book.id, Book.title)\
                .order_by(db.desc('request_count'))\
                .limit(10).all()
            analytics['most_requested_books'] = [
                {'id': id, 'title': title, 'count': count}
                for id, title, count in top_books
            ]
        except Exception as e:
            print(f"Analytics top books error: {e}")

        try:
            # Most active borrowers
            top_borrowers = db.session.query(
                User.id,
                User.username,
                User.first_name,
                User.last_name,
                db.func.count(BorrowRequest.id).label('request_count')
            ).join(BorrowRequest)\
                .filter(BorrowRequest.request_date >= start_date)\
                .group_by(User.id, User.username, User.first_name, User.last_name)\
                .order_by(db.desc('request_count'))\
                .limit(10).all()
            analytics['most_active_borrowers'] = [
                {'id': id, 'username': username, 'name': f"{first_name} {last_name}".strip(), 'count': count}
                for id, username, first_name, last_name, count in top_borrowers
            ]
        except Exception as e:
            print(f"Analytics top borrowers error: {e}")

        try:
            # Average approval time
            approved_requests = BorrowRequest.query.filter(
                BorrowRequest.request_date >= start_date,
                BorrowRequest.status.in_(['approved', 'denied', 'picked_up', 'returned']),
                BorrowRequest.processed_date.isnot(None)
            ).all()

            if approved_requests:
                total_hours = sum([
                    (r.processed_date - r.request_date).total_seconds() / 3600
                    for r in approved_requests
                ])
                analytics['average_approval_hours'] = round(total_hours / len(approved_requests), 2)
        except Exception as e:
            print(f"Analytics approval time error: {e}")

        try:
            # Approval rate
            total_decisions = BorrowRequest.query.filter(
                BorrowRequest.request_date >= start_date,
                BorrowRequest.status.in_(['approved', 'denied', 'picked_up', 'returned'])
            ).count()

            approved_count = BorrowRequest.query.filter(
                BorrowRequest.request_date >= start_date,
                BorrowRequest.status.in_(['approved', 'picked_up', 'returned'])
            ).count()

            if total_decisions > 0:
                analytics['approval_rate'] = round((approved_count / total_decisions * 100), 2)
        except Exception as e:
            print(f"Analytics approval rate error: {e}")

        try:
            # Denial reasons
            denial_reasons = db.session.query(
                BorrowRequest.admin_notes,
                db.func.count(BorrowRequest.id)
            ).filter(
                BorrowRequest.request_date >= start_date,
                BorrowRequest.status == 'denied',
                BorrowRequest.admin_notes.isnot(None)
            ).group_by(BorrowRequest.admin_notes).all()
            analytics['denial_reasons'] = [
                {'reason': reason, 'count': count}
                for reason, count in denial_reasons if reason
            ]
        except Exception as e:
            print(f"Analytics denial reasons error: {e}")

        try:
            # Pickup compliance
            picked_up = BorrowRequest.query.filter(
                BorrowRequest.request_date >= start_date,
                BorrowRequest.status.in_(['picked_up', 'returned'])
            ).count()

            expired = BorrowRequest.query.filter(
                BorrowRequest.request_date >= start_date,
                BorrowRequest.status == 'approved',
                BorrowRequest.pickup_deadline < datetime.utcnow()
            ).count()

            if (picked_up + expired) > 0:
                analytics['pickup_compliance'] = round((picked_up / (picked_up + expired) * 100), 2)
        except Exception as e:
            print(f"Analytics pickup compliance error: {e}")

        return jsonify({
            'status': 'success',
            'analytics': analytics
        }), 200
        
    except Exception as e:
        import traceback
        print(f"Analytics endpoint error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Failed to load analytics: {str(e)}'}), 500


# Bulk operations
@borrow_bp.route('/admin/borrow/bulk-approve', methods=['POST'])
@jwt_required()
def bulk_approve():
    """Bulk approve multiple requests (admin only)"""
    try:
        admin_id = get_jwt_identity()

        # Check admin
        admin = User.query.get(admin_id)
        if not admin or admin.user_type != 'Admin':
            return jsonify({'error': 'Admin access required'}), 403

        data = request.get_json()
        request_ids = data.get('request_ids', [])

        if not request_ids:
            return jsonify({'error': 'No request IDs provided'}), 400

        pickup_days = data.get('pickup_days', 3)
        approved_count = 0

        for request_id in request_ids:
            borrow_request = BorrowRequest.query.get(request_id)
            if borrow_request and borrow_request.status == 'pending':
                borrow_request.status = 'approved'
                borrow_request.processed_by = admin_id
                borrow_request.processed_date = datetime.utcnow()
                borrow_request.pickup_deadline = datetime.utcnow() + timedelta(days=pickup_days)

                add_history(borrow_request.id, 'approved', admin_id, 'Bulk approved')

                create_notification(
                    borrow_request.user_id,
                    'Request Approved! 📚',
                    f'Your request for "{borrow_request.book.title}" has been approved!',
                    'borrow_approved'
                )

                approved_count += 1

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'{approved_count} requests approved',
            'approved_count': approved_count
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@borrow_bp.route('/admin/borrow/bulk-deny', methods=['POST'])
@jwt_required()
def bulk_deny():
    """Bulk deny multiple requests (admin only)"""
    try:
        admin_id = get_jwt_identity()

        # Check admin
        admin = User.query.get(admin_id)
        if not admin or admin.user_type != 'Admin':
            return jsonify({'error': 'Admin access required'}), 403

        data = request.get_json()
        request_ids = data.get('request_ids', [])
        reason = data.get('reason', 'Request denied by administrator')

        if not request_ids:
            return jsonify({'error': 'No request IDs provided'}), 400

        denied_count = 0

        for request_id in request_ids:
            borrow_request = BorrowRequest.query.get(request_id)
            if borrow_request and borrow_request.status == 'pending':
                borrow_request.status = 'denied'
                borrow_request.processed_by = admin_id
                borrow_request.processed_date = datetime.utcnow()
                borrow_request.admin_notes = reason

                add_history(borrow_request.id, 'denied', admin_id, reason)

                create_notification(
                    borrow_request.user_id,
                    'Request Denied ❌',
                    f'Your request for "{borrow_request.book.title}" has been denied. Reason: {reason}',
                    'borrow_denied'
                )

                denied_count += 1

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'{denied_count} requests denied',
            'denied_count': denied_count
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ====================== RESERVATION ENDPOINTS ======================

@borrow_bp.route('/borrow/reserve', methods=['POST'])
@jwt_required()
def create_reservation():
    """Create a book reservation request"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        book_id = data.get('book_id')
        notes = data.get('notes', '')
        
        if not book_id:
            return jsonify({'error': 'Book ID is required'}), 400
        
        # Debug: print the book_id
        print(f"[DEBUG] Reserve request - book_id: {book_id}, user_id: {user_id}")
        
        # Check if book exists
        book = Book.query.get(book_id)
        if not book:
            # Debug: list all books
            all_books = Book.query.all()
            print(f"[DEBUG] Book not found. Available books: {[(b.id, b.title) for b in all_books]}")
            return jsonify({'error': 'Book not found'}), 404
        
        # Check if user already has active reservation for this book
        existing = ReserveRequest.query.filter_by(
            user_id=user_id,
            book_id=book_id,
            status='active'
        ).first()
        
        if existing:
            return jsonify({'error': 'You already have an active reservation for this book'}), 400
        
        # Check if user already has an active borrow for this book
        active_borrow = BorrowRequest.query.filter_by(
            user_id=user_id,
            book_id=book_id,
            status='picked_up'
        ).first()
        
        if active_borrow:
            return jsonify({'error': 'You already have this book borrowed'}), 400
        
        # Create reservation
        reservation = ReserveRequest(
            user_id=user_id,
            book_id=book_id,
            notify_when_available=True,
            status='active',
            expiry_date=datetime.utcnow() + timedelta(days=7)
        )
        
        db.session.add(reservation)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Reservation created successfully',
            'reservation': reserve_request_schema.dump(reservation)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@borrow_bp.route('/borrow/my-reservations', methods=['GET'])
@jwt_required()
def get_my_reservations():
    """Get current user's reservations"""
    try:
        user_id = get_jwt_identity()
        status = request.args.get('status')
        
        query = ReserveRequest.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        # When no status filter, show all reservations (for "All" button)
        
        reservations = query.order_by(ReserveRequest.reserve_date.desc()).all()
        
        return jsonify({
            'status': 'success',
            'reservations': reserve_requests_schema.dump(reservations)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@borrow_bp.route('/borrow/reservations/<int:reservation_id>', methods=['GET'])
@jwt_required()
def get_reservation(reservation_id):
    """Get a specific reservation"""
    try:
        user_id = get_jwt_identity()
        
        reservation = ReserveRequest.query.get(reservation_id)
        if not reservation:
            return jsonify({'error': 'Reservation not found'}), 404
        
        # User can only view their own reservations unless admin
        user = User.query.get(user_id)
        if reservation.user_id != user_id and user.user_type != 'Admin':
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'status': 'success',
            'reservation': reserve_request_schema.dump(reservation)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@borrow_bp.route('/borrow/reservations/<int:reservation_id>', methods=['DELETE'])
@jwt_required()
def cancel_reservation(reservation_id):
    """Cancel a reservation (user can cancel their own)"""
    try:
        user_id = get_jwt_identity()
        
        reservation = ReserveRequest.query.get(reservation_id)
        if not reservation:
            return jsonify({'error': 'Reservation not found'}), 404
        
        # Check ownership or admin
        user = User.query.get(user_id)
        if reservation.user_id != user_id and user.user_type != 'Admin':
            return jsonify({'error': 'Access denied'}), 403
        
        if reservation.status not in ('active', 'pending', 'pending_ill'):
            return jsonify({'error': 'Only active or pending reservations can be cancelled'}), 400
        
        reservation.status = 'cancelled'
        reservation.cancelled_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Reservation cancelled successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ====================== ADMIN RESERVATION ENDPOINTS ======================

@borrow_bp.route('/admin/borrow/reservations', methods=['GET'])
@jwt_required()
def admin_get_all_reservations():
    """Get all reservations (admin only)"""
    try:
        admin_id = get_jwt_identity()
        
        # Check admin
        admin = User.query.get(admin_id)
        if not admin or admin.user_type != 'Admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = ReserveRequest.query
        
        if status:
            query = query.filter_by(status=status)
        
        # Order by reserve date, active first
        reservations = query.order_by(
            ReserveRequest.status == 'active',
            ReserveRequest.reserve_date.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'status': 'success',
            'reservations': reserve_requests_schema.dump(reservations.items),
            'total': reservations.total,
            'pages': reservations.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@borrow_bp.route('/admin/borrow/reservations/<int:reservation_id>/fulfill', methods=['POST'])
@jwt_required()
def fulfill_reservation(reservation_id):
    """Mark reservation as fulfilled (admin only)"""
    try:
        admin_id = get_jwt_identity()
        
        # Check admin
        admin = User.query.get(admin_id)
        if not admin or admin.user_type != 'Admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        reservation = ReserveRequest.query.get(reservation_id)
        if not reservation:
            return jsonify({'error': 'Reservation not found'}), 404
        
        if reservation.status not in ('active', 'pending', 'pending_ill'):
            return jsonify({'error': 'Only active or pending reservations can be fulfilled'}), 400
        
        # Get book title (works for both local and OpenLibrary reservations)
        if reservation.book:
            book_title = reservation.book.title
        elif reservation.notes:
            try:
                notes_data = json.loads(reservation.notes)
                book_title = notes_data.get('title', 'Unknown Book')
            except:
                book_title = 'Unknown Book'
        else:
            book_title = 'Unknown Book'
        
        # Update reservation
        reservation.status = 'fulfilled'
        reservation.fulfilled_date = datetime.utcnow()
        
        db.session.commit()
        
        # Notify user
        create_notification(
            reservation.user_id,
            'Reservation Fulfilled 📚',
            f'Your reservation for "{book_title}" is ready for pickup!',
            'reservation_fulfilled'
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Reservation fulfilled successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@borrow_bp.route('/admin/borrow/reservations/<int:reservation_id>/cancel', methods=['POST'])
@jwt_required()
def admin_cancel_reservation(reservation_id):
    """Cancel a reservation (admin only)"""
    try:
        admin_id = get_jwt_identity()
        data = request.get_json() or {}
        reason = data.get('reason', 'Reservation cancelled by administrator')
        
        # Check admin
        admin = User.query.get(admin_id)
        if not admin or admin.user_type != 'Admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        reservation = ReserveRequest.query.get(reservation_id)
        if not reservation:
            return jsonify({'error': 'Reservation not found'}), 404
        
        if reservation.status == 'cancelled':
            return jsonify({'error': 'Reservation is already cancelled'}), 400
        
        # Update reservation
        reservation.status = 'cancelled'
        reservation.cancelled_date = datetime.utcnow()
        
        db.session.commit()
        
        # Get book title (works for both local and external books)
        if reservation.book:
            book_title = reservation.book.title
        elif reservation.notes and "external):" in reservation.notes:
            # Parse title from notes for external books
            try:
                content = reservation.notes.split("external):", 1)[1].strip()
                if " by " in content:
                    book_title = content.rsplit(" by ", 1)[0].strip()
                else:
                    book_title = content
            except:
                book_title = 'Unknown Book'
        else:
            book_title = 'Unknown Book'
        
        # Notify user
        create_notification(
            reservation.user_id,
            'Reservation Cancelled ❌',
            f'Your reservation for "{book_title}" has been cancelled. Reason: {reason}',
            'reservation_cancelled'
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Reservation cancelled successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@borrow_bp.route('/admin/borrow/reservations/<int:reservation_id>/expire', methods=['POST'])
@jwt_required()
def expire_reservation(reservation_id):
    """Manually expire a pending reservation (admin only)"""
    try:
        admin_id = get_jwt_identity()
        
        # Check admin
        admin = User.query.get(admin_id)
        if not admin or admin.user_type != 'Admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        reservation = ReserveRequest.query.get(reservation_id)
        if not reservation:
            return jsonify({'error': 'Reservation not found'}), 404
        
        if reservation.status not in ('active', 'pending'):
            return jsonify({'error': 'Only active or pending reservations can be expired'}), 400
        
        # Update reservation
        reservation.status = 'expired'
        reservation.cancelled_date = datetime.utcnow()
        
        db.session.commit()
        
        # Notify user
        create_notification(
            reservation.user_id,
            'Reservation Expired ⏰',
            f'Your reservation for "{reservation.book.title}" has expired.',
            'reservation_expired'
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Reservation expired successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@borrow_bp.route('/admin/borrow/reservations/analytics', methods=['GET'])
@jwt_required()
def reservation_analytics():
    """Get reservation analytics (admin only)"""
    try:
        admin_id = get_jwt_identity()
        
        # Check admin
        admin = User.query.get(admin_id)
        if not admin or admin.user_type != 'Admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get date range
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Status counts
        status_counts = db.session.query(
            ReserveRequest.status,
            db.func.count(ReserveRequest.id)
        ).filter(
            ReserveRequest.reserve_date >= start_date
        ).group_by(ReserveRequest.status).all()
        
        # Daily reservations
        daily_reservations = db.session.query(
            db.func.date(ReserveRequest.reserve_date),
            db.func.count(ReserveRequest.id)
        ).filter(
            ReserveRequest.reserve_date >= start_date
        ).group_by(db.func.date(ReserveRequest.reserve_date)).all()
        
        # Most reserved books
        top_books = db.session.query(
            Book.id,
            Book.title,
            db.func.count(ReserveRequest.id).label('count')
        ).join(ReserveRequest).filter(
            ReserveRequest.reserve_date >= start_date
        ).group_by(Book.id, Book.title).order_by(db.desc('count')).limit(10).all()
        
        # Average fulfillment time (active to fulfilled)
        fulfilled = ReserveRequest.query.filter(
            ReserveRequest.reserve_date >= start_date,
            ReserveRequest.status == 'fulfilled',
            ReserveRequest.fulfilled_date.isnot(None)
        ).all()
        
        if fulfilled:
            total_hours = sum(
                (r.fulfilled_date - r.reserve_date).total_seconds() / 3600
                for r in fulfilled
            )
            avg_fulfillment_hours = total_hours / len(fulfilled)
        else:
            avg_fulfillment_hours = 0
        
        # Expiry rate
        expired_count = ReserveRequest.query.filter(
            ReserveRequest.reserve_date >= start_date,
            ReserveRequest.status == 'expired'
        ).count()
        
        total_active = sum(count for status, count in status_counts if status in ['active', 'fulfilled'])
        expiry_rate = (expired_count / (total_active + expired_count) * 100) if (total_active + expired_count) > 0 else 0
        
        return jsonify({
            'status': 'success',
            'analytics': {
                'total_reservations': sum(count for status, count in status_counts),
                'reservations_by_status': {status: count for status, count in status_counts},
                'reservations_over_time': [
                    {'date': str(date), 'count': count}
                    for date, count in daily_reservations
                ],
                'most_reserved_books': [
                    {'id': id, 'title': title, 'count': count}
                    for id, title, count in top_books
                ],
                'average_fulfillment_hours': round(avg_fulfillment_hours, 2),
                'expiry_rate': round(expiry_rate, 2)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
