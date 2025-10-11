"use client";
import * as React from "react";
import type { Toast, ToastType } from "../components/Toast";

let toastId = 0;

export function useToast() {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  const addToast = React.useCallback((type: ToastType, message: string, duration?: number) => {
    const id = `toast-${toastId++}`;
    setToasts((prev) => [...prev, { id, type, message, duration }]);
    return id;
  }, []);

  const dismissToast = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = React.useMemo(
    () => ({
      success: (message: string, duration?: number) => addToast("success", message, duration),
      error: (message: string, duration?: number) => addToast("error", message, duration),
      info: (message: string, duration?: number) => addToast("info", message, duration),
    }),
    [addToast]
  );

  return { toasts, toast, dismissToast };
}

