const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getApiUrl: () => ipcRenderer.invoke('get-api-url'),
  getVersion: () => ipcRenderer.invoke('get-version'),
  checkForUpdates: () => ipcRenderer.invoke('check-for-updates'),
  openDevTools: () => ipcRenderer.invoke('open-devtools'),
  onDevToolsClosed: (callback) => ipcRenderer.on('devtools-closed', () => callback()),
  clearAllData: () => ipcRenderer.invoke('clear-all-data'),
});