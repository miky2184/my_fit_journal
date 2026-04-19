import { Injectable, UnauthorizedException } from '@nestjs/common'
import { JwtService } from '@nestjs/jwt'
import * as bcrypt from 'bcryptjs'
import { UsersService } from '../users/users.service'
import type { LoginInput, RegisterInput } from '@mfj/validators'

@Injectable()
export class AuthService {
  constructor(
    private readonly usersService: UsersService,
    private readonly jwtService: JwtService,
  ) {}

  async register(input: RegisterInput) {
    const passwordHash = await bcrypt.hash(input.password, 12)
    const user = await this.usersService.create({
      email: input.email,
      name: input.name,
      passwordHash,
    })
    return this.signTokens(user.id, user.email)
  }

  async login(input: LoginInput) {
    const user = await this.usersService.findByEmail(input.email)
    if (!user) throw new UnauthorizedException('Invalid credentials')
    const valid = await bcrypt.compare(input.password, user.passwordHash)
    if (!valid) throw new UnauthorizedException('Invalid credentials')
    return this.signTokens(user.id, user.email)
  }

  private signTokens(userId: string, email: string) {
    const payload = { sub: userId, email }
    return {
      accessToken: this.jwtService.sign(payload),
      userId,
    }
  }
}
