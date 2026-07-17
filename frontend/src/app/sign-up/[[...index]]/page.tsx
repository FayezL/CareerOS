import { SignUp } from "@clerk/nextjs"

import { AuthLayout } from "@/components/auth/auth-layout"
import { authAppearance } from "@/components/auth/appearance"

export default function SignUpPage() {
  return (
    <AuthLayout title="Create your account" subtitle="Start tracking your job search in minutes.">
      <SignUp
        appearance={authAppearance}
        signInUrl="/sign-in"
        fallbackRedirectUrl="/applications"
      />
    </AuthLayout>
  )
}
