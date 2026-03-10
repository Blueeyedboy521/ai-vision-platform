import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const frontendDir = join(__dirname, '..', 'frontend');

console.log('启动前端开发服务器...');
console.log('工作目录:', frontendDir);

const dev = spawn('npm', ['run', 'dev'], {
  cwd: frontendDir,
  stdio: 'inherit',
  shell: true
});

dev.on('error', (err) => {
  console.error('启动失败:', err);
  process.exit(1);
});

dev.on('close', (code) => {
  console.log('服务器已关闭，退出码:', code);
  process.exit(code);
});
