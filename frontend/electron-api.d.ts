interface ElectronAPI {
  getApiUrl: () => Promise<string>;
  checkForUpdates: () => Promise<void>;
  openDevTools: () => Promise<void>;
  onDevToolsClosed: (callback: () => void) => void;
  clearAllData: () => Promise<{ success: boolean; message: string }>;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
    __API_URL__?: string;
  }
}
