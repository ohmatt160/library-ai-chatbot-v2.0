import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Progress } from '@/app/components/ui/progress';
import { toast } from 'sonner';
import { Star, ThumbsUp, ThumbsDown, Send, Loader2 } from 'lucide-react';

interface Question {
  id: string;
  question: string;
  type: string;
  scale?: number;
  options?: string[];
}

interface SatisfactionSurveyProps {
  sessionId: string;
  onComplete?: () => void;
}

export function SatisfactionSurvey({ sessionId, onComplete }: SatisfactionSurveyProps) {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, number | string>>({});
  const [overallRating, setOverallRating] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    fetchQuestions();
  }, []);

  const fetchQuestions = async () => {
    try {
      const response = await fetch('/api/questionnaire');
      const data = await response.json();
      if (data.status === 'success') {
        setQuestions(data.questionnaire);
      }
    } catch (error) {
      console.error('Error fetching questions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = (questionId: string, answer: number | string) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const response = await fetch('/api/questionnaire', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          answers,
          overall_rating: overallRating || undefined
        })
      });
      const data = await response.json();
      
      if (data.status === 'success') {
        setSubmitted(true);
        toast.success('Thank you! Your satisfaction score: ' + (data.satisfaction_score?.toFixed(1) || 'N/A') + '/5');
        onComplete?.();
      }
    } catch (error) {
      console.error('Error submitting survey:', error);
      toast.error('Failed to submit feedback');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardContent className="flex items-center justify-center p-6">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span className="ml-2">Loading survey...</span>
        </CardContent>
      </Card>
    );
  }

  if (submitted) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardContent className="flex flex-col items-center justify-center p-6">
          <ThumbsUp className="h-12 w-12 text-green-500 mb-4" />
          <h3 className="text-lg font-semibold">Thank you for your feedback!</h3>
          <p className="text-muted-foreground">Your input helps us improve our service.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>User Satisfaction Survey</CardTitle>
        <CardDescription>
          Please help us improve by answering a few questions
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {questions.map((question, index) => (
          <div key={question.id} className="space-y-3">
            <label className="font-medium">
              {index + 1}. {question.question}
            </label>
            
            {question.type === 'likert' && question.options && (
              <div className="flex flex-wrap gap-2">
                {question.options.map((option, optIndex) => (
                  <Button
                    key={optIndex}
                    variant={answers[question.id] === optIndex + 1 ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleAnswer(question.id, optIndex + 1)}
                    className="flex-1 min-w-[100px]"
                  >
                    {option}
                  </Button>
                ))}
              </div>
            )}
            
            {question.type === 'boolean' && question.options && (
              <div className="flex gap-4">
                {question.options.map((option, optIndex) => (
                  <Button
                    key={optIndex}
                    variant={answers[question.id] === option ? 'default' : 'outline'}
                    onClick={() => handleAnswer(question.id, option)}
                  >
                    {option === 'Yes' ? <ThumbsUp className="mr-2 h-4 w-4" /> : <ThumbsDown className="mr-2 h-4 w-4" />}
                    {option}
                  </Button>
                ))}
              </div>
            )}
            
            {question.type === 'text' && (
              <textarea
                className="w-full min-h-[80px] p-3 border rounded-md"
                placeholder={question.placeholder}
                value={answers[question.id] as string || ''}
                onChange={(e) => handleAnswer(question.id, e.target.value)}
              />
            )}
          </div>
        ))}

        {/* Overall Rating */}
        <div className="space-y-3 pt-4 border-t">
          <label className="font-medium">Overall Rating</label>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((rating) => (
              <button
                key={rating}
                onClick={() => setOverallRating(rating)}
                className="p-2 hover:scale-110 transition-transform"
              >
                <Star
                  className={`h-8 w-8 ${
                    rating <= overallRating
                      ? 'fill-yellow-400 text-yellow-400'
                      : 'text-gray-300'
                  }`}
                />
              </button>
            ))}
          </div>
          <p className="text-sm text-muted-foreground">
            {overallRating === 0 && 'Click to rate'}
            {overallRating === 1 && 'Very Poor'}
            {overallRating === 2 && 'Poor'}
            {overallRating === 3 && 'Average'}
            {overallRating === 4 && 'Good'}
            {overallRating === 5 && 'Excellent'}
          </p>
        </div>

        <Button
          onClick={handleSubmit}
          disabled={submitting || Object.keys(answers).length === 0}
          className="w-full"
        >
          {submitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Submitting...
            </>
          ) : (
            <>
              <Send className="mr-2 h-4 w-4" />
              Submit Feedback
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
