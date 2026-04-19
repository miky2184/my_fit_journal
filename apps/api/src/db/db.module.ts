import { Module, Global } from '@nestjs/common'
import { ConfigService } from '@nestjs/config'
import { createDb } from '@mfj/db'

export const DB_TOKEN = 'DB'

@Global()
@Module({
  providers: [
    {
      provide: DB_TOKEN,
      inject: [ConfigService],
      useFactory: (config: ConfigService) => {
        const url = config.getOrThrow<string>('DATABASE_URL')
        return createDb(url)
      },
    },
  ],
  exports: [DB_TOKEN],
})
export class DbModule {}
