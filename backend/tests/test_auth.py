"""
用户认证 API 测试。
"""
import pytest
from fastapi.testclient import TestClient

# 导入 app 之前需要设置好环境变量
import os
os.environ["PASSWORD_SALT"] = "test_salt_for_unit_tests"

from main import app
from database import get_connection


@pytest.fixture
def client():
    """创建测试客户端。"""
    # 清空验证码存储
    from auth import _captcha_store
    _captcha_store.clear()

    # 清理测试用户数据
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 删除所有测试用户（以 test 开头的用户名）
        cursor.execute("DELETE FROM progress WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'test%' OR username LIKE 'duplicate%' OR username LIKE 'login%' OR username LIKE 'wrong%' OR username LIKE 'expired%')")
        cursor.execute("DELETE FROM users WHERE username LIKE 'test%' OR username LIKE 'duplicate%' OR username LIKE 'login%' OR username LIKE 'wrong%' OR username LIKE 'expired%'")
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    with TestClient(app) as client:
        yield client


class TestCaptchaAPI:
    """测试验证码 API。"""

    def test_get_captcha_returns_valid_response(self, client):
        """测试获取验证码返回有效响应。"""
        response = client.get("/api/captcha")

        assert response.status_code == 200
        data = response.json()
        assert "captcha_id" in data
        assert "target_value" in data
        assert len(data["captcha_id"]) == 16

    def test_get_captcha_target_value_in_range(self, client):
        """测试验证码目标值在 0.4-1.0 范围内。"""
        for _ in range(20):  # 多次测试确保范围正确
            response = client.get("/api/captcha")
            data = response.json()
            assert 0.4 <= data["target_value"] <= 1.0, f"目标值 {data['target_value']} 不在 0.4-1.0 范围内"

    def test_get_captcha_target_value_has_2_decimal_places(self, client):
        """测试验证码目标值保留两位小数。"""
        response = client.get("/api/captcha")
        data = response.json()
        # 检查是否为两位小数
        target_str = str(data["target_value"])
        if "." in target_str:
            decimal_places = len(target_str.split(".")[1])
            assert decimal_places <= 2


class TestRegisterAPI:
    """测试注册 API。"""

    def test_register_success(self, client):
        """测试注册成功。"""
        response = client.post("/api/register", json={
            "username": "testuser123",
            "password": "password123",
            "confirm_password": "password123"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "注册成功"
        assert data["username"] == "testuser123"

    def test_register_duplicate_username(self, client):
        """测试重复用户名注册失败。"""
        # 先注册一个用户
        client.post("/api/register", json={
            "username": "duplicateuser",
            "password": "password123",
            "confirm_password": "password123"
        })

        # 尝试注册同名用户
        response = client.post("/api/register", json={
            "username": "duplicateuser",
            "password": "password456",
            "confirm_password": "password456"
        })

        assert response.status_code == 400
        assert "用户名已存在" in response.json()["detail"]

    def test_register_password_mismatch(self, client):
        """测试两次密码不一致失败。"""
        response = client.post("/api/register", json={
            "username": "testuser",
            "password": "password123",
            "confirm_password": "password456"  # 不一致
        })

        assert response.status_code == 422  # 验证错误

    def test_register_password_too_short(self, client):
        """测试密码过短失败。"""
        response = client.post("/api/register", json={
            "username": "testuser",
            "password": "short",  # 少于 8 位
            "confirm_password": "short"
        })

        assert response.status_code == 422

    def test_register_password_invalid_chars(self, client):
        """测试密码包含非法字符失败。"""
        response = client.post("/api/register", json={
            "username": "testuser",
            "password": "password_!",  # 包含非法字符
            "confirm_password": "password_!"
        })

        assert response.status_code == 422


class TestLoginAPI:
    """测试登录 API。"""

    def test_login_success_with_valid_captcha(self, client):
        """测试使用有效验证码登录成功。"""
        # 先注册用户
        client.post("/api/register", json={
            "username": "logintestuser",
            "password": "password123",
            "confirm_password": "password123"
        })

        # 获取验证码
        captcha_response = client.get("/api/captcha")
        captcha_data = captcha_response.json()

        # 使用正确的验证码值登录
        login_response = client.post("/api/login", json={
            "username": "logintestuser",
            "password": "password123",
            "captcha_id": captcha_data["captcha_id"],
            "captcha_value": captcha_data["target_value"]  # 完全匹配
        })

        assert login_response.status_code == 200
        data = login_response.json()
        assert data["message"] == "登录成功"
        assert "session_token" in login_response.cookies

    def test_login_success_with_tolerance(self, client):
        """测试在误差范围内登录成功。"""
        # 先注册用户
        client.post("/api/register", json={
            "username": "tolerancetestuser",
            "password": "password123",
            "confirm_password": "password123"
        })

        # 获取验证码
        captcha_response = client.get("/api/captcha")
        captcha_data = captcha_response.json()

        # 使用有误差但在允许范围内的值登录（误差 0.05）
        login_response = client.post("/api/login", json={
            "username": "tolerancetestuser",
            "password": "password123",
            "captcha_id": captcha_data["captcha_id"],
            "captcha_value": captcha_data["target_value"] + 0.03  # 在 0.05 误差范围内
        })

        assert login_response.status_code == 200

    def test_login_fail_with_wrong_password(self, client):
        """测试密码错误登录失败。"""
        # 先注册用户
        client.post("/api/register", json={
            "username": "wrongpwuser",
            "password": "password123",
            "confirm_password": "password123"
        })

        # 获取验证码
        captcha_response = client.get("/api/captcha")
        captcha_data = captcha_response.json()

        # 使用错误密码登录
        login_response = client.post("/api/login", json={
            "username": "wrongpwuser",
            "password": "wrongpassword",
            "captcha_id": captcha_data["captcha_id"],
            "captcha_value": captcha_data["target_value"]
        })

        assert login_response.status_code == 401
        assert "用户名或密码错误" in login_response.json()["detail"]

    def test_login_fail_with_wrong_captcha(self, client):
        """测试验证码错误登录失败。"""
        # 先注册用户
        client.post("/api/register", json={
            "username": "wrongcaptchauser",
            "password": "password123",
            "confirm_password": "password123"
        })

        # 获取验证码
        captcha_response = client.get("/api/captcha")
        captcha_data = captcha_response.json()

        # 使用超出误差范围的验证码值登录
        login_response = client.post("/api/login", json={
            "username": "wrongcaptchauser",
            "password": "password123",
            "captcha_id": captcha_data["captcha_id"],
            "captcha_value": captcha_data["target_value"] + 0.1  # 超出 0.05 误差范围
        })

        assert login_response.status_code == 401
        assert "验证码不正确" in login_response.json()["detail"]

    def test_login_fail_with_expired_captcha(self, client):
        """测试使用过期验证码登录失败。"""
        # 先注册用户
        client.post("/api/register", json={
            "username": "expiredcaptchauser",
            "password": "password123",
            "confirm_password": "password123"
        })

        # 使用不存在的 captcha_id
        login_response = client.post("/api/login", json={
            "username": "expiredcaptchauser",
            "password": "password123",
            "captcha_id": "nonexistent_id",
            "captcha_value": 0.5
        })

        assert login_response.status_code == 401
        assert "验证码已过期或无效" in login_response.json()["detail"]


class TestLogoutAPI:
    """测试登出 API。"""

    def test_logout_success(self, client):
        """测试登出成功。"""
        response = client.post("/api/logout")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "登出成功"


class TestMeAPI:
    """测试获取当前用户 API。"""

    def test_get_me_not_authenticated(self, client):
        """测试未登录时获取用户信息。"""
        response = client.get("/api/me")

        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False
