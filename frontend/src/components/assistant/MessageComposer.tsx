import { Button } from "@/components/ui/button";
import { ArrowUp, AudioWaveform, Mic, MicOff, Square } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { useAssistantStore } from "./store";

export function MessageComposer() {
  const { send, phase, stop, activeId, model, error } = useAssistantStore();
  const [value, setValue] = useState("");
  const [isListening, setIsListening] = useState(false);
  const ref = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<any>(null);
  const baseValueRef = useRef<string>("");
  const busy = phase !== "idle";

  useEffect(() => {
    ref.current?.focus();
  }, [activeId, phase]);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  // Clean up speech recognition on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort?.();
      }
    };
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {
        console.error(e);
      }
    }
    setIsListening(false);
  }, []);

  const toggleListening = useCallback(() => {
    if (typeof window === "undefined") return;

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      toast.error("Speech recognition is not supported in this browser. Please use Google Chrome or Microsoft Edge.");
      return;
    }

    if (isListening) {
      stopListening();
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      const detectedLang = typeof navigator !== "undefined" ? navigator.language : "en-US";
      recognition.lang = detectedLang || "en-US";
      recognition.maxAlternatives = 1;

      // Preserve any text already typed
      baseValueRef.current = value.trim();

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        const finalPhrases: string[] = [];
        let interimPhrase = "";

        for (let i = 0; i < event.results.length; i++) {
          const result = event.results[i];
          const transcript = result[0]?.transcript?.trim();
          if (!transcript) continue;
          if (result.isFinal) {
            finalPhrases.push(transcript);
          } else {
            interimPhrase = transcript;
          }
        }

        const speechText = [...finalPhrases, interimPhrase].filter(Boolean).join(" ");
        const base = baseValueRef.current;
        setValue(base ? (speechText ? `${base} ${speechText}` : base) : speechText);
      };

      recognition.onerror = (event: any) => {
        console.error("Speech recognition error:", event.error);
        if (event.error === "not-allowed" || event.error === "service-not-allowed") {
          toast.error("Microphone access was denied. Please allow microphone permissions.");
        } else if (event.error !== "no-speech") {
          toast.error(`Voice error: ${event.error}`);
        }
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.error("Failed to start speech recognition:", err);
      setIsListening(false);
    }
  }, [isListening, stopListening, value]);

  const submit = () => {
    if (!value.trim() || busy) return;
    if (isListening) {
      stopListening();
    }
    send(value);
    setValue("");
  };

  return (
    <div className="mx-auto w-full max-w-[840px] shrink-0 px-4 pt-2 pb-4 sm:px-6">
      <div className="relative flex items-center gap-2 rounded-[28px] border border-border/60 bg-[#f4f4f4] dark:bg-[#2f2f2f] dark:border-[#383838]/70 px-3 py-2 shadow-workspace transition-all duration-200 focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/20">
        <label htmlFor="composer" className="sr-only">
          Message
        </label>

        {/* Text input area */}
        <textarea
          id="composer"
          ref={ref}
          rows={1}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="Ask anything..."
          className="block w-full resize-none bg-transparent pl-2.5 sm:pl-3 pr-1.5 py-1 text-[16px] leading-relaxed text-foreground placeholder:text-muted-foreground focus:outline-none min-h-[32px] max-h-[200px]"
        />

        {/* Right side controls */}
        <div className="flex shrink-0 items-center gap-1.5">
          {/* Web Speech API Mic recording button */}
          <button
            id="voice-input-btn"
            type="button"
            onClick={toggleListening}
            title={isListening ? "Listening... Click to stop" : "Start voice input"}
            aria-label={isListening ? "Stop voice input" : "Start voice input"}
            className={`flex size-9 items-center justify-center rounded-full transition-all focus-visible:outline-none ${isListening
                ? "bg-red-500/15 text-red-500 animate-pulse ring-1 ring-red-500/40"
                : "text-muted-foreground hover:text-foreground hover:bg-black/5 dark:hover:bg-white/10"
              }`}
          >
            {isListening ? (
              <MicOff className="size-5" />
            ) : (
              <Mic className="size-5" />
            )}
          </button>

          {/* Action button: Stop when busy, Send when typed, Voice waveform button when empty */}
          {busy ? (
            <Button
              size="icon"
              onClick={stop}
              title="Stop generating"
              aria-label="Stop generating"
              className="flex size-9 items-center justify-center rounded-full bg-foreground text-background transition-transform active:scale-95 focus-visible:outline-none"
            >
              <Square className="size-3 fill-current" />
            </Button>
          ) : value.trim() ? (
            <Button
              size="icon"
              onClick={submit}
              title="Send message"
              aria-label="Send message"
              className="flex size-9 items-center justify-center rounded-full bg-foreground text-background shadow-xs transition-all hover:opacity-90 active:scale-95 focus-visible:outline-none"
            >
              <ArrowUp className="size-4.5 stroke-[2.5]" />
            </Button>
          ) : (
            <button
              type="button"
              onClick={toggleListening}
              title="Voice mode"
              aria-label="Voice mode"
              className={`flex size-9 items-center justify-center rounded-full text-white shadow-sm transition-all active:scale-95 focus-visible:outline-none ${isListening
                  ? "bg-red-500 animate-pulse hover:bg-red-600"
                  : "bg-[#3b82f6] hover:bg-[#2563eb]"
                }`}
            >
              <AudioWaveform className="size-4.5" />
            </button>
          )}
        </div>
      </div>

      <p className="mt-2.5 text-center text-[10px] sm:text-[11px] text-muted-foreground">
        {error ? (
          <span className="text-destructive font-medium">{error}</span>
        ) : (
          <span className="inline-flex items-center gap-1.5">
            <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>
              Connected to{" "}
              {model.provider === "ollama"
                ? "Local (Ollama)"
                : `Cloud (${model.cloudProviderName})`}
            </span>
          </span>
        )}
      </p>
    </div>
  );
}
