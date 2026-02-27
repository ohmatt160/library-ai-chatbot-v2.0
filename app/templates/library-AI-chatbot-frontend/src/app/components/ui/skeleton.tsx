import * as React from "react";
import { cn } from "./utils";

const Skeleton = React.forwardRef<HTMLDivElement, React.ComponentProps<"div">>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      data-slot="skeleton"
      className={cn("bg-accent animate-pulse rounded-md", className)}
      {...props}
    />
  ),
);

Skeleton.displayName = "Skeleton";

export { Skeleton };
