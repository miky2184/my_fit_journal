import { Controller, Get, Post, Delete, Param, Body, UseGuards } from '@nestjs/common'
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger'
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard'
import { CurrentUser, type JwtUser } from '../common/decorators/current-user.decorator'
import { WorkoutsService } from './workouts.service'
import { CreateWorkoutPlanSchema } from '@mfj/validators'

@ApiTags('workouts')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller('workouts')
export class WorkoutsController {
  constructor(private readonly workoutsService: WorkoutsService) {}

  @Get()
  findAll(@CurrentUser() user: JwtUser) {
    return this.workoutsService.findAllByUser(user.userId)
  }

  @Post()
  create(@CurrentUser() user: JwtUser, @Body() body: unknown) {
    const input = CreateWorkoutPlanSchema.parse(body)
    return this.workoutsService.create(user.userId, input)
  }

  @Delete(':id')
  delete(@Param('id') id: string, @CurrentUser() user: JwtUser) {
    return this.workoutsService.deleteById(id, user.userId)
  }
}
