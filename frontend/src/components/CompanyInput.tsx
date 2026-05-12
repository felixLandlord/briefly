interface CompanyInputProps {
  onAnalyze: (companies: string[]) => void;
}

// This component is no longer used directly (form is in App.tsx)
// Keeping it for potential future extraction
export default function CompanyInput() {
  return null;
}
