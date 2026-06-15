<script setup>
import { ref, onMounted, computed } from "vue";

const emit = defineEmits(["login", "register", "back"]);

const username = ref("");
const password = ref("");
const captchaId = ref(null);
const captchaTarget = ref(null);
const captchaValue = ref(null);
const sliderOffset = ref(0);
const error = ref("");
const isLoading = ref(true);
const isVerified = ref(false);

onMounted(async () => {
  await fetchCaptcha();
  isLoading.value = false;
});

async function fetchCaptcha() {
  try {
    const res = await fetch("/api/captcha");
    const data = await res.json();
    captchaId.value = data.captcha_id;
    captchaTarget.value = data.target_value;
    captchaValue.value = null;
    sliderOffset.value = 0;
    isVerified.value = false;
    error.value = "";
  } catch (e) {
    console.error("获取验证码失败:", e);
    error.value = "获取验证码失败，请刷新重试";
  }
}

function handleSliderChange(e) {
  const slider = e.target;
  sliderOffset.value = slider.value / 100;
  captchaValue.value = slider.value / 100;

  // 实时验证是否匹配（误差 ±0.05）
  if (captchaTarget.value !== null) {
    const diff = Math.abs(captchaValue.value - captchaTarget.value);
    if (diff <= 0.05) {
      isVerified.value = true;
      error.value = "";
    } else {
      isVerified.value = false;
    }
  }
}

// 计算滑块位置的背景渐变
const sliderBackground = computed(() => {
  const percent = sliderOffset.value * 100;
  return {
    background: `linear-gradient(to right, var(--success) 0%, var(--success) ${percent}%, #e2e8f0 ${percent}%, #e2e8f0 100%)`
  };
});

// 计算验证状态提示
const verifyHint = computed(() => {
  if (captchaTarget.value === null) return "";
  if (captchaValue.value === null) return "请拖动滑块到目标位置";
  const diff = Math.abs(captchaValue.value - captchaTarget.value);
  if (diff <= 0.05) return "✅ 验证通过";
  return "❌ 验证未通过";
});

async function handleLogin() {
  if (!username.value || !password.value) {
    error.value = "请输入用户名和密码";
    return;
  }

  if (captchaValue.value === null) {
    error.value = "请完成滑动验证";
    return;
  }

  // 检查滑动验证码是否匹配（前端预验证）
  if (!isVerified.value) {
    error.value = "滑动验证未通过，请调整到目标值位置";
    return;
  }

  try {
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: username.value,
        password: password.value,
        captcha_id: captchaId.value,
        captcha_value: captchaValue.value,
      }),
    });

    const data = await res.json();

    if (!res.ok) {
      error.value = data.detail || "登录失败";
      if (data.detail.includes("验证码")) {
        await fetchCaptcha();
      }
      return;
    }

    error.value = "";
    emit("login", data);
  } catch (e) {
    console.error("登录失败:", e);
    error.value = "网络错误，请稍后重试";
  }
}

function handleBack() {
  emit("back");
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <h2 class="login-title">📚 登录</h2>

      <div class="form-group">
        <label for="username">用户名</label>
        <input
          id="username"
          v-model="username"
          type="text"
          placeholder="请输入用户名"
          class="form-input"
        />
      </div>

      <div class="form-group">
        <label for="password">密码</label>
        <input
          id="password"
          v-model="password"
          type="password"
          placeholder="请输入密码"
          class="form-input"
        />
      </div>

      <div class="form-group">
        <label>滑动验证</label>
        <div class="captcha-container">
          <div class="captcha-display">
            <span class="captcha-target">🎯 目标：{{ captchaTarget?.toFixed(2) }}</span>
            <span class="captcha-current">当前：{{ captchaValue?.toFixed(2) }}</span>
          </div>
          <!-- 进度条容器，包含目标刻度标记 -->
          <div class="slider-wrapper">
            <input
              type="range"
              min="0"
              max="100"
              value="0"
              class="slider"
              :style="sliderBackground"
              @input="handleSliderChange"
            />
            <!-- 目标刻度标记 -->
            <div
              class="slider-target-marker"
              :style="{ left: captchaTarget * 100 + '%' }"
              title="目标位置"
            >
              <span class="marker-flag">🎯</span>
            </div>
          </div>
          <div class="slider-hints">
            <span></span>
            <span :class="['gap-hint', { 'gap-success': isVerified }]">{{
              verifyHint
            }}</span>
            <span></span>
          </div>
        </div>
      </div>

      <div v-if="error" class="error-message">{{ error }}</div>

      <div class="login-actions">
        <button class="btn btn-outline" @click="handleBack">返回</button>
        <button class="btn btn-primary" @click="handleLogin">登录</button>
      </div>

      <div class="login-footer">
        还没有账号？
        <a href="#" class="login-link" @click.prevent="emit('register')"
          >去注册</a
        >
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}

.login-card {
  background: var(--card-bg);
  border-radius: var(--radius);
  padding: 32px;
  width: 100%;
  max-width: 400px;
  box-shadow: var(--shadow);
}

.login-title {
  text-align: center;
  color: var(--primary);
  margin-bottom: 24px;
  font-size: 1.5rem;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: var(--text);
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 12px;
  border: 2px solid var(--border);
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary);
}

.captcha-container {
  background: #f8fafc;
  border-radius: 8px;
  padding: 16px;
}

.captcha-display {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 0.9rem;
}

.captcha-target {
  color: var(--primary);
  font-weight: 600;
}

.captcha-current {
  color: var(--text-secondary);
}

.slider-wrapper {
  position: relative;
  width: 100%;
}

.slider {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: #e2e8f0;
  outline: none;
  -webkit-appearance: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--primary);
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* 目标刻度标记 */
.slider-target-marker {
  position: absolute;
  top: -4px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  pointer-events: none;
  z-index: 10;
}

.marker-flag {
  font-size: 1rem;
  animation: bounce 1s ease-in-out infinite;
}

@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
}

.slider-hints {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.gap-hint {
  color: var(--primary);
  font-weight: 600;
}

.gap-success {
  color: var(--success);
}

.error-message {
  background: #fef2f2;
  color: var(--danger);
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 0.9rem;
}

.login-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.login-link {
  color: var(--primary);
  text-decoration: none;
  font-weight: 500;
}

.login-link:hover {
  text-decoration: underline;
}
</style>
