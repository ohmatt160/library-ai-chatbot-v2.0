"""
Metrics and evaluation system for Intelligent Library Chat Assistant
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import statistics
from collections import defaultdict
import redis
import os


class UserSatisfactionQuestionnaire:
    """
    User satisfaction questionnaire system

    Provides standardized questionnaires to collect user feedback
    """

    # Default questionnaire questions
    DEFAULT_QUESTIONS = [
        {
            'id': 'q1',
            'question': 'How satisfied are you with the chatbot\'s response?',
            'type': 'likert',
            'scale': 5,
            'options': ['Very Dissatisfied', 'Dissatisfied', 'Neutral', 'Satisfied', 'Very Satisfied']
        },
        {
            'id': 'q2',
            'question': 'Was the information provided accurate?',
            'type': 'likert',
            'scale': 5,
            'options': ['Very Inaccurate', 'Inaccurate', 'Neutral', 'Accurate', 'Very Accurate']
        },
        {
            'id': 'q3',
            'question': 'How easy was it to get the help you needed?',
            'type': 'likert',
            'scale': 5,
            'options': ['Very Difficult', 'Difficult', 'Neutral', 'Easy', 'Very Easy']
        },
        {
            'id': 'q4',
            'question': 'How would you rate the response time?',
            'type': 'likert',
            'scale': 5,
            'options': ['Very Slow', 'Slow', 'Neutral', 'Fast', 'Very Fast']
        },
        {
            'id': 'q5',
            'question': 'Would you use this chatbot again?',
            'type': 'boolean',
            'options': ['Yes', 'No']
        },
        {
            'id': 'q6',
            'question': 'What could we improve? (Optional)',
            'type': 'text',
            'placeholder': 'Enter your suggestions...'
        }
    ]

    def __init__(self):
        self.questions = self.DEFAULT_QUESTIONS.copy()
        self.responses = []

    def get_questionnaire(self) -> List[Dict]:
        """Get the current questionnaire"""
        return self.questions

    def add_question(self, question: Dict):
        """Add a new question to the questionnaire"""
        self.questions.append(question)

    def remove_question(self, question_id: str):
        """Remove a question from the questionnaire"""
        self.questions = [q for q in self.questions if q.get('id') != question_id]

    def record_response(self, session_id: str, user_id: str, answers: Dict, overall_rating: int = None) -> Dict:
        """
        Record a user's questionnaire response

        Args:
            session_id: The conversation session ID
            user_id: The user ID
            answers: Dictionary of question_id -> answer
            overall_rating: Optional overall rating (1-5)

        Returns:
            The recorded response
        """
        response = {
            'session_id': session_id,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'answers': answers,
            'overall_rating': overall_rating,
            'satisfaction_score': self._calculate_satisfaction_score(answers)
        }

        self.responses.append(response)
        return response

    def _calculate_satisfaction_score(self, answers: Dict) -> float:
        """Calculate overall satisfaction score from answers"""
        likert_answers = []

        for q in self.questions:
            if q['type'] == 'likert' and q['id'] in answers:
                # Convert answer to numeric score (1-5)
                answer = answers[q['id']]
                if isinstance(answer, int):
                    likert_answers.append(answer)
                elif isinstance(answer, str) and 'options' in q:
                    try:
                        score = q['options'].index(answer) + 1
                        likert_answers.append(score)
                    except ValueError:
                        pass

        if likert_answers:
            return statistics.mean(likert_answers)
        return 0.0

    def get_statistics(self, start_date: datetime = None, end_date: datetime = None) -> Dict:
        """
        Get satisfaction statistics

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with statistics
        """
        # Filter responses by date if needed
        filtered_responses = self.responses
        if start_date or end_date:
            filtered_responses = []
            for resp in self.responses:
                resp_date = datetime.fromisoformat(resp['timestamp'])
                if start_date and resp_date < start_date:
                    continue
                if end_date and resp_date > end_date:
                    continue
                filtered_responses.append(resp)

        if not filtered_responses:
            return {
                'total_responses': 0,
                'message': 'No responses recorded'
            }

        # Calculate overall statistics
        satisfaction_scores = [r['satisfaction_score'] for r in filtered_responses if r['satisfaction_score'] > 0]
        overall_ratings = [r['overall_rating'] for r in filtered_responses if r['overall_rating'] is not None]

        # Per-question statistics
        question_stats = {}
        for q in self.questions:
            if q['type'] == 'likert':
                answers = [r['answers'].get(q['id']) for r in filtered_responses if q['id'] in r['answers']]
                numeric_answers = []
                for ans in answers:
                    if isinstance(ans, int):
                        numeric_answers.append(ans)
                    elif isinstance(ans, str) and 'options' in q:
                        try:
                            numeric_answers.append(q['options'].index(ans) + 1)
                        except ValueError:
                            pass

                if numeric_answers:
                    question_stats[q['id']] = {
                        'question': q['question'],
                        'mean': statistics.mean(numeric_answers),
                        'median': statistics.median(numeric_answers),
                        'std_dev': statistics.stdev(numeric_answers) if len(numeric_answers) > 1 else 0,
                        'min': min(numeric_answers),
                        'max': max(numeric_answers),
                        'total_responses': len(numeric_answers)
                    }

        # NPS-like metric (would use again)
        would_use_again_count = sum(
            1 for r in filtered_responses
            if r['answers'].get('q5') in ['Yes', 'yes', True]
        )
        nps_score = (would_use_again_count / len(filtered_responses) * 100) if filtered_responses else 0

        return {
            'total_responses': len(filtered_responses),
            'overall_satisfaction': {
                'mean': statistics.mean(satisfaction_scores) if satisfaction_scores else 0,
                'median': statistics.median(satisfaction_scores) if satisfaction_scores else 0,
                'std_dev': statistics.stdev(satisfaction_scores) if len(satisfaction_scores) > 1 else 0
            },
            'overall_rating': {
                'mean': statistics.mean(overall_ratings) if overall_ratings else 0,
                'distribution': dict(Counter(overall_ratings)) if overall_ratings else {}
            },
            'question_statistics': question_stats,
            'nps_score': nps_score,
            'would_use_again': f"{would_use_again_count}/{len(filtered_responses)}"
        }

    def export_responses(self, format: str = 'json') -> str:
        """Export all responses"""
        if format == 'json':
            return json.dumps(self.responses, indent=2)
        return str(self.responses)


from collections import Counter

class MetricsTracker:
    """Tracks real-time metrics for the chatbot"""

    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                password=os.getenv('REDIS_PASSWORD', None),
                decode_responses=True
            )
            self.redis_client.ping()
        except Exception:
            print("⚠️ Redis not available for metrics, using in-memory storage")
            class MockRedis:
                def __init__(self): self.data = {}
                def get(self, key): return self.data.get(key)
                def set(self, key, val): self.data[key] = val
                def exists(self, key): return key in self.data
                def incr(self, key):
                    val = int(self.data.get(key, 0)) + 1
                    self.data[key] = val
                    return val
                def hset(self, key, mapping=None, **kwargs):
                    if key not in self.data: self.data[key] = {}
                    if mapping: self.data[key].update(mapping)
                    self.data[key].update(kwargs)
                def expire(self, key, time): pass
            self.redis_client = MockRedis()

        # Initialize counters
        self._init_counters()

    def _init_counters(self):
        """Initialize Redis counters"""
        counters = [
            'total_conversations',
            'total_messages',
            'total_users',
            'successful_responses',
            'failed_responses',
            'average_response_time'
        ]

        for counter in counters:
            if not self.redis_client.exists(counter):
                self.redis_client.set(counter, 0)

    def record_interaction(self, user_id: str, session_id: str, message: str,
                          response: str, response_time: float,
                          confidence: float, method: str):
        """Record a single interaction"""

        # Increment counters
        self.redis_client.incr('total_messages')

        # Store interaction details
        interaction_key = f"interaction:{user_id}:{session_id}:{int(datetime.now().timestamp())}"
        interaction_data = {
            'user_id': user_id,
            'session_id': session_id,
            'message': message,
            'response': response,
            'response_time': response_time,
            'confidence': confidence,
            'method': method,
            'timestamp': datetime.now().isoformat()
        }

        self.redis_client.hset(interaction_key, mapping=interaction_data)
        self.redis_client.expire(interaction_key, 604800)  # Keep for 7 days

        # Update response time average
        current_avg = float(self.redis_client.get('average_response_time') or 0)
        total_messages = int(self.redis_client.get('total_messages') or 1)
        new_avg = ((current_avg * (total_messages - 1)) + response_time) / total_messages
        self.redis_client.set('average_response_time', new_avg)

        # Track success
        if confidence > 0.7:
            self.redis_client.incr('successful_responses')
        else:
            self.redis_client.incr('failed_responses')

    def record_session_start(self, user_id: str, session_id: str):
        """Record a new conversation session"""
        self.redis_client.incr('total_conversations')

        session_key = f"session:{session_id}"
        session_data = {
            'user_id': user_id,
            'start_time': datetime.now().isoformat(),
            'message_count': 0
        }

        self.redis_client.hset(session_key, mapping=session_data)

    def record_session_end(self, session_id: str, feedback_score: Optional[int] = None):
        """Record session end with optional feedback"""
        session_key = f"session:{session_id}"

        if self.redis_client.exists(session_key):
            self.redis_client.hset(session_key, 'end_time', datetime.now().isoformat())
            if feedback_score:
                self.redis_client.hset(session_key, 'feedback_score', feedback_score)

    def get_all_metrics(self) -> Dict:
        """Get comprehensive system metrics"""
        return {
            'total_conversations': int(self.redis_client.get('total_conversations') or 0),
            'total_messages': int(self.redis_client.get('total_messages') or 0),
            'successful_responses': int(self.redis_client.get('successful_responses') or 0),
            'failed_responses': int(self.redis_client.get('failed_responses') or 0),
            'average_response_time': float(self.redis_client.get('average_response_time') or 0),
            'success_rate': self._calculate_success_rate(),
            'intent_distribution': self._get_intent_distribution(),
            'common_queries': self._get_common_queries(),
            'user_satisfaction': self._get_user_satisfaction()
        }

    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        successful = int(self.redis_client.get('successful_responses') or 0)
        total = int(self.redis_client.get('total_messages') or 1)
        return (successful / total) * 100

    def _get_intent_distribution(self) -> Dict:
        """Get distribution of detected intents"""
        # This would query your database for intent statistics
        # For now, return a placeholder
        return {
            'book_search': 35,
            'library_hours': 25,
            'borrowing_info': 20,
            'policy_query': 15,
            'other': 5
        }

    def _get_common_queries(self) -> List[Dict]:
        """Get most common user queries"""
        # This would query your database for frequent queries
        return [
            {'query': 'What are the library hours?', 'count': 150},
            {'query': 'How do I borrow a book?', 'count': 120},
            {'query': 'Find computer science books', 'count': 95},
            {'query': 'Where is the quiet study area?', 'count': 80},
            {'query': 'How do I renew a book?', 'count': 75}
        ]

    def _get_user_satisfaction(self) -> Dict:
        """Get user satisfaction metrics"""
        # This would query feedback data
        return {
            'thumbs_up': 85,
            'thumbs_down': 10,
            'neutral': 5,
            'average_rating': 4.2
        }


class EvaluationSystem:
    """Comprehensive evaluation system for the chatbot"""

    def __init__(self):
        self.metrics = {
            'response_accuracy': [],
            'response_times': [],
            'task_completion': {},
            'user_satisfaction': [],
            'conversation_lengths': [],
            'fallback_rates': []
        }

        # Initialize database connection for storing evaluations
        self.evaluations = []

        # Store confusion matrix for F1 calculation
        self.intent_confusion_matrix = defaultdict(lambda: defaultdict(int))
        self.true_labels = []
        self.predicted_labels = []

    def calculate_f1_score(self, true_labels: List[str], predicted_labels: List[str], average: str = 'weighted') -> Dict[str, float]:
        """
        Calculate F1 score for intent classification

        Args:
            true_labels: Actual intent labels
            predicted_labels: Predicted intent labels
            average: 'weighted', 'macro', or 'micro'

        Returns:
            Dictionary with precision, recall, f1 score
        """
        from collections import Counter

        self.true_labels = true_labels
        self.predicted_labels = predicted_labels

        # Build confusion matrix
        for true, pred in zip(true_labels, predicted_labels):
            self.intent_confusion_matrix[true][pred] += 1

        # Get all unique labels
        all_labels = set(true_labels) | set(predicted_labels)

        # Calculate per-class metrics
        per_class_metrics = {}
        for label in all_labels:
            true_positive = sum(1 for t, p in zip(true_labels, predicted_labels) if t == label and p == label)
            false_positive = sum(1 for t, p in zip(true_labels, predicted_labels) if t != label and p == label)
            false_negative = sum(1 for t, p in zip(true_labels, predicted_labels) if t == label and p != label)

            precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
            recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

            per_class_metrics[label] = {
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'support': true_labels.count(label)
            }

        # Calculate aggregate F1 scores
        if average == 'macro':
            avg_precision = sum(m['precision'] for m in per_class_metrics.values()) / len(per_class_metrics)
            avg_recall = sum(m['recall'] for m in per_class_metrics.values()) / len(per_class_metrics)
            avg_f1 = sum(m['f1_score'] for m in per_class_metrics.values()) / len(per_class_metrics)
        elif average == 'micro':
            total_tp = sum(1 for t, p in zip(true_labels, predicted_labels) if t == p)
            total_fp = sum(1 for t, p in zip(true_labels, predicted_labels) if t != p and p == true_labels[predicted_labels.index(p)])
            total_fn = sum(1 for t, p in zip(true_labels, predicted_labels) if t != p and p != true_labels[predicted_labels.index(p)])
            avg_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
            avg_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
            avg_f1 = 2 * (avg_precision * avg_recall) / (avg_precision + avg_recall) if (avg_precision + avg_recall) > 0 else 0
        else:  # weighted
            total_support = sum(m['support'] for m in per_class_metrics.values())
            avg_precision = sum(m['precision'] * m['support'] for m in per_class_metrics.values()) / total_support
            avg_recall = sum(m['recall'] * m['support'] for m in per_class_metrics.values()) / total_support
            avg_f1 = sum(m['f1_score'] * m['support'] for m in per_class_metrics.values()) / total_support

        return {
            'precision': avg_precision,
            'recall': avg_recall,
            'f1_score': avg_f1,
            'average_type': average,
            'per_class': per_class_metrics,
            'total_samples': len(true_labels)
        }

    def record_intent_prediction(self, true_intent: str, predicted_intent: str, confidence: float):
        """Record intent prediction for F1 calculation"""
        self.true_labels.append(true_intent)
        self.predicted_labels.append(predicted_intent)
        self.intent_confusion_matrix[true_intent][predicted_intent] += 1

    def get_confusion_matrix(self) -> Dict:
        """Get the intent confusion matrix"""
        return dict(self.intent_confusion_matrix)

    def get_classification_report(self) -> Dict:
        """Get detailed classification report"""
        if not self.true_labels:
            return {'error': 'No predictions recorded'}

        return self.calculate_f1_score(self.true_labels, self.predicted_labels, 'weighted')

    def evaluate_conversation(self, conversation_id: str,
                              user_feedback: Dict,
                              system_logs: Dict) -> Dict:
        """Comprehensive evaluation of conversation"""

        evaluation = {
            'conversation_id': conversation_id,
            'timestamp': datetime.now().isoformat(),
            'metrics': {}
        }

        # Calculate accuracy based on feedback
        accuracy = self._calculate_accuracy(user_feedback, system_logs)
        evaluation['metrics']['accuracy'] = accuracy

        # Calculate response time metrics
        response_times = system_logs.get('response_times', [])
        if response_times:
            evaluation['metrics']['avg_response_time'] = sum(response_times) / len(response_times)
            evaluation['metrics']['max_response_time'] = max(response_times)
            evaluation['metrics']['min_response_time'] = min(response_times)
            evaluation['metrics']['response_time_std'] = statistics.stdev(response_times) if len(response_times) > 1 else 0

        # Calculate task completion rate
        completed_tasks = self._identify_completed_tasks(system_logs)
        total_tasks = len(system_logs.get('user_requests', []))
        evaluation['metrics']['task_completion_rate'] = len(completed_tasks) / total_tasks if total_tasks > 0 else 0
        evaluation['metrics']['total_tasks'] = total_tasks
        evaluation['metrics']['completed_tasks'] = len(completed_tasks)

        # Calculate user satisfaction
        satisfaction = self._calculate_satisfaction(user_feedback)
        evaluation['metrics']['user_satisfaction'] = satisfaction

        # Calculate system reliability
        evaluation['metrics']['system_reliability'] = self._calculate_reliability(system_logs)

        # Calculate fallback rate
        fallback_rate = self._calculate_fallback_rate(system_logs)
        evaluation['metrics']['fallback_rate'] = fallback_rate

        # Calculate conversation metrics
        evaluation['metrics']['conversation_length'] = system_logs.get('message_count', 0)
        evaluation['metrics']['turns'] = system_logs.get('turns', 0)

        # Store for aggregate reporting
        self._store_evaluation(evaluation)

        return evaluation

    def _calculate_accuracy(self, user_feedback: Dict, system_logs: Dict) -> float:
        """Calculate accuracy based on feedback and system logs"""

        # If explicit accuracy is provided in feedback
        if 'accuracy_rating' in user_feedback:
            return user_feedback['accuracy_rating']

        # Calculate based on feedback ratings
        ratings = user_feedback.get('ratings', [])
        if ratings:
            # Convert ratings to numerical scores
            rating_scores = {
                'thumbs_up': 1.0,
                'neutral': 0.5,
                'thumbs_down': 0.0
            }

            total_score = sum(rating_scores.get(rating, 0.5) for rating in ratings)
            return total_score / len(ratings)

        # Calculate based on confidence scores
        confidence_scores = system_logs.get('confidence_scores', [])
        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)

        return 0.7  # Default

    def _identify_completed_tasks(self, system_logs: Dict) -> List[str]:
        """Identify completed tasks from conversation logs"""
        completed_tasks = []
        user_requests = system_logs.get('user_requests', [])
        system_responses = system_logs.get('system_responses', [])

        # Define task completion indicators
        task_indicators = {
            'book_search': ['found', 'available', 'located', 'search results'],
            'information_query': ['answer is', 'information', 'details', 'explanation'],
            'procedural_help': ['steps', 'process', 'procedure', 'how to'],
            'policy_clarification': ['policy states', 'according to', 'rules', 'guidelines']
        }

        for i, (request, response) in enumerate(zip(user_requests, system_responses)):
            if i < len(system_responses):
                response_lower = response.lower()

                # Check if response indicates task completion
                for task_type, indicators in task_indicators.items():
                    if any(indicator in response_lower for indicator in indicators):
                        completed_tasks.append(f"{task_type}_{i}")

        return completed_tasks

    def _calculate_satisfaction(self, user_feedback: Dict) -> float:
        """Calculate user satisfaction score"""

        # Direct satisfaction score
        if 'satisfaction_score' in user_feedback:
            return user_feedback['satisfaction_score']

        # Calculate from ratings
        ratings = user_feedback.get('ratings', [])
        if ratings:
            rating_values = {
                'thumbs_up': 5.0,
                'neutral': 3.0,
                'thumbs_down': 1.0
            }

            total = sum(rating_values.get(rating, 3.0) for rating in ratings)
            return total / len(ratings)

        # Calculate from feedback comments (simple sentiment analysis)
        comments = user_feedback.get('comments', [])
        if comments:
            # Simple positive word detection
            positive_words = ['good', 'great', 'excellent', 'helpful', 'thanks', 'thank you', 'useful']
            negative_words = ['bad', 'poor', 'terrible', 'unhelpful', 'useless', 'waste']

            positive_count = sum(1 for comment in comments
                               if any(word in comment.lower() for word in positive_words))
            negative_count = sum(1 for comment in comments
                               if any(word in comment.lower() for word in negative_words))

            total_comments = len(comments)
            if total_comments > 0:
                base_score = 3.0  # Neutral
                positive_boost = (positive_count / total_comments) * 2.0
                negative_penalty = (negative_count / total_comments) * 2.0
                return min(5.0, max(1.0, base_score + positive_boost - negative_penalty))

        return 3.0  # Default neutral satisfaction

    def _calculate_reliability(self, system_logs: Dict) -> float:
        """Calculate system reliability score"""

        errors = system_logs.get('errors', 0)
        total_requests = system_logs.get('total_requests', 1)

        error_rate = errors / total_requests
        reliability = 1.0 - error_rate

        # Consider response time consistency
        response_times = system_logs.get('response_times', [])
        if len(response_times) > 1:
            time_std = statistics.stdev(response_times)
            max_allowed_time = system_logs.get('max_response_time', 4.0)

            # Penalize high variance
            time_consistency = 1.0 - min(1.0, time_std / max_allowed_time)
            reliability = (reliability + time_consistency) / 2

        return max(0.0, min(1.0, reliability))

    def _calculate_fallback_rate(self, system_logs: Dict) -> float:
        """Calculate fallback to clarification rate"""
        fallback_count = system_logs.get('fallback_count', 0)
        total_requests = system_logs.get('total_requests', 1)

        return fallback_count / total_requests

    def _store_evaluation(self, evaluation: Dict):
        """Store evaluation in memory and optionally database"""
        self.evaluations.append(evaluation)

        # Keep only last 1000 evaluations
        if len(self.evaluations) > 1000:
            self.evaluations = self.evaluations[-1000:]

        # Also update metrics
        metrics = evaluation['metrics']
        self.metrics['response_accuracy'].append(metrics.get('accuracy', 0))
        self.metrics['response_times'].append(metrics.get('avg_response_time', 0))
        self.metrics['user_satisfaction'].append(metrics.get('user_satisfaction', 0))
        self.metrics['conversation_lengths'].append(metrics.get('conversation_length', 0))
        self.metrics['fallback_rates'].append(metrics.get('fallback_rate', 0))

    def _get_evaluations_in_period(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get evaluations within a date period"""
        return [
            eval for eval in self.evaluations
            if start_date <= datetime.fromisoformat(eval['timestamp']) <= end_date
        ]

    def _average_metric(self, evaluations: List[Dict], metric_name: str) -> float:
        """Calculate average of a metric across evaluations"""
        values = []
        for eval in evaluations:
            metric_value = eval['metrics'].get(metric_name)
            if metric_value is not None:
                values.append(metric_value)

        return sum(values) / len(values) if values else 0.0

    def _calculate_success_rate(self, evaluations: List[Dict]) -> float:
        """Calculate success rate from evaluations"""
        if not evaluations:
            return 0.0

        successful = sum(1 for eval in evaluations
                        if eval['metrics'].get('task_completion_rate', 0) > 0.7)

        return successful / len(evaluations)

    def _breakdown_by_intent(self, evaluations: List[Dict]) -> Dict:
        """Break down metrics by intent type"""
        breakdown = defaultdict(lambda: {
            'count': 0,
            'avg_accuracy': 0,
            'avg_response_time': 0,
            'avg_satisfaction': 0
        })

        # This would normally query database for intent data
        # For now, provide sample breakdown
        sample_intents = ['book_search', 'library_hours', 'borrowing_info', 'policy_query']

        for intent in sample_intents:
            breakdown[intent] = {
                'count': len([e for e in evaluations if e.get('intent') == intent]),
                'avg_accuracy': 0.85,
                'avg_response_time': 1.2,
                'avg_satisfaction': 4.0,
                'success_rate': 0.9
            }

        return dict(breakdown)

    def _generate_recommendations(self, summary: Dict, detailed_metrics: Dict) -> List[str]:
        """Generate improvement recommendations based on metrics"""
        recommendations = []

        # Check response time
        avg_response_time = summary.get('average_response_time', 0)
        if avg_response_time > 3.0:
            recommendations.append(
                f"Response time ({avg_response_time:.2f}s) is above target (3s). "
                "Consider optimizing NLP models or database queries."
            )

        # Check accuracy
        avg_accuracy = summary.get('average_accuracy', 0)
        if avg_accuracy < 0.8:
            recommendations.append(
                f"Accuracy ({avg_accuracy:.1%}) is below target (80%). "
                "Consider expanding the knowledge base or improving intent recognition."
            )

        # Check satisfaction
        avg_satisfaction = summary.get('average_satisfaction', 0)
        if avg_satisfaction < 4.0:
            recommendations.append(
                f"User satisfaction ({avg_satisfaction:.1f}/5) is below target (4.0). "
                "Consider improving response quality and adding more conversational features."
            )

        # Check success rate
        success_rate = summary.get('success_rate', 0)
        if success_rate < 0.8:
            recommendations.append(
                f"Task success rate ({success_rate:.1%}) is below target (80%). "
                "Consider enhancing fallback mechanisms and clarification prompts."
            )

        # Intent-specific recommendations
        for intent, metrics in detailed_metrics.items():
            if metrics.get('success_rate', 1.0) < 0.7:
                recommendations.append(
                    f"Intent '{intent}' has low success rate ({metrics['success_rate']:.1%}). "
                    "Consider improving handling for this intent."
                )

        if not recommendations:
            recommendations.append("System is performing well. Consider adding advanced features like voice input or personalized recommendations.")

        return recommendations

    def generate_report(self, start_date: datetime, end_date: datetime) -> Dict:
        """Generate comprehensive evaluation report"""

        report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'summary': {},
            'detailed_metrics': {},
            'recommendations': []
        }

        # Calculate aggregate metrics
        relevant_evaluations = self._get_evaluations_in_period(start_date, end_date)

        if relevant_evaluations:
            report['summary'] = {
                'total_conversations': len(relevant_evaluations),
                'average_accuracy': self._average_metric(relevant_evaluations, 'accuracy'),
                'average_response_time': self._average_metric(relevant_evaluations, 'avg_response_time'),
                'average_satisfaction': self._average_metric(relevant_evaluations, 'user_satisfaction'),
                'success_rate': self._calculate_success_rate(relevant_evaluations),
                'total_messages': sum(e['metrics'].get('conversation_length', 0) for e in relevant_evaluations),
                'avg_conversation_length': statistics.mean([e['metrics'].get('conversation_length', 0)
                                                          for e in relevant_evaluations]) if relevant_evaluations else 0
            }

            # Add detailed breakdown
            report['detailed_metrics'] = self._breakdown_by_intent(relevant_evaluations)

            # Generate recommendations
            report['recommendations'] = self._generate_recommendations(report['summary'],
                                                                       report['detailed_metrics'])
        else:
            report['summary'] = {
                'total_conversations': 0,
                'message': 'No data available for the selected period'
            }

        return report


# Helper functions for metrics calculation
def calculate_precision_recall_f1(true_positives: int, false_positives: int, false_negatives: int) -> Dict:
    """Calculate precision, recall, and F1 score"""

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score
    }


def calculate_response_time_percentiles(response_times: List[float]) -> Dict:
    """Calculate response time percentiles"""
    if not response_times:
        return {}

    sorted_times = sorted(response_times)

    return {
        'p50': sorted_times[int(len(sorted_times) * 0.5)],
        'p75': sorted_times[int(len(sorted_times) * 0.75)],
        'p90': sorted_times[int(len(sorted_times) * 0.90)],
        'p95': sorted_times[int(len(sorted_times) * 0.95)],
        'p99': sorted_times[int(len(sorted_times) * 0.99)]
    }


def calculate_user_engagement_metrics(sessions: List[Dict]) -> Dict:
    """Calculate user engagement metrics"""
    if not sessions:
        return {}

    session_lengths = [s.get('duration', 0) for s in sessions]
    messages_per_session = [s.get('message_count', 0) for s in sessions]

    return {
        'avg_session_length': statistics.mean(session_lengths),
        'median_session_length': statistics.median(session_lengths),
        'avg_messages_per_session': statistics.mean(messages_per_session),
        'retention_rate': len([s for s in sessions if s.get('returning_user', False)]) / len(sessions)
    }


class UserSatisfactionQuestionnaire:
    """User satisfaction questionnaire for collecting feedback"""
    
    def __init__(self):
        self.questions = [
            {
                'id': 'q1',
                'question': 'How easy was it to find the information you were looking for?',
                'type': 'likert',
                'scale': 5,
                'options': ['Very Difficult', 'Difficult', 'Neutral', 'Easy', 'Very Easy']
            },
            {
                'id': 'q2',
                'question': 'How satisfied are you with the accuracy of the information provided?',
                'type': 'likert',
                'scale': 5,
                'options': ['Very Dissatisfied', 'Dissatisfied', 'Neutral', 'Satisfied', 'Very Satisfied']
            },
            {
                'id': 'q3',
                'question': 'How would you rate the response time of the assistant?',
                'type': 'likert',
                'scale': 5,
                'options': ['Very Slow', 'Slow', 'Acceptable', 'Fast', 'Very Fast']
            },
            {
                'id': 'q4',
                'question': 'Was the assistant helpful in answering your question?',
                'type': 'boolean',
                'options': ['Yes', 'No']
            },
            {
                'id': 'q5',
                'question': 'Would you use this chatbot again in the future?',
                'type': 'boolean',
                'options': ['Yes', 'No']
            },
            {
                'id': 'q6',
                'question': 'Do you have any additional comments or suggestions?',
                'type': 'text',
                'placeholder': 'Enter your comments here...'
            }
        ]
    
    def get_questionnaire(self) -> List[Dict]:
        """Return the list of questionnaire questions"""
        return self.questions