import { config } from 'dotenv'
import { expand } from 'dotenv-expand'
import type { Config } from 'drizzle-kit'

expand(config({ path: '../../.env' }))

export default {
  schema: './src/schema/index.ts',
  out: './migrations',
  dialect: 'postgresql',
  dbCredentials: {
    url: process.env['DATABASE_URL']!,
  },
} satisfies Config
