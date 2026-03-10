const { spawn } = require('child_process');
const path = require('path');

// 切换到 frontend 目录
const frontendDir = path.join(__dirname, '..', 'frontend');

console.log(`[v0] 启动开发服务器...`);
console.log(`[v0] 工作目录: ${frontendDir}`);

// 启动 npm run dev
const dev = spawn('npm', ['run', 'dev'], {
  cwd: frontendDir,
  stdio: 'inherit',
  shell: true
});

dev.on('error', (err) => {
  console.error(`[v0] 启动失败:`, err);
  process.exit(1);
});

dev.on('exit', (code) => {
  console.log(`[v0] 开发服务器已退出，代码: ${code}`);
});
