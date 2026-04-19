import { z } from 'zod'

export const WorkoutCategorySchema = z.enum(['gym', 'swimming', 'running', 'cycling', 'other'])
export const ExerciseTypeSchema = z.enum(['strength', 'cardio', 'flexibility'])
export const MuscleGroupSchema = z.enum([
  'chest',
  'back',
  'shoulders',
  'biceps',
  'triceps',
  'legs',
  'core',
  'full_body',
])

export const CreateExerciseSchema = z.object({
  name: z.string().min(1).max(100),
  type: ExerciseTypeSchema,
  muscleGroups: z.array(MuscleGroupSchema).min(1),
  description: z.string().max(500).optional(),
})

export const WorkoutExerciseSchema = z.object({
  exerciseId: z.string().uuid(),
  order: z.number().int().min(0),
  sets: z.number().int().min(1).max(100),
  reps: z.number().int().min(1).max(1000).optional(),
  durationSeconds: z.number().int().min(1).optional(),
  weightKg: z.number().min(0).max(1000).optional(),
  restSeconds: z.number().int().min(0).max(600).default(60),
  notes: z.string().max(300).optional(),
})

export const CreateWorkoutPlanSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
  category: WorkoutCategorySchema,
  exercises: z.array(WorkoutExerciseSchema),
  estimatedMinutes: z.number().int().min(1).max(600),
})

export const StartSessionSchema = z.object({
  workoutPlanId: z.string().uuid().optional(),
  name: z.string().min(1).max(100),
  category: WorkoutCategorySchema,
})

export const CompleteSessionSchema = z.object({
  completedAt: z.string().datetime(),
  durationMinutes: z.number().int().min(1).optional(),
  kcalBurned: z.number().int().min(0).optional(),
  notes: z.string().max(1000).optional(),
})

export const LogSetSchema = z.object({
  setNumber: z.number().int().min(1),
  reps: z.number().int().min(0).optional(),
  weightKg: z.number().min(0).optional(),
  durationSeconds: z.number().int().min(0).optional(),
  completed: z.boolean(),
})

export type CreateExerciseInput = z.infer<typeof CreateExerciseSchema>
export type CreateWorkoutPlanInput = z.infer<typeof CreateWorkoutPlanSchema>
export type StartSessionInput = z.infer<typeof StartSessionSchema>
export type CompleteSessionInput = z.infer<typeof CompleteSessionSchema>
export type LogSetInput = z.infer<typeof LogSetSchema>
