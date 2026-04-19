import { Controller, Get, Post, Body, UseGuards } from '@nestjs/common'
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger'
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard'
import { ExercisesService } from './exercises.service'
import { CreateExerciseSchema } from '@mfj/validators'

@ApiTags('exercises')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller('exercises')
export class ExercisesController {
  constructor(private readonly exercisesService: ExercisesService) {}

  @Get()
  findAll() {
    return this.exercisesService.findAll()
  }

  @Post()
  create(@Body() body: unknown) {
    const input = CreateExerciseSchema.parse(body)
    return this.exercisesService.create(input)
  }
}
