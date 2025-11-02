
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "@/contexts/ThemeContext";
import ErrorBoundary from "@/components/ErrorBoundary";
import { AppLayout } from "@/components/layout/AppLayout";
import LazyIndex from "./pages/LazyIndex";
import NotFound from "./pages/NotFound";
import { PriceAlertsPage } from "./pages/PriceAlerts";
import { SmartListsPage } from "./pages/SmartLists";
import { AnalyticsPage } from "./pages/Analytics";
import SearchPage from "./pages/SearchPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

const App = () => (
  <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <ErrorBoundary>
              <AppLayout>
                <Routes>
                  <Route path="/" element={<LazyIndex />} />
                  <Route path="/search" element={<SearchPage />} />
                  <Route path="/alerts" element={<PriceAlertsPage />} />
                  <Route path="/lists" element={<SmartListsPage />} />
                  <Route path="/analytics" element={<AnalyticsPage />} />
                  {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </AppLayout>
            </ErrorBoundary>
          </BrowserRouter>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  </ErrorBoundary>
);

export default App;
