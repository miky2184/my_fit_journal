FROM node:22-alpine AS base
RUN npm install -g pnpm
WORKDIR /app

FROM base AS deps
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml* ./
COPY packages/db/package.json packages/db/
COPY packages/types/package.json packages/types/
COPY packages/validators/package.json packages/validators/
COPY apps/api/package.json apps/api/
RUN pnpm install --frozen-lockfile

FROM base AS builder
COPY --from=deps /app/node_modules node_modules
COPY --from=deps /app/packages packages
COPY . .
RUN pnpm --filter @mfj/api build

FROM node:22-alpine AS runner
WORKDIR /app
COPY --from=builder /app/apps/api/dist dist
COPY --from=builder /app/node_modules node_modules
EXPOSE 4000
CMD ["node", "dist/main"]
