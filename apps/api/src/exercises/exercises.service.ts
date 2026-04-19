import { Injectable, Inject } from '@nestjs/common'
import { eq } from 'drizzle-orm'
import type { Db } from '@mfj/db'
import { exercises } from '@mfj/db'
import { DB_TOKEN } from '../db/db.module'
import type { CreateExerciseInput } from '@mfj/validators'

@Injectable()
export class ExercisesService {
  constructor(@Inject(DB_TOKEN) private readonly db: Db) {}

  findAll() {
    return this.db.select().from(exercises)
  }

  findById(id: string) {
    return this.db.select().from(exercises).where(eq(exercises.id, id))
  }

  create(input: CreateExerciseInput) {
    return this.db
      .insert(exercises)
      .values({ ...input, muscleGroups: input.muscleGroups as string[] })
      .returning()
  }
}
