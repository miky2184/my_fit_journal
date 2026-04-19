import { Injectable, Inject, ConflictException } from '@nestjs/common'
import { eq } from 'drizzle-orm'
import type { Db } from '@mfj/db'
import { users } from '@mfj/db'
import { DB_TOKEN } from '../db/db.module'

@Injectable()
export class UsersService {
  constructor(@Inject(DB_TOKEN) private readonly db: Db) {}

  async create(data: { email: string; name: string; passwordHash: string }) {
    const existing = await this.findByEmail(data.email)
    if (existing) throw new ConflictException('Email already in use')
    const [user] = await this.db.insert(users).values(data).returning()
    return user!
  }

  async findByEmail(email: string) {
    const [user] = await this.db.select().from(users).where(eq(users.email, email))
    return user ?? null
  }

  async findById(id: string) {
    const [user] = await this.db.select().from(users).where(eq(users.id, id))
    return user ?? null
  }
}
