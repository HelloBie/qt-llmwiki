# Stage 1: 前端依赖安装与静态资源构建
FROM node:20-alpine AS builder

WORKDIR /app

# 优先拷贝 package.json 利用 Docker 缓存
COPY package.json ./
RUN npm install

# 拷贝前端代码并构建
COPY . ./
RUN npm run build

# Stage 2: 使用轻量 Nginx 镜像进行静态托管和反代
FROM nginx:alpine

# 拷贝打包产物与 Nginx 配置
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
