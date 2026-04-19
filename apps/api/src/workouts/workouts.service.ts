import { Injectable, Inject } from '@nestjs/common'
import { eq } from 'drizzle-orm'
import type { Db } from '@mfj/db'
import { workoutPlans, workoutExercises } from '@mfj/db'
import { DB_TOKEN } from '../db/db.module'
import type { CreateWorkoutPlanInput } from '@mfj/validators'

@Injectable()
export class WorkoutsService {
  constructor(@Inject(DB_TOKEN) private readonly db: Db) {}

  findAllByUser(userId: string) {
    return this.db.select().from(workoutPlans).where(eq(workoutPlans.userId, userId))
  }

  async create(userId: string, input: CreateWorkoutPlanInput) {
    const [plan] = await this.db
      .insert(workoutPlans)
      .values({
        userId,
        name: input.name,
        description: input.description,
        category: input.category,
        estimatedMinutes: input.estimatedMinutes,
      })
      .returning()

    if (!plan) throw new Error('Failed to create workout plan')

    if (input.exercises.length > 0) {
      await this.db.insert(workoutExercises).values(
        input.exercises.map((e) => ({
          workoutPlanId: plan.id,
          exerciseId: e.exerciseId,
          order: e.order,
          sets: e.sets,
          reps: e.reps,
          durationSeconds: e.durationSeconds,
          weightKg: e.weightKg?.toString(),
          restSeconds: e.restSeconds,
          notes: e.notes,
        })),
      )
    }

    return plan
  }

  deleteById(id: string, userId: string) {
    return this.db
      .delete(workoutPlans)
      .where(eq(workoutPlans.id, id))
      .returning()
  }
}
