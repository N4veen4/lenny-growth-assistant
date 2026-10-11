import { Moon, Sun, Monitor } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/hooks/use-theme";
import { cn } from "@/lib/utils";

export function ThemeToggle({
  className,
  variant = "ghost",
}: {
  className?: string;
  variant?: "ghost" | "outline";
}) {
  const { resolvedTheme, toggleTheme } = useTheme();

  return (
    <Button
      variant={variant}
      size="sm"
      onClick={toggleTheme}
      className={cn(
        "relative h-9 px-2.5 flex items-center gap-2 rounded-lg text-xs font-medium transition-all duration-200",
        "text-muted-foreground hover:text-foreground hover:bg-accent/80",
        className,
      )}
      title={`Switch to ${resolvedTheme === "dark" ? "light" : "dark"} mode`}
      aria-label={`Switch to ${resolvedTheme === "dark" ? "light" : "dark"} mode`}
    >
      {resolvedTheme === "dark" ? (
        <>
          <Sun className="size-4 text-amber-400 transition-transform duration-300 hover:rotate-45" />
          <span className="hidden sm:inline">Light mode</span>
        </>
      ) : (
        <>
          <Moon className="size-4 text-indigo-500 transition-transform duration-300 hover:-rotate-12" />
          <span className="hidden sm:inline">Dark mode</span>
        </>
      )}
    </Button>
  );
}

export function ThemeSegmentedControl({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme();

  return (
    <div
      className={cn(
        "flex items-center rounded-lg border border-border/70 bg-background/50 p-0.5 text-xs",
        className,
      )}
    >
      <button
        type="button"
        onClick={() => setTheme("light")}
        className={cn(
          "flex flex-1 items-center justify-center gap-1.5 rounded-md py-1.5 px-2 font-medium transition-colors",
          theme === "light"
            ? "bg-card text-foreground shadow-xs border border-border/50"
            : "text-muted-foreground hover:text-foreground",
        )}
        title="Light theme"
      >
        <Sun className="size-3.5 text-amber-500" />
        <span>Light</span>
      </button>
      <button
        type="button"
        onClick={() => setTheme("dark")}
        className={cn(
          "flex flex-1 items-center justify-center gap-1.5 rounded-md py-1.5 px-2 font-medium transition-colors",
          theme === "dark"
            ? "bg-card text-foreground shadow-xs border border-border/50"
            : "text-muted-foreground hover:text-foreground",
        )}
        title="Dark theme"
      >
        <Moon className="size-3.5 text-indigo-400" />
        <span>Dark</span>
      </button>
      <button
        type="button"
        onClick={() => setTheme("system")}
        className={cn(
          "flex flex-1 items-center justify-center gap-1.5 rounded-md py-1.5 px-2 font-medium transition-colors",
          theme === "system"
            ? "bg-card text-foreground shadow-xs border border-border/50"
            : "text-muted-foreground hover:text-foreground",
        )}
        title="System theme"
      >
        <Monitor className="size-3.5 text-muted-foreground" />
        <span>System</span>
      </button>
    </div>
  );
}
