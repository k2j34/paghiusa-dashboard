const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js')
    }
  });

  mainWindow.loadFile('index.html');

  mainWindow.on('closed', function () {
    mainWindow = null;
  });

  startPythonProcess();
}

function startPythonProcess() {
  const python = spawn('python', ['people_counter.py']);

  python.stdout.on('data', (data) => {
    const output = data.toString().trim();
    console.log('Python Output:', output);

    // Send the output to the renderer process
    if (mainWindow) {
      mainWindow.webContents.send('python-data', output);
    }
  });

  python.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data}`);
  });

  python.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', function () {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
