# ── HOJ Vue ── Node 16 构建 (需 --openssl-legacy-provider) + Nginx
FROM node:16-alpine AS builder
WORKDIR /app
COPY package*.json .
RUN npm ci --legacy-peer-deps
COPY . .
ENV NODE_OPTIONS=--openssl-legacy-provider
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
