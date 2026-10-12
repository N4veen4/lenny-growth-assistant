import { Moon, Sun, Monitor, Settings, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/hooks/use-theme";
import { cn } from "@/lib/utils";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useState } from "react";

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

export function ThemeSettingsPopover({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme();
  const [open, setOpen] = useState(false);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={cn(
            "flex size-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground focus-visible:outline-none",
            className,
          )}
          title="Theme settings"
          aria-label="Theme settings"
        >
          <Settings className="size-4" />
        </button>
      </PopoverTrigger>
      <PopoverContent align="end" side="top" className="w-44 p-1.5 shadow-xl border border-border/80">
        <p className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Appearance
        </p>
        <div className="space-y-0.5">
          <button
            type="button"
            onClick={() => {
              setTheme("light");
              setOpen(false);
            }}
            className={cn(
              "flex w-full items-center justify-between rounded-md px-2.5 py-1.5 text-xs transition-colors hover:bg-accent hover:text-foreground",
              theme === "light" && "bg-accent font-medium text-foreground",
            )}
          >
            <span className="flex items-center gap-2">
              <Sun className="size-3.5 text-amber-500" /> Light
            </span>
            {theme === "light" && <Check className="size-3.5 text-primary" />}
          </button>
          <button
            type="button"
            onClick={() => {
              setTheme("dark");
              setOpen(false);
            }}
            className={cn(
              "flex w-full items-center justify-between rounded-md px-2.5 py-1.5 text-xs transition-colors hover:bg-accent hover:text-foreground",
              theme === "dark" && "bg-accent font-medium text-foreground",
            )}
          >
            <span className="flex items-center gap-2">
              <Moon className="size-3.5 text-indigo-400" /> Dark
            </span>
            {theme === "dark" && <Check className="size-3.5 text-primary" />}
          </button>
          <button
            type="button"
            onClick={() => {
              setTheme("system");
              setOpen(false);
            }}
            className={cn(
              "flex w-full items-center justify-between rounded-md px-2.5 py-1.5 text-xs transition-colors hover:bg-accent hover:text-foreground",
              theme === "system" && "bg-accent font-medium text-foreground",
            )}
          >
            <span className="flex items-center gap-2">
              <Monitor className="size-3.5 text-muted-foreground" /> System
            </span>
            {theme === "system" && <Check className="size-3.5 text-primary" />}
          </button>
        </div>
      </PopoverContent>
    </Popover>
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
