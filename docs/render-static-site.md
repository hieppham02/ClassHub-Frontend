# Frontend ClassHub tren Render Static Site

## Repository frontend rieng
New > Static Site, chon repository frontend.
Name: classhub-web
Root Directory: de trong
Build Command: npm ci && npm run build
Publish Directory: dist

Neu dung monorepo ClassHub: Root Directory = Frontend.
Khong tao frontend bang Web Service, khong dung npm run dev / npm start lam lenh chay production.

## Environment Variables cua FRONTEND
VITE_API_URL=https://<BACKEND-THAT>.onrender.com/api
VITE_HUB_URL=https://<BACKEND-THAT>.onrender.com
NODE_VERSION=22
SKIP_INSTALL_DEPS=true

NODE_VERSION selects the latest compatible Node 22.x version for Vite 8.
SKIP_INSTALL_DEPS avoids a duplicate automatic dependency install because the Build Command runs npm ci.
Thay <BACKEND-THAT> bang hostname backend thuc te.
Chi URL cong khai duoc dua vao VITE_*. Khong them mat khau MySQL, MQTT hoac JWT vao frontend.
Bien VITE_* duoc gan luc build, doi bien can rebuild frontend.
Khong can dua .cert/ len GitHub; Vite chi doc chung khi chay dev, khong doc khi build/preview.

## Vue Router
Settings > Redirects/Rewrites:
Source: /*
Destination: /index.html
Action: Rewrite (khong phai Redirect)

## Backend CORS
Sau khi co URL frontend, tren service BACKEND dat:
Cors__AllowedOrigins__0=https://<FRONTEND-THAT>.onrender.com
Khong them /api, duong dan trang hay dau / cuoi. Luu va deploy lai backend.
VITE_HUB_URL la origin backend, code se them /hub/cabinet.

## Verify
Backend /health should respond successfully.
Open frontend /login, log in, navigate to /admin/batteries and refresh that path.
Check that API calls use the Render backend, not localhost.
A frontend 404 at nested routes indicates missing SPA rewrite.
CORS errors require checking exact frontend origin and backend configuration.

No hosting deployment or GitHub push is performed by preparing these files.
