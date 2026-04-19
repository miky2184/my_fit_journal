export type WorkoutCategory = 'gym' | 'swimming' | 'running' | 'cycling' | 'other'
export type ExerciseType = 'strength' | 'cardio' | 'flexibility'
export type MuscleGroup =
  | 'chest'
  | 'back'
  | 'shoulders'
  | 'biceps'
  | 'triceps'
  | 'legs'
  | 'core'
  | 'full_body'

export interface Exercise {
  id: string
  name: string
  type: ExerciseType
  muscleGroups: MuscleGroup[]
  description?: string
}

export interface WorkoutExercise {
  id: string
  exerciseId: string
  exercise: Exercise
  order: number
  sets: number
  reps?: number
  durationSeconds?: number
  weightKg?: number
  restSeconds: number
  notes?: string
}

export interface WorkoutPlan {
  id: string
  userId: string
  name: string
  description?: string
  category: WorkoutCategory
  exercises: WorkoutExercise[]
  estimatedMinutes: number
  createdAt: Date
  updatedAt: Date
}

export interface WorkoutSession {
  id: string
  userId: string
  workoutPlanId?: string
  workoutPlan?: WorkoutPlan
  name: string
  category: WorkoutCategory
  startedAt: Date
  completedAt?: Date
  durationMinutes?: number
  kcalBurned?: number
  notes?: string
  exerciseLogs: ExerciseLog[]
}

export interface ExerciseLog {
  id: string
  sessionId: string
  workoutExerciseId?: string
  exerciseId: string
  exercise: Exercise
  order: number
  setLogs: SetLog[]
  completed: boolean
}

export interface SetLog {
  id: string
  exerciseLogId: string
  setNumber: number
  reps?: number
  weightKg?: number
  durationSeconds?: number
  completed: boolean
  performedAt?: Date
}
