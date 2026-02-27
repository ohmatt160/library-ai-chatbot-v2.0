import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/app/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/app/components/ui/tabs';
import { Button } from '@/app/components/ui/button';
import { Badge } from '@/app/components/ui/badge';
import { Progress } from '@/app/components/ui/progress';
import { Loader2, RefreshCw, TrendingUp, Target, Star } from 'lucide-react';
import { toast } from 'sonner';

interface F1Report {
  precision: number;
  recall: number;
  f1_score: number;
  average_type: string;
  total_samples: number;
  per_class?: Record<string, {
    precision: number;
    recall: number;
    f1_score: number;
    support: number;
  }>;
}

interface SatisfactionStats {
  total_responses: number;
  overall_satisfaction: {
    mean: number;
    median: number;
    std_dev: number;
  };
  overall_rating: {
    mean: number;
    distribution: Record<number, number>;
  };
  question_statistics: Record<string, {
    question: string;
    mean: number;
    median: number;
    std_dev: number;
    min: number;
    max: number;
    total_responses: number;
  }>;
  nps_score: number;
  would_use_again: string;
}

export function EvaluationReport() {
  const [f1Report, setF1Report] = useState<F1Report | null>(null);
  const [satisfactionStats, setSatisfactionStats] = useState<SatisfactionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Fetch F1 report
      const f1Response = await fetch('/api/evaluation/report', { headers });
      const f1Data = await f1Response.json();
      if (f1Data.status === 'success') {
        setF1Report(f1Data.report);
      }

      // Fetch satisfaction stats
      const statsResponse = await fetch('/api/questionnaire/stats', { headers });
      const statsData = await statsResponse.json();
      if (statsData.status === 'success') {
        setSatisfactionStats(statsData.statistics);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load evaluation data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-500';
    if (score >= 0.6) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getScoreBadge = (score: number) => {
    if (score >= 0.8) return 'bg-green-500';
    if (score >= 0.6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center p-8">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Loading evaluation data...</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Evaluation Report</h2>
          <p className="text-muted-foreground">F1-Score and User Satisfaction Metrics</p>
        </div>
        <Button onClick={handleRefresh} disabled={refreshing}>
          {refreshing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
          Refresh
        </Button>
      </div>

      <Tabs defaultValue="f1" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="f1">F1-Score Analysis</TabsTrigger>
          <TabsTrigger value="satisfaction">User Satisfaction</TabsTrigger>
        </TabsList>

        {/* F1-Score Tab */}
        <TabsContent value="f1" className="space-y-4">
          {f1Report && f1Report.total_samples > 0 ? (
            <>
              {/* Overall Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Precision</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className={`text-3xl font-bold ${getScoreColor(f1Report.precision)}`}>
                      {(f1Report.precision * 100).toFixed(1)}%
                    </div>
                    <Progress value={f1Report.precision * 100} className="mt-2" />
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Recall</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className={`text-3xl font-bold ${getScoreColor(f1Report.recall)}`}>
                      {(f1Report.recall * 100).toFixed(1)}%
                    </div>
                    <Progress value={f1Report.recall * 100} className="mt-2" />
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">F1-Score</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className={`text-3xl font-bold ${getScoreColor(f1Report.f1_score)}`}>
                      {(f1Report.f1_score * 100).toFixed(1)}%
                    </div>
                    <Progress value={f1Report.f1_score * 100} className="mt-2" />
                  </CardContent>
                </Card>
              </div>

              {/* Per-Class Metrics */}
              {f1Report.per_class && Object.keys(f1Report.per_class).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <Target className="mr-2 h-5 w-5" />
                      Per-Intent Performance
                    </CardTitle>
                    <CardDescription>F1-Score breakdown by intent type</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {Object.entries(f1Report.per_class).map(([intent, metrics]) => (
                        <div key={intent} className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-medium capitalize">{intent.replace('_', ' ')}</span>
                            <Badge className={getScoreBadge(metrics.f1_score)}>
                              F1: {(metrics.f1_score * 100).toFixed(0)}%
                            </Badge>
                          </div>
                          <div className="grid grid-cols-3 gap-2 text-sm">
                            <div>
                              <span className="text-muted-foreground">Precision: </span>
                              <span className={getScoreColor(metrics.precision)}>
                                {(metrics.precision * 100).toFixed(0)}%
                              </span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Recall: </span>
                              <span className={getScoreColor(metrics.recall)}>
                                {(metrics.recall * 100).toFixed(0)}%
                              </span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Samples: </span>
                              <span>{metrics.support}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center p-8">
                <TrendingUp className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold">No F1 Data Yet</h3>
                <p className="text-muted-foreground text-center">
                  F1 scores will appear here after collecting intent classification data.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Satisfaction Tab */}
        <TabsContent value="satisfaction" className="space-y-4">
          {satisfactionStats && satisfactionStats.total_responses > 0 ? (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Total Responses</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{satisfactionStats.total_responses}</div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Avg Satisfaction</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold flex items-center">
                      {satisfactionStats.overall_satisfaction.mean.toFixed(1)}
                      <Star className="ml-1 h-5 w-5 fill-yellow-400 text-yellow-400" />
                    </div>
                    <p className="text-xs text-muted-foreground">out of 5</p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">NPS Score</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className={`text-3xl font-bold ${getScoreColor(satisfactionStats.nps_score / 100)}`}>
                      {satisfactionStats.nps_score.toFixed(0)}
                    </div>
                    <p className="text-xs text-muted-foreground">Net Promoter Score</p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Would Use Again</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{satisfactionStats.would_use_again}</div>
                    <p className="text-xs text-muted-foreground">users</p>
                  </CardContent>
                </Card>
              </div>

              {/* Rating Distribution */}
              <Card>
                <CardHeader>
                  <CardTitle>Rating Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4">
                    {[1, 2, 3, 4, 5].map((rating) => (
                      <div key={rating} className="flex-1 text-center">
                        <div className="flex items-center justify-center mb-2">
                          <Star className={`h-5 w-5 ${rating <= satisfactionStats.overall_rating.mean ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`} />
                        </div>
                        <div className="h-24 flex flex-col justify-end">
                          <div 
                            className="bg-primary rounded-t"
                            style={{ 
                              height: `${((satisfactionStats.overall_rating.distribution[rating] || 0) / satisfactionStats.total_responses) * 100}%`,
                              minHeight: satisfactionStats.overall_rating.distribution[rating] ? '4px' : '0'
                            }}
                          />
                        </div>
                        <p className="text-sm mt-1">{satisfactionStats.overall_rating.distribution[rating] || 0}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Per-Question Stats */}
              {satisfactionStats.question_statistics && Object.keys(satisfactionStats.question_statistics).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Question Breakdown</CardTitle>
                    <CardDescription>Average score per question</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {Object.entries(satisfactionStats.question_statistics).map(([qId, stats]) => (
                        <div key={qId} className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">{stats.question}</span>
                            <Badge variant="outline">{stats.mean.toFixed(1)} / 5</Badge>
                          </div>
                          <Progress value={(stats.mean / 5) * 100} />
                          <p className="text-xs text-muted-foreground">
                            {stats.total_responses} responses • σ = {stats.std_dev.toFixed(2)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center p-8">
                <Star className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold">No Survey Data Yet</h3>
                <p className="text-muted-foreground text-center">
                  User satisfaction data will appear here after users complete the survey.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
