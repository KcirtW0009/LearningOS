const { app, BrowserWindow, ipcMain, shell, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');
const net = require('net');
const { autoUpdater } = require('electron-updater');

let mainWindow = null;
let backendProcess = null;
let backendPort = 8000;
let frontendPort = 0;
let frontendServer = null;
let splashWindow = null;

const isDev = !app.isPackaged;

// ── Built-in HTTP static server for frontend ──────────────────────────

const MIME_TYPES = {
  '.html': 'text/html', '.js': 'application/javascript',
  '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
  '.woff2': 'font/woff2', '.txt': 'text/plain',
};

function startFrontendServer() {
  const frontendOutDir = isDev
    ? path.join(__dirname, '../frontend/out')
    : path.join(process.resourcesPath, 'frontend', 'out');

  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      let urlPath = req.url.split('?')[0];
      if (urlPath === '/') urlPath = '/index.html';
      
      let filePath = path.join(frontendOutDir, urlPath);

      // SPA fallback: if file not found, try .html extension or serve index.html
      if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
        const withHtml = filePath.replace(/\/$/, '') + '.html';
        if (fs.existsSync(withHtml)) {
          filePath = withHtml;
        } else {
          filePath = path.join(frontendOutDir, 'index.html');
        }
      }

      const ext = path.extname(filePath).toLowerCase();
      res.writeHead(200, { 'Content-Type': MIME_TYPES[ext] || 'application/octet-stream' });
      res.end(fs.readFileSync(filePath));
    });

    server.listen(0, '127.0.0.1', () => {
      frontendPort = server.address().port;
      frontendServer = server;
      console.log(`[Electron] Frontend server on http://127.0.0.1:${frontendPort}`);
      resolve(frontendPort);
    });
  });
}

// ── Port utilities ────────────────────────────────────────────────────

function findAvailablePort(startPort) {
  return new Promise((resolve) => {
    const checkPort = (port) => {
      const server = net.createServer();
      server.once('error', () => checkPort(port + 1));
      server.once('listening', () => { server.close(); resolve(port); });
      server.listen(port, '127.0.0.1');
    };
    checkPort(startPort);
  });
}

// ── Splash window ─────────────────────────────────────────────────────

async function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 400, height: 500,
    transparent: true, frame: false,
    resizable: false, center: true,
    alwaysOnTop: true,
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  });

  const splashHtml = `
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>LearningOS</title>
      <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:white}
        .logo{width:80px;height:80px;border-radius:20px;background:rgba(255,255,255,.15);backdrop-filter:blur(10px);display:flex;align-items:center;justify-content:center;font-size:40px;margin-bottom:24px;animation:float 3s ease-in-out infinite}
        @keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
        h1{font-size:28px;font-weight:700;margin-bottom:8px;letter-spacing:1px}
        .subtitle{font-size:14px;opacity:.8;margin-bottom:40px}
        .loader{width:48px;height:48px;border:3px solid rgba(255,255,255,.2);border-top-color:white;border-radius:50%;animation:spin 1s linear infinite;margin-bottom:24px}
        @keyframes spin{to{transform:rotate(360deg)}}
        .status{font-size:13px;opacity:.9}
        .progress-bar{width:200px;height:4px;background:rgba(255,255,255,.2);border-radius:2px;overflow:hidden;margin-top:16px}
        .progress-fill{height:100%;background:white;border-radius:2px;width:0%;transition:width .3s}
        .version{font-size:11px;opacity:.5;margin-top:24px}
      </style>
    </head>
    <body>
      <div class="logo">🌳</div><h1>LearningOS</h1><p class="subtitle">构建你的知识图谱</p>
      <div class="loader"></div>
      <div class="status" id="status">正在启动后端服务...</div>
      <div class="progress-bar"><div class="progress-fill" id="progress"></div></div>
      <div class="version">v${app.getVersion()}</div>
    </body></html>`;

  splashWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(splashHtml)}`);
  return splashWindow;
}

function updateSplashStatus(message, progress = null) {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.webContents.executeJavaScript(`
      document.getElementById('status').textContent = '${message.replace(/'/g, "\\'")}';
      ${progress !== null ? `document.getElementById('progress').style.width = '${progress}%';` : ''}
    `).catch(() => {});
  }
}

// ── Backend ───────────────────────────────────────────────────────────

async function startBackend() {
  updateSplashStatus('检测可用端口...', 10);
  backendPort = await findAvailablePort(8000);
  console.log(`[Electron] Starting backend on port ${backendPort}`);
  updateSplashStatus(`启动后端服务 (端口 ${backendPort})...`, 20);

  const runtimeDir = isDev 
    ? path.join(__dirname, '../runtime')
    : path.join(process.resourcesPath, 'runtime');

  if (isDev) {
    const pythonPath = process.env.PYTHON_PATH || 'python';
    backendProcess = spawn(pythonPath, [
      '-m', 'uvicorn', 'los.api.server:app',
      '--host', '127.0.0.1', '--port', String(backendPort), '--reload'
    ], {
      cwd: runtimeDir,
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
    });
  } else {
    const backendExe = path.join(process.resourcesPath, 'backend.exe');
    const graphsDir = path.join(process.resourcesPath, 'runtime', 'graphs');
    const dataDir = app.getPath('userData');

    if (!fs.existsSync(backendExe)) {
      throw new Error('Backend executable not found: ' + backendExe);
    }

    backendProcess = spawn(backendExe, ['--host', '127.0.0.1', '--port', String(backendPort)], {
      cwd: runtimeDir,
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
      env: {
        ...process.env,
        LEARNINGOS_GRAPHS_DIR: graphsDir,
        LEARNINGOS_DATA_DIR: dataDir,
      },
    });
  }

  backendProcess.stdout.on('data', (d) => console.log(`[Backend] ${d.toString().trim()}`));
  backendProcess.stderr.on('data', (d) => console.log(`[Backend ERROR] ${d.toString().trim()}`));

  updateSplashStatus('等待服务就绪...', 50);

  return new Promise((resolve, reject) => {
    let attempts = 0;
    const maxAttempts = 30;
    const checkReady = () => {
      attempts++;
      const socket = net.createConnection({ port: backendPort, host: '127.0.0.1' }, () => {
        socket.end();
        updateSplashStatus('服务就绪！', 90);
        setTimeout(resolve, 500);
      });
      socket.on('error', () => {
        if (attempts >= maxAttempts) {
          reject(new Error('Backend failed to start after 30 attempts'));
        } else {
          updateSplashStatus(`等待服务就绪 (${attempts}/${maxAttempts})...`, Math.min(50 + attempts * 1.5, 80));
          setTimeout(checkReady, 500);
        }
      });
    };
    setTimeout(checkReady, 1000);
  });
}

// ── Main window ───────────────────────────────────────────────────────

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200, height: 800,
    minWidth: 800, minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    title: `LearningOS v${app.getVersion()}`,
    autoHideMenuBar: true,
    show: false,
  });

  // DevTools close notification
  mainWindow.webContents.on('devtools-closed', () => {
    mainWindow.webContents.send('devtools-closed');
  });

  mainWindow.webContents.executeJavaScript(
    `window.__API_URL__ = "http://127.0.0.1:${backendPort}";`
  ).catch(console.error);

  mainWindow.webContents.on('did-fail-load', (_, code, desc, url) => {
    console.error(`[Electron] Load failed: ${code} - ${desc} at ${url}`);
  });

  if (isDev) {
    await mainWindow.loadURL('http://localhost:3000');
  } else {
    await mainWindow.loadURL(`http://127.0.0.1:${frontendPort}`);
  }

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url);
    return { action: 'deny' };
  });

  mainWindow.once('ready-to-show', () => {
    console.log('[Electron] Main window ready');
    if (splashWindow && !splashWindow.isDestroyed()) splashWindow.destroy();
    mainWindow.show();
  });

  // Fallback timeout
  setTimeout(() => {
    if (splashWindow && !splashWindow.isDestroyed()) {
      console.error('[Electron] Window ready timeout');
      splashWindow.destroy();
      mainWindow.show();
    }
  }, 15000);
}

// ── Clear all data (IPC handler) ──────────────────────────────────────

ipcMain.handle('clear-all-data', () => {
  try {
    const userDataPath = app.getPath('userData');
    const filesToDelete = [
      'user-global-state.json',
      'runtime-manifest.json',
      'devtools-autoclose',
    ];
    
    filesToDelete.forEach(file => {
      const filePath = path.join(userDataPath, file);
      try {
        if (fs.existsSync(filePath)) {
          fs.unlinkSync(filePath);
          console.log(`[Electron] Deleted: ${file}`);
        }
      } catch (e) {
        console.error(`[Electron] Failed to delete ${file}:`, e);
      }
    });
    
    const userStateFiles = fs.readdirSync(userDataPath).filter(f => f.startsWith('user-state-'));
    userStateFiles.forEach(file => {
      const filePath = path.join(userDataPath, file);
      try {
        if (fs.existsSync(filePath)) {
          fs.unlinkSync(filePath);
          console.log(`[Electron] Deleted: ${file}`);
        }
      } catch (e) {
        console.error(`[Electron] Failed to delete ${file}:`, e);
      }
    });
    
    return { success: true, message: '所有后端数据已清理' };
  } catch (e) {
    console.error('[Electron] Failed to clear all data:', e);
    return { success: false, message: '清理失败: ' + e.message };
  }
});

// ── Error dialog ──────────────────────────────────────────────────────

function showErrorDialog(title, message, detail) {
  if (splashWindow && !splashWindow.isDestroyed()) splashWindow.destroy();
  dialog.showMessageBox({
    type: 'error', title, message, detail,
    buttons: ['退出', '重试'], defaultId: 0,
  }).then((result) => {
    if (result.response === 1) app.relaunch();
    app.quit();
  });
}

// ── Cleanup ───────────────────────────────────────────────────────────

function cleanup() {
  if (backendProcess) {
    try {
      if (process.platform === 'win32') {
        spawn('taskkill', ['/F', '/T', '/PID', String(backendProcess.pid)]);
      } else {
        try { process.kill(-backendProcess.pid); } catch { backendProcess.kill(); }
      }
    } catch { try { backendProcess.kill(); } catch {} }
    backendProcess = null;
  }
  if (frontendServer) {
    frontendServer.close();
    frontendServer = null;
  }
}

// ── App lifecycle ─────────────────────────────────────────────────────

app.whenReady().then(async () => {
  try {
    console.log('[Electron] Starting LearningOS...');
    await createSplashWindow();
    updateSplashStatus('初始化应用...', 5);

    if (!isDev) {
      await startFrontendServer();
    }

    await startBackend();
    console.log('[Electron] Backend ready');
    updateSplashStatus('启动主界面...', 95);
    await createWindow();
    console.log('[Electron] Window created');
  } catch (error) {
    console.error('[Electron] Startup failed:', error);
    showErrorDialog('启动失败', 'LearningOS 无法启动', error.message);
  }
});

app.on('window-all-closed', () => { cleanup(); app.quit(); });
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

// ── IPC ───────────────────────────────────────────────────────────────

ipcMain.handle('get-api-url', () => `http://127.0.0.1:${backendPort}`);

ipcMain.handle('get-version', () => app.getVersion());

ipcMain.handle('check-for-updates', () => {
  if (isDev) return { available: false, message: '开发模式下禁用更新检查' };
  return { available: false, message: '检查完成' };
});

ipcMain.handle('open-devtools', () => {
  if (mainWindow && !mainWindow.isDestroyed()) {
    try {
      if (!mainWindow.isFocused()) {
        mainWindow.focus();
      }
      if (mainWindow.webContents.isDevToolsOpened()) {
        mainWindow.webContents.closeDevTools();
        setTimeout(() => {
          if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.openDevTools({ mode: 'detach' });
          }
        }, 300);
        return { opened: true };
      }
      mainWindow.webContents.openDevTools({ mode: 'detach' });
      return { opened: true };
    } catch (e) {
      return { opened: false, message: String(e) };
    }
  }
  return { opened: false, message: '窗口未就绪' };
});
