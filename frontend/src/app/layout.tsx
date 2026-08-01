import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: `LearningOS v${process.env.APP_VERSION || '0.0.0'}`,
  description: "Graph-driven learning runtime",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {children}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', () => {
                  navigator.serviceWorker.register('/sw.js').catch(() => {});
                });
              }
            `,
          }}
        />
      </body>
    </html>
  );
}
