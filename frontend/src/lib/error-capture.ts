let lastCapturedError: unknown = null;

if (typeof window !== "undefined") {
  window.addEventListener("error", (event) => {
    lastCapturedError = event.error || event.message;
  });
  window.addEventListener("unhandledrejection", (event) => {
    lastCapturedError = event.reason;
  });
}

export function captureError(error: unknown) {
  lastCapturedError = error;
}

export function consumeLastCapturedError(): unknown {
  const err = lastCapturedError;
  lastCapturedError = null;
  return err;
}
