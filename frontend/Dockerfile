FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY app ./app
COPY lib ./lib
COPY next.config.ts tsconfig.json ./
RUN npm run build
ENV NODE_ENV=production
EXPOSE 3000
CMD ["npm","start"]

