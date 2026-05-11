import Link from "next/link";
import { ArrowRight } from "lucide-react";

export default function SignIn() {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-4">Welcome back</div>
      <h1 className="font-display text-[44px] leading-[1] tracking-tightest">
        Sign in to <span className="italic text-blue">Resolve.</span>
      </h1>
      <p className="mt-3 text-ink-2 text-[14px]">Operating support at the speed of an API call.</p>

      <form className="mt-10 space-y-5">
        <Field label="Work email" type="email" placeholder="kira@acme.co" />
        <Field label="Password" type="password" placeholder="••••••••••" />
        <div className="flex items-center justify-between text-[12.5px]">
          <label className="inline-flex items-center gap-2 text-ink-2">
            <input type="checkbox" className="accent-blue h-3.5 w-3.5" /> Keep me signed in
          </label>
          <Link href="/forgot" className="text-ink-2 hover:text-blue transition">Forgot?</Link>
        </div>
        <button className="w-full h-11 bg-ink text-paper inline-flex items-center justify-center gap-2 text-[14px] hover:bg-blue transition">
          Sign in <ArrowRight size={15} />
        </button>
        <div className="relative my-2 text-center">
          <span className="absolute inset-x-0 top-1/2 h-px bg-line" />
          <span className="relative inline-block bg-paper px-3 text-[11px] uppercase tracking-[0.18em] text-ink-3">or</span>
        </div>
        <button className="w-full h-11 border border-line text-[13.5px] hover:border-ink transition">
          Continue with SSO
        </button>
      </form>

      <p className="mt-10 text-[13px] text-ink-2">
        New to Resolve? <Link href="/signup" className="text-ink hover:text-blue underline underline-offset-4 decoration-line">Create an account →</Link>
      </p>
    </div>
  );
}

function Field({ label, ...rest }: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="block">
      <span className="block text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">{label}</span>
      <input
        {...rest}
        className="w-full h-11 px-3 border border-line bg-paper text-[14px] focus:border-ink outline-none transition"
      />
    </label>
  );
}
