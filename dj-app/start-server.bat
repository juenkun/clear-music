@echo off
cd /d "%~dp0"
echo ============================================
echo   Clear-music AI DJ
echo ============================================
echo.
echo 本地访问: http://localhost:8080
echo 局域网访问: http://192.168.5.9:8080
echo.
echo 正在创建公网隧道（serveo）...
echo.

start "Clear-music-公网隧道" cmd /c "ssh -o StrictHostKeyChecking=accept-new -R 80:localhost:8080 serveo.net"
start "Clear-music-本地服务器" cmd /c ""C:\Users\Juenkun\AppData\Local\Programs\Python\Python312\python.exe" server.py"

echo 服务器已启动。
echo 公网地址会显示在新弹出的 SSH 窗口中，格式如 https://xxx.serveo.net
echo.
echo 按任意键关闭本窗口（隧道和服务器会继续运行）...
pause >nul
