import type { ComponentProps } from "react"
import type { SignIn } from "@clerk/nextjs"

// Derive Clerk's appearance type from the component itself so we don't need a
// direct dep on the transitive @clerk/types package.
type ClerkAppearance = NonNullable<ComponentProps<typeof SignIn>["appearance"]>

/**
 * Clerk appearance overrides for the <SignIn /> / <SignUp /> pages.
 *
 * The split-screen AuthLayout already provides the outer surface (title,
 * subtitle, panel), so we strip Clerk's built-in card chrome + header and
 * restyle the controls to read as native shadcn inputs/buttons. This avoids
 * the "Clerk box pasted on top of a page" look.
 */
export const authAppearance: ClerkAppearance = {
  layout: {
    socialButtonsPlacement: "top",
    socialButtonsVariant: "blockButton",
  },
  elements: {
    rootBox: "w-full",
    card: "shadow-none border-0 bg-transparent p-0 rounded-none",
    cardBox: "shadow-none border-0 bg-transparent p-0 rounded-none",
    // AuthLayout renders its own title/subtitle — hide Clerk's redundant header.
    header: "hidden",
    headerTitle: "hidden",
    headerSubtitle: "hidden",
    // Social / OAuth buttons — bordered, calm, full width.
    socialButtonsBlockButton:
      "w-full bg-background border border-input rounded-md h-10 text-sm font-medium text-foreground hover:bg-accent hover:text-accent-foreground transition-colors",
    socialButtonsBlockButtonText: "text-sm font-medium",
    socialButtonsIconBox: "mr-2",
    // Divider ("or").
    dividerLine: "bg-border",
    dividerText: "text-xs uppercase tracking-wider text-muted-foreground",
    // Form fields — shadcn input look.
    form: "gap-3",
    formField: "gap-1",
    formFieldLabel: "text-xs font-medium text-muted-foreground data-[valid]:text-foreground",
    formFieldInput:
      "bg-background border border-input rounded-md h-10 px-3 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-0",
    formFieldPasswordInputButton: "text-muted-foreground hover:text-foreground",
    formButtonPrimary:
      "bg-primary text-primary-foreground shadow hover:bg-primary/90 rounded-md h-10 w-full text-sm font-medium transition-colors",
    formButtonReset: "text-xs text-muted-foreground hover:text-foreground",
    // OTP / code input rows.
    otpCodeFieldInput:
      "bg-background border border-input rounded-md h-12 w-12 text-center text-lg font-semibold",
    // Footer ("Don't have an account?") + legal line.
    footer: "flex flex-col items-center gap-2 pt-2",
    footerPageLink: "text-sm font-medium text-primary hover:text-primary/90 transition-colors",
    footerActionLink: "text-sm font-medium text-primary hover:text-primary/90 transition-colors",
    footerPages: "flex flex-row gap-3",
    footerPageText: "text-xs text-muted-foreground",
    identityPreview: "bg-muted/50 border border-border rounded-md",
    identityPreviewText: "text-sm text-foreground",
    identityPreviewEditButton: "text-xs text-primary hover:text-primary/90",
    // Loading / spinner.
    main: "bg-transparent",
    formWarning: "text-xs text-destructive",
    alert: "bg-destructive/10 border-destructive/20 text-destructive rounded-md",
  },
}
