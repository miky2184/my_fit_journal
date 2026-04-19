import { Controller, Get, Post, Patch, Param, Body, Query, UseGuards } from '@nestjs/common'
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger'
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard'
import { CurrentUser, type JwtUser } from '../common/decorators/current-user.decorator'
import { SessionsService } from './sessions.service'
import { StartSessionSchema, CompleteSessionSchema, LogSetSchema } from '@mfj/validators'

@ApiTags('sessions')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller('sessions')
export class SessionsController {
  constructor(private readonly sessionsService: SessionsService) {}

  @Get('history')
  getHistory(
    @CurrentUser() user: JwtUser,
    @Query('limit') limit?: string,
    @Query('offset') offset?: string,
  ) {
    return this.sessionsService.getHistory(
      user.userId,
      limit ? parseInt(limit) : 20,
      offset ? parseInt(offset) : 0,
    )
  }

  @Post('start')
  start(@CurrentUser() user: JwtUser, @Body() body: unknown) {
    const input = StartSessionSchema.parse(body)
    return this.sessionsService.startSession(user.userId, input)
  }

  @Patch(':id/complete')
  complete(@Param('id') id: string, @Body() body: unknown) {
    const input = CompleteSessionSchema.parse(body)
    return this.sessionsService.completeSession(id, input)
  }

  @Post('exercise-logs/:exerciseLogId/sets')
  logSet(@Param('exerciseLogId') exerciseLogId: string, @Body() body: unknown) {
    const input = LogSetSchema.parse(body)
    return this.sessionsService.logSet(exerciseLogId, input)
  }

  @Patch('exercise-logs/:exerciseLogId/complete')
  completeExercise(@Param('exerciseLogId') exerciseLogId: string) {
    return this.sessionsService.markExerciseComplete(exerciseLogId)
  }
}
