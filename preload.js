// preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    onPythonData: (callback) => ipcRenderer.on('python-data', (event, data) => callback(data))
});
