import Link from "next/link";
import { ArrowRight } from "lucide-react";

export default function SignUp() {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-4">Get started</div>
      <h1 className="font-display text-[44px] leading-[1] tracking-tightest">
        Create your <span className="italic text-blue">workspace.</span>
      </h1>
      <p className="mt-3 text-ink-2 text-[14px]">$0 forever for the first 200 resolutions per month.</p>

      <form className="mt-10 space-y-5">
        <div className="grid grid-cols-2 gap-3">
          <Field label="Full name" placeholder="Kira Tan" />
          <Field label="Company" placeholder="Acme Goods" />
        </div>
        <Field label="Work email" type="email" placeholder="kira@acme.co" />
        <Field label="Password" type="password" placeholder="•••••••••" hint="At least 12 characters, mixed case." />

        <button className="w-full h-11 bg-ink text-paper inline-flex items-center justify-center gap-2 text-[14px] hover:bg-blue transition">
          Create workspace <ArrowRight size={15} />
        </button>
        <p className="text-[12px] text-ink-3 leading-relaxed">
          By continuing you agree to our <Link href="/terms" className="underline underline-offset-4 decoration-line">Terms</Link>{" "}
          and <Link href="/privacy" className="underline underline-offset-4 decoration-line">Privacy</Link>. We'll never
          email you for product news without asking first.
        </p>
      </form>

      <p className="mt-10 text-[13px] text-ink-2">
        Have an account? <Link href="/signin" className="text-ink hover:text-blue underline underline-offset-4 decoration-line">Sign in →</Link>
      </p>
    </div>
  );
}

function Field({
  label,
  hint,
  ...rest
}: { label: string; hint?: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="block">
      <span className="block text-[11px] uppercase tracking-[0.18em] text-ink-3 mb-2">{label}</span>
      <input
        {...rest}
        className="w-full h-11 px-3 border border-line bg-paper text-[14px] focus:border-ink outline-none transition"
      />
      {hint && <span className="block mt-1.5 text-[12px] text-ink-3">{hint}</span>}
    </label>
  );
}
