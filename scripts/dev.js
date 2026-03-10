const { spawn } = require('child_process');
const path = require('path');

const frontendDir = path.join(__dirname, '..', 'frontend');

console.log('Starting frontend development server...');
console.log(`Working directory: ${frontendDir}`);

const dev = spawn('npm', ['run', 'dev'], {
  cwd: frontendDir,
  stdio: 'inherit',
  shell: true
});

dev.on('error', (err) => {
  console.error('Failed to start dev server:', err);
  process.exit(1);
});

dev.on('close', (code) => {
  console.log(`Dev server exited with code ${code}`);
  process.exit(code);
});
