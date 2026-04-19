import { Module } from '@nestjs/common'
import { ConfigModule } from '@nestjs/config'
import { DbModule } from './db/db.module'
import { AuthModule } from './auth/auth.module'
import { UsersModule } from './users/users.module'
import { WorkoutsModule } from './workouts/workouts.module'
import { ExercisesModule } from './exercises/exercises.module'
import { SessionsModule } from './sessions/sessions.module'

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    DbModule,
    AuthModule,
    UsersModule,
    WorkoutsModule,
    ExercisesModule,
    SessionsModule,
  ],
})
export class AppModule {}
