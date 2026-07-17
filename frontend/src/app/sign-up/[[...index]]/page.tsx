import { SignUp } from "@clerk/nextjs"

import { AuthLayout } from "@/components/auth/auth-layout"

export default function SignUpPage() {
  return (
    <AuthLayout title="Create your account" subtitle="Start tracking your job search in minutes.">
      <SignUp />
    </AuthLayout>
  )
}
