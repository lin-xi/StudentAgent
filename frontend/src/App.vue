<script setup></script>

<template>
  <div class="app-container">
    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<style>
/* ========== Reset & 全局 ========== */
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

* {
  box-sizing: border-box;
}

:root {
  --primary: #4f46e5;
  --primary-light: #818cf8;
  --primary-dark: #3730a3;
  --success: #10b981;
  --danger: #ef4444;
  --warning: #f59e0b;
  --bg: #f0f4ff;
  --card-bg: #ffffff;
  --text: #1e293b;
  --text-secondary: #64748b;
  --border: #e2e8f0;
  --radius: 12px;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

body {
  font-family:
    -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Microsoft YaHei", sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  min-height: 100vh;
}

.app-container {
  max-width: 100vw;
  margin: 0 auto;
  padding: 20px 16px 40px;
}

.app-header {
  text-align: center;
  margin-bottom: 32px;
  position: relative;
}

.app-title {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--primary);
}

.app-subtitle {
  color: var(--text-secondary);
  font-size: 0.95rem;
  margin-top: 4px;
}

.header-reset-btn {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  opacity: 0.5;
  transition:
    opacity 0.2s,
    background 0.2s;
  line-height: 1;
}
.header-reset-btn:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.05);
}

.app-main {
  min-height: 60vh;
}

/* ========== 通用组件 ========== */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 28px;
  border: 2px solid transparent;
  border-radius: var(--radius);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:active {
  transform: scale(0.97);
}

.btn-primary {
  background: var(--primary);
  color: #fff;
}
.btn-primary:hover {
  background: var(--primary-dark);
}

.btn-outline {
  background: transparent;
  border-color: var(--border);
  color: var(--text);
}
.btn-outline:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.btn-danger {
  background: var(--danger);
  color: #fff;
}
.btn-danger:hover {
  background: #dc2626;
}

/* ========== 加载 ========== */
.loading-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 80px 0;
  color: var(--text-secondary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ========== 通关界面 ========== */
.complete-screen {
  text-align: center;
  padding: 60px 20px;
}

.complete-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.complete-desc {
  color: var(--text-secondary);
  margin: 12px 0 24px;
}

.level-badge.large {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 16px 30px;
  border-radius: 50px;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  font-size: 1.3rem;
  font-weight: 700;
  margin-bottom: 32px;
}

.level-badge.large .level-icon {
  font-size: 1.8rem;
}

.complete-screen .btn {
  margin: 8px;
}

/* ========== 弹窗 ========== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  background: var(--card-bg);
  border-radius: var(--radius);
  padding: 28px;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.modal h3 {
  margin-bottom: 8px;
}

.modal p {
  color: var(--text-secondary);
  margin-bottom: 20px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

/* ========== 响应式 ========== */
@media (max-width: 480px) {
  .app-container {
    padding: 12px 10px 32px;
  }
  .app-title {
    font-size: 1.4rem;
  }
}
</style>
