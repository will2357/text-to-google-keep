import { Link, usePage } from "@inertiajs/react"
import type { ReactNode } from "react"

import { Button } from "@/components/ui/button"
import type { FlashMessage } from "@/lib/types"

type PageProps = {
  flash?: FlashMessage[]
  oauth_ready?: boolean
}

export default function Layout({ children }: { children: ReactNode }) {
  const { oauth_ready } = usePage<PageProps>().props

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-sm">
        <nav className="mx-auto flex h-14 max-w-5xl items-center justify-between px-6">
          <div className="flex items-center gap-5">
            <Link href="/" className="text-lg font-bold tracking-tight text-primary">
              text-to-google-keep
            </Link>
          </div>
          {oauth_ready ? (
            <Button variant="outline" size="sm" asChild>
              <a href="/oauth/start/">Sign in with Google</a>
            </Button>
          ) : null}
        </nav>
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t border-border/50 py-6 text-center text-sm text-muted-foreground">
        Django + Inertia + React · same theme as{" "}
        <a className="text-primary underline-offset-4 hover:underline" href="https://github.com/kiwiz/gkeepapi">
          gkeepapi
        </a>{" "}
        / Google Keep API
      </footer>
    </div>
  )
}
