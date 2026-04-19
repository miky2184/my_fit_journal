import { Module } from '@nestjs/common'
import { WorkoutsService } from './workouts.service'
import { WorkoutsController } from './workouts.controller'

@Module({
  providers: [WorkoutsService],
  controllers: [WorkoutsController],
  exports: [WorkoutsService],
})
export class WorkoutsModule {}
