import {
  pgTable,
  uuid,
  varchar,
  text,
  integer,
  numeric,
  boolean,
  timestamp,
  pgEnum,
} from 'drizzle-orm/pg-core'
import { users } from './users'
import { exercises } from './exercises'

export const workoutCategoryEnum = pgEnum('workout_category', [
  'gym',
  'swimming',
  'running',
  'cycling',
  'other',
])

export const workoutPlans = pgTable('workout_plans', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id')
    .notNull()
    .references(() => users.id, { onDelete: 'cascade' }),
  name: varchar('name', { length: 100 }).notNull(),
  description: text('description'),
  category: workoutCategoryEnum('category').notNull(),
  estimatedMinutes: integer('estimated_minutes').notNull(),
  isActive: boolean('is_active').notNull().default(true),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
})

export const workoutExercises = pgTable('workout_exercises', {
  id: uuid('id').primaryKey().defaultRandom(),
  workoutPlanId: uuid('workout_plan_id')
    .notNull()
    .references(() => workoutPlans.id, { onDelete: 'cascade' }),
  exerciseId: uuid('exercise_id')
    .notNull()
    .references(() => exercises.id),
  order: integer('order').notNull(),
  sets: integer('sets').notNull(),
  reps: integer('reps'),
  durationSeconds: integer('duration_seconds'),
  weightKg: numeric('weight_kg', { precision: 6, scale: 2 }),
  restSeconds: integer('rest_seconds').notNull().default(60),
  notes: text('notes'),
})

export const workoutSessions = pgTable('workout_sessions', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id')
    .notNull()
    .references(() => users.id, { onDelete: 'cascade' }),
  workoutPlanId: uuid('workout_plan_id').references(() => workoutPlans.id, {
    onDelete: 'set null',
  }),
  name: varchar('name', { length: 100 }).notNull(),
  category: workoutCategoryEnum('category').notNull(),
  startedAt: timestamp('started_at', { withTimezone: true }).notNull().defaultNow(),
  completedAt: timestamp('completed_at', { withTimezone: true }),
  durationMinutes: integer('duration_minutes'),
  kcalBurned: integer('kcal_burned'),
  notes: text('notes'),
})

export const exerciseLogs = pgTable('exercise_logs', {
  id: uuid('id').primaryKey().defaultRandom(),
  sessionId: uuid('session_id')
    .notNull()
    .references(() => workoutSessions.id, { onDelete: 'cascade' }),
  workoutExerciseId: uuid('workout_exercise_id').references(() => workoutExercises.id, {
    onDelete: 'set null',
  }),
  exerciseId: uuid('exercise_id')
    .notNull()
    .references(() => exercises.id),
  order: integer('order').notNull(),
  completed: boolean('completed').notNull().default(false),
})

export const setLogs = pgTable('set_logs', {
  id: uuid('id').primaryKey().defaultRandom(),
  exerciseLogId: uuid('exercise_log_id')
    .notNull()
    .references(() => exerciseLogs.id, { onDelete: 'cascade' }),
  setNumber: integer('set_number').notNull(),
  reps: integer('reps'),
  weightKg: numeric('weight_kg', { precision: 6, scale: 2 }),
  durationSeconds: integer('duration_seconds'),
  completed: boolean('completed').notNull().default(false),
  performedAt: timestamp('performed_at', { withTimezone: true }),
})
