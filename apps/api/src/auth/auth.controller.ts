import { Controller, Post, Body, HttpCode, HttpStatus } from '@nestjs/common'
import { ApiTags } from '@nestjs/swagger'
import { AuthService } from './auth.service'
import { LoginSchema, RegisterSchema } from '@mfj/validators'

@ApiTags('auth')
@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post('register')
  register(@Body() body: unknown) {
    const input = RegisterSchema.parse(body)
    return this.authService.register(input)
  }

  @Post('login')
  @HttpCode(HttpStatus.OK)
  login(@Body() body: unknown) {
    const input = LoginSchema.parse(body)
    return this.authService.login(input)
  }
}
