import { Injectable, Inject } from '@nestjs/common'
import { eq, desc } from 'drizzle-orm'
import type { Db } from '@mfj/db'
import { workoutSessions, exerciseLogs, setLogs } from '@mfj/db'
import { DB_TOKEN } from '../db/db.module'
import type { StartSessionInput, CompleteSessionInput, LogSetInput } from '@mfj/validators'

@Injectable()
export class SessionsService {
  constructor(@Inject(DB_TOKEN) private readonly db: Db) {}

  getHistory(userId: string, limit = 20, offset = 0) {
    return this.db
      .select()
      .from(workoutSessions)
      .where(eq(workoutSessions.userId, userId))
      .orderBy(desc(workoutSessions.startedAt))
      .limit(limit)
      .offset(offset)
  }

  async startSession(userId: string, input: StartSessionInput) {
    const [session] = await this.db
      .insert(workoutSessions)
      .values({ userId, ...input })
      .returning()
    return session!
  }

  async completeSession(sessionId: string, input: CompleteSessionInput) {
    const [session] = await this.db
      .update(workoutSessions)
      .set({
        completedAt: new Date(input.completedAt),
        durationMinutes: input.durationMinutes,
        kcalBurned: input.kcalBurned,
        notes: input.notes,
      })
      .where(eq(workoutSessions.id, sessionId))
      .returning()
    return session!
  }

  async logSet(exerciseLogId: string, input: LogSetInput) {
    const [set] = await this.db
      .insert(setLogs)
      .values({
        exerciseLogId,
        setNumber: input.setNumber,
        reps: input.reps,
        weightKg: input.weightKg?.toString(),
        durationSeconds: input.durationSeconds,
        completed: input.completed,
        performedAt: input.completed ? new Date() : undefined,
      })
      .returning()
    return set!
  }

  async markExerciseComplete(exerciseLogId: string) {
    const [log] = await this.db
      .update(exerciseLogs)
      .set({ completed: true })
      .where(eq(exerciseLogs.id, exerciseLogId))
      .returning()
    return log!
  }
}
