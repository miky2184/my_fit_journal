import {
  pgTable,
  uuid,
  varchar,
  text,
  timestamp,
  pgEnum,
} from 'drizzle-orm/pg-core'

export const exerciseTypeEnum = pgEnum('exercise_type', ['strength', 'cardio', 'flexibility'])

export const exercises = pgTable('exercises', {
  id: uuid('id').primaryKey().defaultRandom(),
  name: varchar('name', { length: 100 }).notNull(),
  type: exerciseTypeEnum('type').notNull(),
  muscleGroups: text('muscle_groups').array().notNull().default([]),
  description: text('description'),
  isGlobal: varchar('is_global', { length: 1 }).notNull().default('Y'),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
})
