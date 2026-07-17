import { SignIn } from "@clerk/nextjs"

import { AuthLayout } from "@/components/auth/auth-layout"

export default function SignInPage() {
  return (
    <AuthLayout title="Welcome back" subtitle="Sign in to continue to your dashboard.">
      <SignIn />
    </AuthLayout>
  )
}
