<script setup>
import { ref } from "vue";

const emit = defineEmits(["register", "login", "back"]);

const username = ref("");
const password = ref("");
const confirmPassword = ref("");
const error = ref("");
const success = ref(false);

async function handleRegister() {
    error.value = "";

    // 验证输入
    if (!username.value || !password.value || !confirmPassword.value) {
        error.value = "请填写所有字段";
        return;
    }

    if (username.value.length < 1 || username.value.length > 50) {
        error.value = "用户名长度需在 1-50 个字符之间";
        return;
    }

    if (password.value.length < 8 || password.value.length > 20) {
        error.value = "密码长度需为 8-20 位";
        return;
    }

    if (!/^[a-zA-Z0-9]+$/.test(password.value)) {
        error.value = "密码只能包含英文字母和数字";
        return;
    }

    if (password.value !== confirmPassword.value) {
        error.value = "两次输入的密码不一致";
        return;
    }

    try {
        const res = await fetch("/api/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                username: username.value,
                password: password.value,
                confirm_password: confirmPassword.value,
            }),
        });

        const data = await res.json();

        if (!res.ok) {
            error.value = data.detail || "注册失败";
            return;
        }

        success.value = true;
        setTimeout(() => {
            emit("login");
        }, 1500);
    } catch (e) {
        console.error("注册失败:", e);
        error.value = "网络错误，请稍后重试";
    }
}

function handleBack() {
    emit("back");
}
</script>

<template>
    <div class="register-container">
        <div class="register-card">
            <h2 class="register-title">📝 注册</h2>

            <div v-if="success" class="success-message">
                ✅ 注册成功，即将跳转登录...
            </div>

            <div class="form-group">
                <label for="username">用户名</label>
                <input
                    id="username"
                    v-model="username"
                    type="text"
                    placeholder="请输入用户名"
                    class="form-input"
                    :disabled="success"
                />
            </div>

            <div class="form-group">
                <label for="password">密码</label>
                <input
                    id="password"
                    v-model="password"
                    type="password"
                    placeholder="8-20 位英文和数字"
                    class="form-input"
                    :disabled="success"
                />
                <p class="form-hint">密码需为 8-20 位英文字母和数字组合</p>
            </div>

            <div class="form-group">
                <label for="confirmPassword">确认密码</label>
                <input
                    id="confirmPassword"
                    v-model="confirmPassword"
                    type="password"
                    placeholder="请再次输入密码"
                    class="form-input"
                    :disabled="success"
                />
            </div>

            <div v-if="error" class="error-message">{{ error }}</div>

            <div class="register-actions">
                <button class="btn btn-outline" @click="handleBack">返回</button>
                <button class="btn btn-primary" @click="handleRegister" :disabled="success">注册</button>
            </div>

            <div class="register-footer">
                已有账号？
                <a href="#" class="register-link" @click.prevent="emit('login')">去登录</a>
            </div>
        </div>
    </div>
</template>

<style scoped>
.register-container {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
}

.register-card {
    background: var(--card-bg);
    border-radius: var(--radius);
    padding: 32px;
    width: 100%;
    max-width: 400px;
    box-shadow: var(--shadow);
}

.register-title {
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

.form-input:disabled {
    background: #f1f5f9;
    cursor: not-allowed;
}

.form-hint {
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-top: 4px;
}

.error-message {
    background: #fef2f2;
    color: var(--danger);
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 20px;
    font-size: 0.9rem;
}

.success-message {
    background: #f0fdf4;
    color: var(--success);
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 20px;
    font-size: 0.9rem;
    text-align: center;
}

.register-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
}

.register-footer {
    text-align: center;
    margin-top: 20px;
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.register-link {
    color: var(--primary);
    text-decoration: none;
    font-weight: 500;
}

.register-link:hover {
    text-decoration: underline;
}
</style>
