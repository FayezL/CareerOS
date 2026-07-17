import { SignIn } from "@clerk/nextjs"

import { AuthLayout } from "@/components/auth/auth-layout"
import { authAppearance } from "@/components/auth/appearance"

export default function SignInPage() {
  return (
    <AuthLayout title="Welcome back" subtitle="Sign in to continue to your dashboard.">
      <SignIn
        appearance={authAppearance}
        signUpUrl="/sign-up"
        fallbackRedirectUrl="/applications"
      />
    </AuthLayout>
  )
}
