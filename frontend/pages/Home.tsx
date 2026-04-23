import { Head, useForm } from "@inertiajs/react"
import type { FormEvent } from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import type { FlashMessage } from "@/lib/types"

type Props = {
  flash: FlashMessage[]
  oauth_ready: boolean
}

export default function Home({ flash, oauth_ready }: Props) {
  const form = useForm({
    email: "",
    content: "",
    password: "",
    master_token: "",
    labels: "",
    use_oauth: false,
    reset: false,
    blank_lines: false,
    file: null as File | null,
  })

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    form.post("/import/", { forceFormData: true, preserveScroll: true })
  }

  return (
    <>
      <Head title="text-to-google-keep" />
      <div className="mx-auto max-w-lg px-4 py-8">
        {flash.map((f, i) => (
          <div
            key={i}
            className={
              f.level === "error"
                ? "mb-3 rounded-md border border-destructive/50 bg-destructive/15 px-3 py-2 text-sm text-red-200"
                : f.level === "success"
                  ? "mb-3 rounded-md border border-green-700/40 bg-green-950/40 px-3 py-2 text-sm text-green-100"
                  : "mb-3 rounded-md border border-border px-3 py-2 text-sm text-muted-foreground"
            }
          >
            {f.text}
          </div>
        ))}
        {!oauth_ready ? (
          <p className="mb-4 text-sm text-muted-foreground">
            Set <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">GOOGLE_KEEP_CLIENT_SECRETS</code> or
            place <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">client_secret.json</code> in the
            server working directory to show <strong>Sign in with Google</strong> in the header.
          </p>
        ) : null}

        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Google account</CardTitle>
              <CardDescription>
                OAuth (official API) or gkeepapi (password / master token). See README.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="flex items-center gap-2">
                <input
                  id="use_oauth"
                  type="checkbox"
                  className="size-4 accent-primary"
                  checked={form.data.use_oauth}
                  onChange={(e) => form.setData("use_oauth", e.target.checked)}
                />
                <Label htmlFor="use_oauth" className="cursor-pointer font-normal">
                  Use Google OAuth (personal Gmail). Sign in from the header first.
                </Label>
              </div>
              <p className="text-xs text-muted-foreground">OAuth mode does not support labels.</p>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  name="email"
                  value={form.data.email}
                  onChange={(e) => form.setData("email", e.target.value)}
                  autoComplete="username"
                  required
                  placeholder="you@gmail.com"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password or app password</Label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  value={form.data.password}
                  onChange={(e) => form.setData("password", e.target.value)}
                  autoComplete="current-password"
                  placeholder="gkeepapi only"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="master_token">Master token (optional)</Label>
                <textarea
                  id="master_token"
                  name="master_token"
                  className="min-h-[4.5rem] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm text-foreground shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 dark:bg-input/30"
                  value={form.data.master_token}
                  onChange={(e) => form.setData("master_token", e.target.value)}
                  placeholder="aas_et/…"
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  id="reset"
                  type="checkbox"
                  className="size-4 accent-primary"
                  checked={form.data.reset}
                  onChange={(e) => form.setData("reset", e.target.checked)}
                />
                <Label htmlFor="reset" className="cursor-pointer font-normal">
                  Clear saved token for this email before sign-in
                </Label>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Notes</CardTitle>
              <CardDescription>Paste lines or choose a UTF-8 file (file replaces textarea).</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="space-y-2">
                <Label htmlFor="content">Lines to import</Label>
                <textarea
                  id="content"
                  name="content"
                  className="min-h-40 w-full rounded-md border border-input bg-transparent px-3 py-2 font-mono text-sm text-foreground shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 dark:bg-input/30"
                  value={form.data.content}
                  onChange={(e) => form.setData("content", e.target.value)}
                  placeholder="One line → one note…"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="file">Or UTF-8 file</Label>
                <Input
                  id="file"
                  name="file"
                  type="file"
                  accept=".txt,text/plain,.md,.csv,.log,*/*"
                  onChange={(e) => form.setData("file", e.target.files?.[0] ?? null)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="labels">Labels (comma-separated, gkeepapi only)</Label>
                <Input
                  id="labels"
                  name="labels"
                  value={form.data.labels}
                  onChange={(e) => form.setData("labels", e.target.value)}
                  placeholder="Shopping, Inbox"
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  id="blank_lines"
                  type="checkbox"
                  className="size-4 accent-primary"
                  checked={form.data.blank_lines}
                  onChange={(e) => form.setData("blank_lines", e.target.checked)}
                />
                <Label htmlFor="blank_lines" className="cursor-pointer font-normal">
                  Import blank lines as empty notes
                </Label>
              </div>
            </CardContent>
          </Card>

          <Button type="submit" className="w-full" disabled={form.processing}>
            {form.processing ? "Importing…" : "Import to Keep"}
          </Button>
        </form>
      </div>
    </>
  )
}
