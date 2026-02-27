import { Link } from 'react-router';
import { Home, Search } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';

export function NotFoundPage() {
  return (
    <Card className="backdrop-blur-sm bg-card/80 border border-border/50">
      <CardContent className="p-12 text-center">
        <div className="text-6xl font-bold mb-4">404</div>
        <h2 className="mb-2">Page Not Found</h2>
        <p className="text-muted-foreground mb-6">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="flex gap-4 justify-center">
          <Button asChild>
            <Link to="/">
              <Home className="mr-2 h-4 w-4" />
              Go Home
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/search">
              <Search className="mr-2 h-4 w-4" />
              Search Books
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
