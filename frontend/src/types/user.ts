export interface UserMe {
  id: string
  display_name: string
  email: string | null
  avatar_url: string | null
  is_admin: boolean
  reputation: number
}
