FROM node:20-alpine

WORKDIR /app
# install deps
COPY apps/web/package*.json ./
RUN npm ci --no-audit --no-fund

# copy rest
COPY apps/web /app
ENV NEXT_TELEMETRY_DISABLED=1
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# build and run production server
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "start"]
