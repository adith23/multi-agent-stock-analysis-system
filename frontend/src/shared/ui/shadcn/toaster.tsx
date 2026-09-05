"use client";

import { Toaster as Sonner, toast } from "sonner";

type ToasterProps = React.ComponentProps<typeof Sonner>;

function Toaster(props: ToasterProps) {
  return (
    <Sonner
      theme="dark"
      position="bottom-right"
      toastOptions={{
        classNames: {
          toast: "!rounded-terminal !border-hairline-bright !bg-panel-raised !text-text-primary",
          description: "!text-text-dim",
          actionButton: "!rounded-terminal !bg-amber !text-void",
          cancelButton: "!rounded-terminal !bg-inset !text-text-dim",
        },
      }}
      {...props}
    />
  );
}

export { Toaster, toast };
