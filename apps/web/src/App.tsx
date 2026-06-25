import { getApiBaseUrl } from "./api/client";
import { AppShell } from "./components/AppShell";
import { HomePage } from "./pages/HomePage";

export default function App() {
  return (
    <AppShell apiBaseUrl={getApiBaseUrl()}>
      <HomePage />
    </AppShell>
  );
}
