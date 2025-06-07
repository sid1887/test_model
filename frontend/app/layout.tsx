import React from 'react';
import type { Metadata } from 'next';
import './globals.css';
import { ThemeProvider } from './components/ui/theme-provider';

export const metadata: Metadata = {
  title: 'Cumpair - AI Price Comparison',
  description: 'AI-powered price comparison across multiple e-commerce platforms',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>      <body>
        <ThemeProvider
          defaultTheme="system"
          storageKey="cumpair-ui-theme"
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
