@echo off
cd /d D:\claude_demo\demo2\demo
echo Creating Vue 3 frontend project...
call npm create vite@latest frontend -- --template vue
if errorlevel 1 (
    echo Failed to create Vue project
    exit /b 1
)
cd frontend
echo Installing dependencies...
call npm install
echo Installing Element Plus...
call npm install element-plus axios vue-router pinia
echo Done!
