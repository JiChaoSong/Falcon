FROM node:20-alpine AS builder

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"

WORKDIR /srv/falcon-ui

RUN corepack enable

COPY falcon-ui/package.json falcon-ui/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY falcon-ui ./

ARG VITE_APP_TITLE=Falcon
ARG VITE_API_BASE_URL=/api
ENV VITE_APP_TITLE=${VITE_APP_TITLE}
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN pnpm build

FROM nginx:1.27-alpine

COPY deploy/falcon-ui.nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /srv/falcon-ui/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
